"""Video Fraud & Deepfake Detector.
Analyzes sampled frames, metadata consistency, inter-frame temporal variations,
and OCR on representative frames without loading large video files into memory.
"""

import time
import io
import logging
from typing import Optional, Dict, Any, List
import numpy as np
import cv2
from app.detectors.base import FraudDetector
from app.schemas.analysis import DetectorResult
from app.extraction.video import sample_video_frames
from app.extraction.ocr import extract_text_with_ocr
from app.extraction.qr import extract_qr_from_bytes

logger = logging.getLogger(__name__)


class VideoDetector(FraudDetector):
    @property
    def module_name(self) -> str:
        return "video_fraud"

    @property
    def model_version(self) -> str:
        return "video-temporal-analyzer-v1"

    async def analyze(self, **kwargs) -> DetectorResult:
        start_t = time.time()
        file_bytes = kwargs.get("file_bytes")

        if not file_bytes:
            return self._create_result(0.0, 1.0, [], 0.0, error="No video content provided")

        # 1. Sample frames and extract video metadata (max 4 keyframes to maintain 512MB RAM budget)
        sampled = sample_video_frames(file_bytes, max_frames=4, sample_rate_sec=2.0)
        if sampled.get("error"):
            return self._create_result(
                probability=0.0,
                confidence=0.3,
                signals=["Video stream could not be parsed."],
                processing_time_ms=(time.time() - start_t) * 1000,
                error=sampled["error"],
            )

        frames = sampled.get("frames", [])
        metadata = sampled.get("metadata", {})
        frames_analyzed = len(frames)

        score = 0.0
        signals = []
        extracted_texts = []
        extracted_urls = []

        if frames_analyzed == 0:
            return self._create_result(
                probability=0.0,
                confidence=0.4,
                signals=["No readable video frames could be extracted."],
                processing_time_ms=(time.time() - start_t) * 1000,
            )

        signals.append(f"Sampled {frames_analyzed} keyframes across {sampled.get('duration_sec', 0)}s duration")

        # 2. Temporal consistency analysis between consecutive frames
        frame_diffs = []
        for i in range(len(frames) - 1):
            try:
                curr_bytes = frames[i][1]
                next_bytes = frames[i+1][1]
                img1 = cv2.imdecode(np.frombuffer(curr_bytes, np.uint8), cv2.IMREAD_GRAYSCALE)
                img2 = cv2.imdecode(np.frombuffer(next_bytes, np.uint8), cv2.IMREAD_GRAYSCALE)
                if img1 is not None and img2 is not None and img1.shape == img2.shape:
                    diff = cv2.absdiff(img1, img2)
                    frame_diffs.append(float(np.mean(diff)))
            except Exception as e:
                logger.debug(f"Frame diff error: {e}")

        if frame_diffs:
            mean_diff = float(np.mean(frame_diffs))
            max_diff = float(np.max(frame_diffs))
            metadata["mean_temporal_diff"] = round(mean_diff, 2)
            metadata["max_temporal_diff"] = round(max_diff, 2)

            # Abrupt temporal jumps or unnatural flickering (common in early deepfake synthesis)
            if max_diff > 45.0 and mean_diff < 15.0:
                score += 0.25
                signals.append("Temporal discontinuity: localized sudden jump cuts / unnatural artifact flicker detected")

        # 3. OCR and QR scanning on sampled frames (sample first, middle, last)
        sample_indices = [0, len(frames) // 2, len(frames) - 1]
        seen_texts = set()
        for idx in set(sample_indices):
            if idx < len(frames):
                frame_jpg = frames[idx][1]
                # Check for on-screen scam text
                text = extract_text_with_ocr(frame_jpg)
                if text and text not in seen_texts:
                    seen_texts.add(text)
                    extracted_texts.append(text)
                
                # Check for on-screen QR codes
                qrs = extract_qr_from_bytes(frame_jpg)
                if qrs:
                    for qr_val, _ in qrs:
                        extracted_urls.append(qr_val)
                        signals.append(f"Video frame contains embedded QR code pointing to: {qr_val[:40]}")
                        score += 0.25

        if extracted_texts:
            signals.append(f"Text overlay detected across {len(extracted_texts)} video keyframes")

        # Video metadata flags
        if metadata.get("fps", 0) < 12.0:
            score += 0.15
            signals.append("Abnormally low framerate (< 12 fps), typical of rendered spoofing loops")

        final_score = min(1.0, max(0.0, score))
        proc_time = (time.time() - start_t) * 1000

        return self._create_result(
            probability=final_score,
            confidence=0.82,
            signals=signals,
            processing_time_ms=proc_time,
            metadata={
                "frames_analyzed": frames_analyzed,
                "video_metadata": metadata,
                "sampled_frames": [f[1] for f in frames[:4]],
                "extracted_texts": extracted_texts,
                "extracted_urls": extracted_urls,
            }
        )
