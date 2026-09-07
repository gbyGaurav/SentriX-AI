"""Automatic Input Type Classifier.
Examines MIME types, file magic signatures, text structures, URLs, and image contents
to accurately route any input without requiring manual user selection.
"""

import re
import logging
from typing import Optional
from fastapi import UploadFile
try:
    import magic
except Exception:
    magic = None

from app.schemas.analysis import InputType
from app.extraction.qr import extract_qr_from_bytes

logger = logging.getLogger(__name__)


class InputClassifier:
    """Automatically determines the modality of user input."""

    async def classify(
        self,
        *,
        file: Optional[UploadFile] = None,
        text: Optional[str] = None,
        url: Optional[str] = None
    ) -> InputType:
        # 1. Direct URL provided
        if url and url.strip():
            return InputType.URL

        # 2. Text or pasted content provided
        if text and text.strip():
            cleaned = text.strip()
            if self._is_url(cleaned):
                return InputType.URL
            if self._is_email_content(cleaned):
                return InputType.EMAIL
            return InputType.TEXT

        # 3. File upload provided
        if file:
            # Read first 4096 bytes for MIME detection
            header_bytes = await file.read(4096)
            await file.seek(0)
            
            # Read full bytes for accurate classification if reasonable size
            full_bytes = await file.read()
            await file.seek(0)

            mime_type = file.content_type or ""
            if magic:
                try:
                    detected_mime = magic.from_buffer(header_bytes, mime=True)
                    if detected_mime:
                        mime_type = detected_mime
                except Exception as e:
                    logger.debug(f"Magic byte detection error: {e}")

            filename = file.filename or ""
            extension = filename.split(".")[-1].lower() if "." in filename else ""

            # Check if image contains QR code
            if mime_type.startswith("image/") or extension in ("png", "jpg", "jpeg", "webp", "bmp"):
                has_qr = await self._check_qr(full_bytes)
                if has_qr:
                    return InputType.QR
                return InputType.IMAGE

            return self._mime_to_input_type(mime_type, extension)

        return InputType.UNKNOWN

    def _is_url(self, text: str) -> bool:
        url_pattern = re.compile(
            r'^(?:https?://|www\.)[a-zA-Z0-9\-._~:/?#\[\]@!$&\'()*+,;=]+$',
            re.IGNORECASE
        )
        return bool(url_pattern.match(text.strip()))

    def _is_email_content(self, text: str) -> bool:
        headers = ["From:", "To:", "Subject:", "Date:", "MIME-Version:"]
        matches = sum(1 for h in headers if h.lower() in text.lower())
        return matches >= 2

    async def _check_qr(self, file_bytes: bytes) -> bool:
        """Inspects whether image bytes encode a detectable QR code."""
        if not file_bytes:
            return False
        try:
            results = extract_qr_from_bytes(file_bytes)
            return len(results) > 0
        except Exception:
            return False

    def _mime_to_input_type(self, mime_type: str, extension: str) -> InputType:
        if mime_type.startswith("video/") or extension in ("mp4", "mov", "webm", "avi", "mkv"):
            return InputType.VIDEO
        if mime_type.startswith("audio/") or extension in ("mp3", "wav", "m4a", "ogg", "flac"):
            return InputType.AUDIO
        if mime_type == "application/pdf" or extension == "pdf":
            return InputType.PDF
        if (
            "document" in mime_type
            or "msword" in mime_type
            or extension in ("docx", "doc", "rtf", "odt")
        ):
            return InputType.DOCUMENT
        if mime_type.startswith("text/") or extension in ("txt", "csv", "log"):
            return InputType.TEXT

        return InputType.UNKNOWN
