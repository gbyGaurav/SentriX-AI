"""Multimodal Modality Router with Multi-Tier Cascading Analysis.
Routes classified inputs to specialized detectors using lazy initialization,
sequential execution for memory-heavy modalities (to respect 512MB RAM limits),
and builds cross-modal evidence graphs.
"""

import gc
import logging
from typing import Tuple, List, Dict, Optional, Any

from app.schemas.analysis import InputType, DetectorResult, EvidenceItem
from app.fusion.evidence_graph import EvidenceGraph

logger = logging.getLogger(__name__)


class ModalityRouter:
    """Intelligent router that dispatches inputs and handles cross-modal cascading
    with lazy singleton initialization and strict memory protection.
    """

    def __init__(self):
        # Lazy detector cache: modules are imported and instantiated ONLY on demand
        self._detectors: Dict[str, Any] = {}

    def _get_detector(self, name: str):
        if name in self._detectors:
            return self._detectors[name]

        if name == "url":
            from app.detectors.url.detector import URLDetector
            det = URLDetector()
        elif name == "text":
            from app.detectors.text.detector import TextDetector
            det = TextDetector()
        elif name == "spam":
            from app.detectors.spam.detector import SpamDetector
            det = SpamDetector()
        elif name == "qr":
            from app.detectors.qr.detector import QRDetector
            det = QRDetector()
        elif name == "document":
            from app.detectors.document.detector import DocumentDetector
            det = DocumentDetector()
        elif name == "image":
            from app.detectors.image.detector import ImageDetector
            det = ImageDetector()
        elif name == "video":
            from app.detectors.video.detector import VideoDetector
            det = VideoDetector()
        elif name == "audio":
            from app.detectors.audio.detector import AudioDetector
            det = AudioDetector()
        elif name == "ai_media":
            from app.detectors.ai_media.detector import AIMediaDetector
            det = AIMediaDetector()
        else:
            raise ValueError(f"Unknown detector name: {name}")

        self._detectors[name] = det
        return det

    @property
    def url_detector(self):
        return self._get_detector("url")

    @property
    def text_detector(self):
        return self._get_detector("text")

    @property
    def spam_detector(self):
        return self._get_detector("spam")

    @property
    def qr_detector(self):
        return self._get_detector("qr")

    @property
    def document_detector(self):
        return self._get_detector("document")

    @property
    def image_detector(self):
        return self._get_detector("image")

    @property
    def video_detector(self):
        return self._get_detector("video")

    @property
    def audio_detector(self):
        return self._get_detector("audio")

    @property
    def ai_media_detector(self):
        return self._get_detector("ai_media")

    def _get_primary_detector(self, input_type: InputType):
        mapping = {
            InputType.URL: "url",
            InputType.TEXT: "text",
            InputType.EMAIL: "text",
            InputType.QR: "qr",
            InputType.PDF: "document",
            InputType.DOCUMENT: "document",
            InputType.IMAGE: "image",
            InputType.VIDEO: "video",
            InputType.AUDIO: "audio",
        }
        name = mapping.get(input_type)
        return self._get_detector(name) if name else None

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
        and cascades through child detectors sequentially for memory safety.
        """
        detector_results: List[DetectorResult] = []
        evidence_graph = EvidenceGraph()
        extracted_content: Dict[str, Any] = {}

        kwargs = {
            "text": text,
            "url": url,
            "file_bytes": file_bytes,
            "filename": filename,
        }

        # 1. Primary analysis execution (Sequential to prevent memory spikes on 512MB RAM)
        try:
            if input_type in (InputType.TEXT, InputType.EMAIL):
                t_res = await self.text_detector.analyze(**kwargs)
                detector_results.append(t_res)
                primary_res = t_res

                s_res = await self.spam_detector.analyze(**kwargs)
                detector_results.append(s_res)

            elif input_type == InputType.IMAGE:
                # Step 1: Run image fraud analysis
                img_res = await self.image_detector.analyze(**kwargs)
                detector_results.append(img_res)
                primary_res = img_res
                gc.collect()

                # Step 2: Run AI media detection sequentially
                ai_res = await self.ai_media_detector.analyze(file_bytes=file_bytes)
                detector_results.append(ai_res)
                if ai_res.metadata and "ai_media" in ai_res.metadata:
                    extracted_content["ai_media"] = ai_res.metadata["ai_media"]
                gc.collect()

            elif input_type == InputType.VIDEO:
                # Step 1: Run video fraud analysis
                vid_res = await self.video_detector.analyze(**kwargs)
                detector_results.append(vid_res)
                primary_res = vid_res
                gc.collect()

                # Step 2: Run AI media detection on sampled frames sequentially
                sampled_frames = [f[1] for f in vid_res.metadata.get("sampled_frames", [])[:2]]
                ai_res = await self.ai_media_detector.analyze(frames_bytes=sampled_frames)
                detector_results.append(ai_res)
                if ai_res.metadata and "ai_media" in ai_res.metadata:
                    extracted_content["ai_media"] = ai_res.metadata["ai_media"]
                gc.collect()

            else:
                primary_detector = self._get_primary_detector(input_type)
                if not primary_detector:
                    logger.warning(f"No detector registered for input type: {input_type}")
                    return [], [], {}
                primary_res = await primary_detector.analyze(**kwargs)
                detector_results.append(primary_res)

        except Exception as e:
            logger.error(f"Primary detector error for {input_type}: {e}", exc_info=True)
            return [], [], {}

        # 2. Gather extracted content from metadata
        meta = primary_res.metadata or {}
        extracted_urls = list(meta.get("extracted_urls", []))
        extracted_text = meta.get("extracted_text") or meta.get("transcript") or ""
        extracted_qrs = list(meta.get("extracted_qrs", []))
        extracted_emails = list(meta.get("extracted_emails", []))
        extracted_phones = list(meta.get("extracted_phones", []))

        # Check secondary detectors for additional metadata
        for det in detector_results:
            if det.metadata:
                for u in det.metadata.get("extracted_urls", []):
                    if u not in extracted_urls:
                        extracted_urls.append(u)
                if not extracted_text and det.metadata.get("extracted_text"):
                    extracted_text = det.metadata.get("extracted_text")
                if "ai_media" in det.metadata and "ai_media" not in extracted_content:
                    extracted_content["ai_media"] = det.metadata["ai_media"]

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

        # 3. Cascading Tier 1: Process extracted QRs, Text, URLs sequentially
        seen_urls = set()

        # (a) If Image or Video found QR codes -> Cascade to QR Detector
        for qr_data in extracted_qrs:
            evidence_graph.add_relationship(
                source=input_type.value,
                relationship="contains_qr",
                target="QR",
                content=qr_data,
                severity="warning"
            )
            try:
                qr_res = await self.qr_detector.analyze(qr_content=qr_data)
                detector_results.append(qr_res)
                # Check for URLs inside QR
                for qu in qr_res.metadata.get("extracted_urls", []):
                    if qu not in extracted_urls:
                        extracted_urls.append(qu)
            except Exception as e:
                logger.debug(f"Cascading QR analysis error: {e}")

        # (b) If Document / Image OCR / Video OCR found text -> Cascade to Text AND Spam Detector
        if extracted_text and input_type not in (InputType.TEXT, InputType.EMAIL):
            evidence_graph.add_relationship(
                source=input_type.value,
                relationship="contains_text",
                target="TEXT",
                content=extracted_text[:200] + ("..." if len(extracted_text) > 200 else ""),
                severity="info"
            )
            try:
                t_res = await self.text_detector.analyze(text=extracted_text)
                detector_results.append(t_res)
                for tu in t_res.metadata.get("extracted_urls", []):
                    if tu not in extracted_urls:
                        extracted_urls.append(tu)
            except Exception as e:
                logger.debug(f"Cascading text analysis error: {e}")

            try:
                s_res = await self.spam_detector.analyze(text=extracted_text)
                detector_results.append(s_res)
            except Exception as e:
                logger.debug(f"Cascading spam analysis error: {e}")

        # (c) If Primary or Casings yielded URLs -> Cascade to URL Detector
        for u in extracted_urls[:5]:  # Cap at 5 URLs to protect resources
            if u not in seen_urls:
                seen_urls.add(u)
                evidence_graph.add_relationship(
                    source=input_type.value,
                    relationship="contains_url",
                    target="URL",
                    content=u,
                    severity="warning" if any(k in u.lower() for k in ("login", "verify", "pay", "bank")) else "info"
                )
                try:
                    url_res = await self.url_detector.analyze(url=u)
                    detector_results.append(url_res)
                except Exception as e:
                    logger.debug(f"Cascading URL analysis error: {e}")

        # Clean up memory after completing analysis pipeline
        gc.collect()

        return detector_results, evidence_graph.get_evidence_summary(), extracted_content

