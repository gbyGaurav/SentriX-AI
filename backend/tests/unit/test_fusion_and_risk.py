import pytest
from app.schemas.analysis import DetectorResult, RiskLevel, FraudType, EvidenceItem
from app.fusion.fusion_engine import FusionEngine
from app.fusion.risk_engine import RiskEngine


def test_fusion_empty():
    fusion = FusionEngine()
    prob, conf = fusion.fuse([])
    assert prob == 0.0
    assert conf == 0.0


def test_fusion_single_detector():
    fusion = FusionEngine()
    res = DetectorResult(
        module="url_fraud",
        fraud_probability=0.8,
        confidence=0.9,
        risk=RiskLevel.HIGH,
        signals=[],
        model_version="v1",
        processing_time_ms=10.0,
    )
    prob, conf = fusion.fuse([res])
    assert prob == 0.8
    assert conf == 0.9


def test_risk_engine_critical_threshold():
    risk_engine = RiskEngine()
    det1 = DetectorResult(
        module="url_fraud",
        fraud_probability=0.9,
        confidence=0.85,
        risk=RiskLevel.CRITICAL,
        signals=["Suspicious URL", "Credential request"],
        model_version="v1",
        processing_time_ms=10.0,
    )
    det2 = DetectorResult(
        module="text_fraud",
        fraud_probability=0.95,
        confidence=0.90,
        risk=RiskLevel.CRITICAL,
        signals=["High urgency language"],
        model_version="v1",
        processing_time_ms=10.0,
    )
    evidence = [
        EvidenceItem(
            evidence_type="text_contains_url",
            source_modality="TEXT",
            target_modality="URL",
            content="http://bad.xyz",
            severity="critical",
            relationship="contains_url",
        )
    ]

    score, level, fraud_types, conf = risk_engine.calculate_risk(0.92, 0.87, [det1, det2], evidence)
    assert score >= 81
    assert level == RiskLevel.CRITICAL
    assert FraudType.PHISHING in fraud_types or FraudType.SOCIAL_ENGINEERING in fraud_types
