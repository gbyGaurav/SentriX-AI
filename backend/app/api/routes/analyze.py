"""Analysis API routes — main entry point for all fraud analysis."""

import logging
import time
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.security import validate_file
from app.db.database import get_db
from app.db.models import Analysis, DetectorResultDB, EvidenceDB
from app.fusion.explainability import ExplainabilityEngine
from app.fusion.fusion_engine import FusionEngine
from app.fusion.risk_engine import RiskEngine
from app.llm.investigator import LLMInvestigator
from app.router.input_classifier import InputClassifier
from app.router.modality_router import ModalityRouter
from app.schemas.analysis import (
    AnalysisRequest,
    AnalysisResponse,
    DetectorResult,
    EvidenceItem,
    FraudType,
    InputType,
    RiskLevel,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["analysis"])

# Module-level singletons
classifier = InputClassifier()
modality_router = ModalityRouter()
fusion = FusionEngine()
risk_engine = RiskEngine()
explainer = ExplainabilityEngine()
llm_investigator = LLMInvestigator()


async def _run_analysis(
    *,
    file: UploadFile | None = None,
    text: str | None = None,
    url: str | None = None,
    db: AsyncSession,
) -> AnalysisResponse:
    """Core analysis pipeline shared by all endpoints."""
    start_t = time.time()

    # 1. Validate input
    if not any([file, text, url]):
        raise HTTPException(status_code=422, detail="Must provide a file, text, or URL.")

    # 2. File validation
    file_bytes = None
    filename = None
    if file:
        is_valid, error_msg = validate_file(file)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        file_bytes = await file.read()
        filename = file.filename

    # 3. Input classification
    try:
        input_type = await classifier.classify(file=file, text=text, url=url)
    except Exception as e:
        logger.error(f"Input classification failed: {e}")
        raise HTTPException(status_code=400, detail="Could not determine input type.")

    if input_type == InputType.UNKNOWN:
        raise HTTPException(
            status_code=400,
            detail="Unable to determine input type. Please upload a supported file or paste a URL/text.",
        )

    logger.info(f"Input classified as: {input_type.value}")

    # 4. Route to detector(s)
    try:
        det_results, ev_items, ext_content = await modality_router.route_and_analyze(
            input_type, file_bytes=file_bytes, text=text, url=url, filename=filename
        )
    except Exception as e:
        logger.error(f"Analysis pipeline error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Analysis pipeline encountered an error.")

    if not det_results:
        raise HTTPException(
            status_code=500,
            detail="Analysis did not produce results. The input may not be supported.",
        )

    # 5. Fuse results
    fused_prob, fused_conf = fusion.fuse(det_results)

    # 6. Calculate risk
    r_score, r_level, f_types, f_conf = risk_engine.calculate_risk(
        fused_prob, fused_conf, det_results, ev_items
    )

    # 7. Generate explanation
    base_explanation = explainer.generate_explanation(r_score, r_level, f_types, det_results, ev_items)
    explanation = await llm_investigator.generate_investigation_report(
        input_type=input_type.value,
        risk_score=r_score,
        risk_level=r_level,
        fraud_types=f_types,
        confidence=f_conf,
        detectors=det_results,
        evidence=ev_items,
        extracted_content=ext_content,
        fallback_explanation=base_explanation
    )
    all_signals = [s for d in det_results for s in d.signals]
    recommendations = explainer.generate_recommendations(r_level, f_types, all_signals)
    summary = explainer.generate_summary(r_score, r_level, f_types, input_type)
    why_suspicious = explainer.generate_why_suspicious(det_results, ev_items, f_types, r_level)
    multimodal_findings = explainer.generate_multimodal_findings(ev_items, det_results, ext_content)

    ai_media = None
    for d in det_results:
        if d.metadata and "ai_media" in d.metadata:
            ai_media = d.metadata["ai_media"]
            break
    if not ai_media and "ai_media" in ext_content:
        ai_media = ext_content["ai_media"]

    # 8. Save to database
    proc_time = (time.time() - start_t) * 1000
    analysis_id = str(uuid.uuid4())
    now = datetime.utcnow()
    logger.info(f"POST: Created analysis ID = {analysis_id}")

    try:
        db_analysis = Analysis(
            id=analysis_id,
            input_type=input_type.value,
            risk_score=r_score,
            risk_level=r_level.value if hasattr(r_level, "value") else str(r_level),
            fraud_types=[f.value if hasattr(f, "value") else str(f) for f in f_types],
            confidence=f_conf,
            explanation=explanation,
            recommendations=recommendations,
            extracted_content=ext_content,
            processing_time_ms=proc_time,
            created_at=now,
        )
        db.add(db_analysis)

        for d in det_results:
            db_det = DetectorResultDB(
                id=str(uuid.uuid4()),
                analysis_id=analysis_id,
                module=d.module,
                fraud_probability=float(d.fraud_probability),
                confidence=float(d.confidence),
                risk=d.risk.value if hasattr(d.risk, "value") else str(d.risk),
                signals=list(d.signals),
                model_version=str(d.model_version),
                processing_time_ms=float(d.processing_time_ms),
                metadata_=d.metadata or {},
            )
            db.add(db_det)

        for ev in ev_items:
            db_ev = EvidenceDB(
                id=str(uuid.uuid4()),
                analysis_id=analysis_id,
                evidence_type=str(ev.evidence_type),
                source_modality=str(ev.source_modality),
                target_modality=ev.target_modality,
                content=str(ev.content[:500]) if ev.content else "",
                severity=str(ev.severity) if hasattr(ev.severity, "value") else str(ev.severity),
                evidence_relationship=ev.relationship,
            )
            db.add(db_ev)

        await db.commit()
        logger.info(f"POST: Successfully committed analysis ID = {analysis_id} to database")
    except Exception as e:
        logger.error(f"POST: Database save failed for analysis ID = {analysis_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database persistence failed: {type(e).__name__}: {str(e)}",
        )

    logger.info(
        f"Analysis complete: id={analysis_id}, type={input_type.value}, "
        f"score={r_score}, level={r_level.value}, time={proc_time:.0f}ms"
    )

    return AnalysisResponse(
        analysis_id=analysis_id,
        id=analysis_id,
        input_type=input_type,
        risk_score=r_score,
        risk_level=r_level,
        fraud_types=f_types,
        confidence=f_conf,
        detectors=det_results,
        evidence=ev_items,
        explanation=explanation,
        recommendations=recommendations,
        extracted_content=ext_content,
        processing_time_ms=proc_time,
        created_at=now.isoformat() + "Z",
        summary=summary,
        why_suspicious=why_suspicious,
        recommended_actions=recommendations,
        ai_media=ai_media,
        multimodal_findings=multimodal_findings,
    )


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze(
    file: UploadFile = File(None),
    text: str = Form(None),
    url: str = Form(None),
    db: AsyncSession = Depends(get_db),
):
    """Main analysis endpoint.
    
    Accepts a file upload, raw text, or URL. The system automatically
    classifies the input type and routes to appropriate fraud detectors.
    """
    return await _run_analysis(file=file, text=text, url=url, db=db)


