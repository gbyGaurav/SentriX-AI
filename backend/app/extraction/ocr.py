"""OCR extraction module using RapidOCR with pytesseract and PyMuPDF graceful fallbacks."""

import io
import gc
import logging
from typing import Optional
from PIL import Image

logger = logging.getLogger(__name__)

import sys
import subprocess
import os

OCR_SUBPROCESS_SCRIPT = """
import sys, os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

try:
    from rapidocr_onnxruntime import RapidOCR
    ocr = RapidOCR(use_cls=False, max_side_len=1024)
    data = sys.stdin.buffer.read()
    if data:
        result, _ = ocr(data)
        if result:
            lines = [line[1] for line in result if len(line) > 1 and line[1]]
            text = "\\n".join(lines).strip()
            if text:
                sys.stdout.write(text)
                sys.stdout.flush()
except Exception:
    pass
"""


def extract_text_with_ocr(image_bytes: bytes) -> Optional[str]:
    """Attempts to run OCR on image bytes.
    Executes in an isolated subprocess to ensure any ONNX Runtime crash,
    C++ OpenMP collision, or memory spike is quarantined without affecting the
    main web server.
    """
    if not image_bytes:
        return None

    # Pre-resize image if dimensions exceed 1500px to protect memory
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

    # 1. Run in quarantined subprocess
    try:
        proc = subprocess.run(
            [sys.executable, "-c", OCR_SUBPROCESS_SCRIPT],
            input=processed_bytes,
            capture_output=True,
            timeout=15.0
        )
        if proc.returncode == 0:
            extracted_text = proc.stdout.decode("utf-8", errors="replace").strip()
            if extracted_text:
                return extracted_text
        else:
            logger.debug(f"OCR subprocess exited with code {proc.returncode}")
    except subprocess.TimeoutExpired:
        logger.warning("OCR subprocess timed out after 15s; continuing without OCR")
    except Exception as e:
        logger.debug(f"OCR subprocess execution failed: {e}")

    # 2. Fallback to pytesseract if installed
    try:
        import pytesseract
        image = Image.open(io.BytesIO(processed_bytes))
        if image.mode not in ("L", "RGB"):
            image = image.convert("RGB")
        text = pytesseract.image_to_string(image)
        if text and text.strip():
            return text.strip()
    except Exception as e:
        logger.debug(f"pytesseract fallback skipped: {e}")

    return None

