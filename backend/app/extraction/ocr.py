"""OCR extraction module using RapidOCR with pytesseract and PyMuPDF graceful fallbacks."""

import io
import logging
from typing import Optional
from PIL import Image

logger = logging.getLogger(__name__)

_rapid_ocr_instance = None


def _get_rapid_ocr():
    global _rapid_ocr_instance
    if _rapid_ocr_instance is None:
        try:
            from rapidocr_onnxruntime import RapidOCR
            _rapid_ocr_instance = RapidOCR()
            logger.info("RapidOCR initialized successfully.")
        except Exception as e:
            logger.debug(f"RapidOCR unavailable: {e}")
            _rapid_ocr_instance = False
    return _rapid_ocr_instance if _rapid_ocr_instance is not False else None


def extract_text_with_ocr(image_bytes: bytes) -> Optional[str]:
    """Attempts to run OCR on image bytes.
    First tries RapidOCR (self-contained ONNX runtime), then falls back to pytesseract.
    Returns extracted text string, or None if OCR is unavailable/empty.
    """
    if not image_bytes:
        return None

    # 1. Try RapidOCR (high accuracy, self-contained)
    ocr_engine = _get_rapid_ocr()
    if ocr_engine:
        try:
            result, _ = ocr_engine(image_bytes)
            if result:
                lines = [line[1] for line in result if len(line) > 1 and line[1]]
                full_text = "\n".join(lines).strip()
                if full_text:
                    return full_text
        except Exception as e:
            logger.debug(f"RapidOCR execution error: {e}")

    # 2. Fallback to pytesseract if installed
    try:
        import pytesseract
        image = Image.open(io.BytesIO(image_bytes))
        if image.mode not in ("L", "RGB"):
            image = image.convert("RGB")
        text = pytesseract.image_to_string(image)
        return text.strip() if text else None
    except Exception as e:
        logger.debug(f"pytesseract fallback failed: {e}")

    return None
