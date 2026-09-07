"""OCR extraction module using RapidOCR with pytesseract and PyMuPDF graceful fallbacks."""

import io
import gc
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
            # use_cls=False avoids loading the direction-classification model (cls.onnx)
            # max_side_len=1024 caps the internal detection feature map
            _rapid_ocr_instance = RapidOCR(use_cls=False, max_side_len=1024)
            logger.info("RapidOCR initialized with memory-optimized parameters.")
        except Exception as e:
            logger.debug(f"RapidOCR unavailable: {e}")
            _rapid_ocr_instance = False
    return _rapid_ocr_instance if _rapid_ocr_instance is not False else None


def extract_text_with_ocr(image_bytes: bytes) -> Optional[str]:
    """Attempts to run OCR on image bytes.
    First tries RapidOCR (self-contained ONNX runtime), then falls back to pytesseract.
    Pre-downsamples images exceeding 1500px to keep memory footprint under 25MB.
    Returns extracted text string, or None if OCR is unavailable/empty.
    """
    if not image_bytes:
        return None

    # Pre-resize image if dimensions exceed 1500px to protect Render free-tier RAM
    processed_bytes = image_bytes
    try:
        with Image.open(io.BytesIO(image_bytes)) as pil_img:
            max_d = max(pil_img.width, pil_img.height)
            if max_d > 1500:
                scale = 1500.0 / max_d
                new_w = max(1, int(pil_img.width * scale))
                new_h = max(1, int(pil_img.height * scale))
                resized = pil_img.resize((new_w, new_h), Image.Resampling.BILINEAR)
                buf = io.BytesIO()
                if resized.mode not in ("RGB", "L"):
                    resized = resized.convert("RGB")
                resized.save(buf, format="JPEG", quality=85)
                processed_bytes = buf.getvalue()
    except Exception as e:
        logger.debug(f"OCR pre-resize skipped: {e}")

    extracted_text = None

    # 1. Try RapidOCR (high accuracy, self-contained)
    ocr_engine = _get_rapid_ocr()
    if ocr_engine:
        try:
            result, _ = ocr_engine(processed_bytes)
            if result:
                lines = [line[1] for line in result if len(line) > 1 and line[1]]
                full_text = "\n".join(lines).strip()
                if full_text:
                    extracted_text = full_text
        except Exception as e:
            logger.debug(f"RapidOCR execution error: {e}")

    # 2. Fallback to pytesseract if installed
    if not extracted_text:
        try:
            import pytesseract
            image = Image.open(io.BytesIO(processed_bytes))
            if image.mode not in ("L", "RGB"):
                image = image.convert("RGB")
            text = pytesseract.image_to_string(image)
            if text and text.strip():
                extracted_text = text.strip()
        except Exception as e:
            logger.debug(f"pytesseract fallback failed: {e}")

    # Clean up memory
    gc.collect()
    return extracted_text

