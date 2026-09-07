"""QR code extraction and decoding module.
Uses OpenCV's QRCodeDetector with robust fallback handling.
"""

import io
import logging
from typing import List, Tuple, Optional
from PIL import Image
import numpy as np

logger = logging.getLogger(__name__)


def extract_qr_from_bytes(image_bytes: bytes) -> List[Tuple[str, Optional[dict]]]:
    """Extract and decode QR codes from image bytes.
    Returns a list of (decoded_text, metadata).
    """
    results = []
    
    # 1. Try OpenCV QRCodeDetector
    try:
        import cv2
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is not None:
            # Standard single/multi detector
            detector = cv2.QRCodeDetector()
            # Try multi first
            retval, decoded_info, points, _ = detector.detectAndDecodeMulti(img)
            if retval and decoded_info:
                for text in decoded_info:
                    text_str = text.strip() if isinstance(text, str) else ""
                    if text_str:
                        results.append((text_str, {"engine": "opencv_multi"}))
            
            # Fallback to single if multi didn't find anything
            if not results:
                val, pts, _ = detector.detectAndDecode(img)
                if val and val.strip():
                    results.append((val.strip(), {"engine": "opencv_single"}))
    except Exception as e:
        logger.debug(f"OpenCV QR decode attempt error: {e}")

    # 2. Try pyzbar if installed
    if not results:
        try:
            from pyzbar.pyzbar import decode as pyzbar_decode
            image = Image.open(io.BytesIO(image_bytes))
            decoded_objects = pyzbar_decode(image)
            for obj in decoded_objects:
                data = obj.data.decode("utf-8", errors="ignore").strip()
                if data:
                    results.append((data, {"engine": "pyzbar", "type": obj.type}))
        except Exception as e:
            logger.debug(f"Pyzbar QR decode attempt error: {e}")

    return results