@router.post("/analyze/url", response_model=AnalysisResponse)
async def analyze_url(request: AnalysisRequest, db: AsyncSession = Depends(get_db)):
    """Direct URL analysis endpoint."""
    if not request.url:
        raise HTTPException(status_code=422, detail="URL is required.")
    return await _run_analysis(url=request.url, db=db)


@router.post("/analyze/text", response_model=AnalysisResponse)
async def analyze_text(request: AnalysisRequest, db: AsyncSession = Depends(get_db)):
    """Direct text analysis endpoint."""
    if not request.text:
        raise HTTPException(status_code=422, detail="Text is required.")
    return await _run_analysis(text=request.text, db=db)


@router.get("/analysis/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(analysis_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve a past analysis by ID."""
    logger.info(f"GET: Requested analysis ID = {analysis_id}")
    stmt = (
        select(Analysis)
        .options(
            selectinload(Analysis.detectors),
            selectinload(Analysis.evidences),
        )
        .where(Analysis.id == analysis_id)
    )
    result = await db.execute(stmt)
    db_a = result.scalar_one_or_none()
    if not db_a:
        logger.warning(f"GET: Requested analysis ID = {analysis_id}")
        logger.warning("GET: Database lookup result = NOT FOUND")
        raise HTTPException(status_code=404, detail="Analysis not found.")

    logger.info("GET: Database lookup result = FOUND")

    return AnalysisResponse(
        analysis_id=db_a.id,
        id=db_a.id,
        input_type=InputType(db_a.input_type),
        risk_score=db_a.risk_score,
        risk_level=RiskLevel(db_a.risk_level) if isinstance(db_a.risk_level, str) else db_a.risk_level,
        fraud_types=[FraudType(f) if isinstance(f, str) else f for f in db_a.fraud_types],
        confidence=db_a.confidence,
        detectors=[
            DetectorResult(
                module=d.module,
                fraud_probability=d.fraud_probability,
                confidence=d.confidence,
                risk=RiskLevel(d.risk) if isinstance(d.risk, str) else d.risk,
                signals=d.signals,
                model_version=d.model_version,
                processing_time_ms=d.processing_time_ms,
                metadata=d.metadata_,
            )
            for d in db_a.detectors
        ],
        evidence=[
            EvidenceItem(
                evidence_type=ev.evidence_type,
                source_modality=ev.source_modality,
                target_modality=ev.target_modality,
                content=ev.content,
                severity=ev.severity,
                relationship=ev.evidence_relationship,
            )
            for ev in db_a.evidences
        ],
        explanation=db_a.explanation,
        recommendations=db_a.recommendations or [],
        extracted_content=db_a.extracted_content or {},
        processing_time_ms=db_a.processing_time_ms,
        created_at=db_a.created_at.isoformat() + "Z" if not db_a.created_at.isoformat().endswith("Z") else db_a.created_at.isoformat(),
        summary=explainer.generate_summary(
            db_a.risk_score,
            RiskLevel(db_a.risk_level) if isinstance(db_a.risk_level, str) else db_a.risk_level,
            [FraudType(f) if isinstance(f, str) else f for f in db_a.fraud_types],
            InputType(db_a.input_type)
        ),
        why_suspicious=explainer.generate_why_suspicious(
            [
                DetectorResult(
                    module=d.module,
                    fraud_probability=d.fraud_probability,
                    confidence=d.confidence,
                    risk=RiskLevel(d.risk) if isinstance(d.risk, str) else d.risk,
                    signals=d.signals,
                    model_version=d.model_version,
                    processing_time_ms=d.processing_time_ms,
                    metadata=d.metadata_,
                )
                for d in db_a.detectors
            ],
            [
                EvidenceItem(
                    evidence_type=ev.evidence_type,
                    source_modality=ev.source_modality,
                    target_modality=ev.target_modality,
                    content=ev.content,
                    severity=ev.severity,
                    relationship=ev.evidence_relationship,
                )
                for ev in db_a.evidences
            ],
            [FraudType(f) if isinstance(f, str) else f for f in db_a.fraud_types],
            RiskLevel(db_a.risk_level) if isinstance(db_a.risk_level, str) else db_a.risk_level,
        ),
        recommended_actions=db_a.recommendations or [],
        ai_media=(
            next((d.metadata_.get("ai_media") for d in db_a.detectors if d.metadata_ and "ai_media" in d.metadata_), None)
            or (db_a.extracted_content.get("ai_media") if db_a.extracted_content else None)
        ),
        multimodal_findings=explainer.generate_multimodal_findings(
            [
                EvidenceItem(
                    evidence_type=ev.evidence_type,
                    source_modality=ev.source_modality,
                    target_modality=ev.target_modality,
                    content=ev.content,
                    severity=ev.severity,
                    relationship=ev.evidence_relationship,
                )
                for ev in db_a.evidences
            ],
            [
                DetectorResult(
                    module=d.module,
                    fraud_probability=d.fraud_probability,
                    confidence=d.confidence,
                    risk=RiskLevel(d.risk) if isinstance(d.risk, str) else d.risk,
                    signals=d.signals,
                    model_version=d.model_version,
                    processing_time_ms=d.processing_time_ms,
                    metadata=d.metadata_,
                )
                for d in db_a.detectors
            ],
            db_a.extracted_content or {},
        ),
    )

