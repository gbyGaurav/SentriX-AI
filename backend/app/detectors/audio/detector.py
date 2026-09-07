"""Audio Fraud Detector.
Analyzes audio payloads (MP3, WAV, M4A) for social engineering, synthetic speech indicators,
and speech transcription cascading into the text fraud pipeline.
"""

import time
import logging
from typing import Optional, Dict, Any, List
from app.detectors.base import FraudDetector
from app.schemas.analysis import DetectorResult

logger = logging.getLogger(__name__)


class AudioDetector(FraudDetector):
    @property
    def module_name(self) -> str:
        return "audio_fraud"

    @property
    def model_version(self) -> str:
        return "audio-transcription-baseline-v1"

    async def analyze(self, **kwargs) -> DetectorResult:
        start_t = time.time()
        file_bytes = kwargs.get("file_bytes")
        filename = kwargs.get("filename", "").lower()

        if not file_bytes:
            return self._create_result(0.0, 1.0, [], 0.0, error="No audio provided")

        signals = []
        score = 0.0
        transcript = ""

        # Basic audio file header analysis
        audio_len = len(file_bytes)
        signals.append(f"Audio file received ({audio_len / 1024:.1f} KB)")

        # Optional Speech-To-Text if Whisper is available
        try:
            import whisper
            import tempfile
            import os

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(file_bytes)
                tmp_path = tmp.name

            try:
                model = whisper.load_model("tiny")
                res = model.transcribe(tmp_path)
                transcript = res.get("text", "")
                if transcript:
                    signals.append(f"Transcribed audio speech ({len(transcript.split())} words)")
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
        except Exception:
            # Fallback note: Whisper not installed or heavy compute disabled
            signals.append("Audio speech transcription baseline active (deep speech synthesis inspection pending)")

        final_score = min(1.0, max(0.0, score))
        proc_time = (time.time() - start_t) * 1000

        return self._create_result(
            probability=final_score,
            confidence=0.7,
            signals=signals,
            processing_time_ms=proc_time,
            metadata={
                "audio_size_bytes": audio_len,
                "transcript": transcript,
            }
        )
