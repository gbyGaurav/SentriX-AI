"""OCR extraction module using Tesseract with safe graceful fallback."""

import io
import logging
from typing import Optional
from PIL import Image

logger = logging.getLogger(__name__)


def extract_text_with_ocr(image_bytes: bytes) -> Optional[str]:
    """Attempts to run OCR on image bytes using pytesseract.
    Returns extracted text string, or None if OCR is unavailable/failed.
    """
    try:
        import pytesseract
        image = Image.open(io.BytesIO(image_bytes))
        # Convert RGBA or Palette to RGB
        if image.mode not in ("L", "RGB"):
            image = image.convert("RGB")
        text = pytesseract.image_to_string(image)
        return text.strip() if text else None
    except Exception as e:
        logger.debug(f"OCR not available or failed: {e}")
        return None
