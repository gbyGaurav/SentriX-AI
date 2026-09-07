"""Multimodal Modality Router with Multi-Tier Cascading Analysis.
Routes any classified input to its primary detector, extracts secondary modalities
(e.g., text, URLs, QRs, metadata), runs subsequent specialized detectors concurrently,
and constructs cross-modal evidence graph relationships.
"""

import asyncio
import logging
from typing import Tuple, List, Dict, Optional, Any

from app.schemas.analysis import InputType, DetectorResult, EvidenceItem
from app.fusion.evidence_graph import EvidenceGraph

logger = logging.getLogger(__name__)


class ModalityRouter:
    """Intelligent router that dispatches inputs and handles cross-modal cascading."""

    def __init__(self):
        self.detectors = {}
        self._register_detectors()

    def _register_detectors(self):
        from app.detectors.url.detector import URLDetector
        from app.detectors.text.detector import TextDetector
        from app.detectors.qr.detector import QRDetector
        from app.detectors.document.detector import DocumentDetector
        from app.detectors.image.detector import ImageDetector
        from app.detectors.video.detector import VideoDetector
        from app.detectors.audio.detector import AudioDetector

        self.url_detector = URLDetector()
        self.text_detector = TextDetector()
        self.qr_detector = QRDetector()
        self.document_detector = DocumentDetector()
        self.image_detector = ImageDetector()
        self.video_detector = VideoDetector()
        self.audio_detector = AudioDetector()

        self.detectors = {
            InputType.URL: self.url_detector,
            InputType.TEXT: self.text_detector,
            InputType.EMAIL: self.text_detector,
            InputType.QR: self.qr_detector,
            InputType.PDF: self.document_detector,
            InputType.DOCUMENT: self.document_detector,
            InputType.IMAGE: self.image_detector,
            InputType.VIDEO: self.video_detector,
            InputType.AUDIO: self.audio_detector,
        }

    async def route_and_analyze(
        self,
        input_type: InputType,
        *,
        file_bytes: Optional[bytes] = None,
        text: Optional[str] = None,
        url: Optional[str] = None,
        filename: Optional[str] = None
    ) -> Tuple[List[DetectorResult], List[EvidenceItem], Dict[str, Any]]:
        """Executes primary analysis, discovers secondary modalities,
        and cascades through child detectors concurrently.
        """
        detector_results: List[DetectorResult] = []
        evidence_graph = EvidenceGraph()
        extracted_content: Dict[str, Any] = {}

        primary_detector = self.detectors.get(input_type)
        if not primary_detector:
            logger.warning(f"No detector registered for input type: {input_type}")
            return [], [], {}

        kwargs = {
            "text": text,
            "url": url,
            "file_bytes": file_bytes,
            "filename": filename,
        }

        # 1. Primary analysis execution
        try:
            primary_res = await primary_detector.analyze(**kwargs)
            detector_results.append(primary_res)
        except Exception as e:
            logger.error(f"Primary detector error ({primary_detector.module_name}): {e}", exc_info=True)
            return [], [], {}

        # 2. Gather extracted content from metadata
        meta = primary_res.metadata or {}
        extracted_urls = list(meta.get("extracted_urls", []))
        extracted_text = meta.get("extracted_text") or meta.get("transcript") or ""
        extracted_qrs = list(meta.get("extracted_qrs", []))
        extracted_emails = list(meta.get("extracted_emails", []))
        extracted_phones = list(meta.get("extracted_phones", []))

        # Save to extracted content dictionary
        if extracted_text:
            extracted_content["extracted_text"] = extracted_text
        if extracted_urls:
            extracted_content["extracted_urls"] = extracted_urls
        if extracted_emails:
            extracted_content["extracted_emails"] = extracted_emails
        if extracted_phones:
            extracted_content["extracted_phones"] = extracted_phones
        if meta.get("image_metadata"):
            extracted_content["metadata"] = meta["image_metadata"]
        elif meta.get("video_metadata"):
            extracted_content["metadata"] = meta["video_metadata"]
        elif meta.get("metadata"):
            extracted_content["metadata"] = meta["metadata"]

        # 3. Cascading Tier 1: Process extracted QRs, Text, URLs concurrently
        cascade_tasks = []
        task_tags = []

        # (a) If Image or Video found QR codes -> Cascade to QR Detector
        for qr_data in extracted_qrs:
            evidence_graph.add_relationship(
                source=input_type.value,
                relationship="contains_qr",
                target="QR",
                content=qr_data,
                severity="warning"
            )
            cascade_tasks.append(self.qr_detector.analyze(qr_content=qr_data))
            task_tags.append(("QR", qr_data))

        # (b) If Document / Image OCR / Video OCR found text -> Cascade to Text Detector
        if extracted_text and input_type not in (InputType.TEXT, InputType.EMAIL):
            evidence_graph.add_relationship(
                source=input_type.value,
                relationship="contains_text",
                target="TEXT",
                content=extracted_text[:200] + ("..." if len(extracted_text) > 200 else ""),
                severity="info"
            )
            cascade_tasks.append(self.text_detector.analyze(text=extracted_text))
            task_tags.append(("TEXT", extracted_text))

        # (c) If Primary or QR directly yielded URLs -> Cascade to URL Detector
        seen_urls = set()
        for u in extracted_urls:
            if u not in seen_urls:
                seen_urls.add(u)
                evidence_graph.add_relationship(
                    source=input_type.value,
                    relationship="contains_url",
                    target="URL",
                    content=u,
                    severity="warning" if ("login" in u.lower() or "verify" in u.lower()) else "info"
                )
                cascade_tasks.append(self.url_detector.analyze(url=u))
                task_tags.append(("URL", u))

        # Execute Tier 1 Cascading
        if cascade_tasks:
            results = await asyncio.gather(*cascade_tasks, return_exceptions=True)
            for (tag, source_val), res in zip(task_tags, results):
                if isinstance(res, DetectorResult):
                    detector_results.append(res)
                    # 4. Cascading Tier 2: If Tier 1 Text or QR yielded further URLs, analyze them!
                    child_urls = res.metadata.get("extracted_urls", [])
                    for cu in child_urls:
                        if cu not in seen_urls:
                            seen_urls.add(cu)
                            evidence_graph.add_relationship(
                                source=tag,
                                relationship="resolves_to_url",
                                target="URL",
                                content=cu,
                                severity="critical"
                            )
                            # Run child URL detector
                            try:
                                url_res = await self.url_detector.analyze(url=cu)
                                detector_results.append(url_res)
                            except Exception as e:
                                logger.debug(f"Secondary URL analysis error: {e}")

        return detector_results, evidence_graph.get_evidence_summary(), extracted_content
