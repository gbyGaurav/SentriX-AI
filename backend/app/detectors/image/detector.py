"""Image Fraud & Authenticity Detector.
Performs:
1. EXIF and metadata analysis (photoshop signatures, AI generator tags, editing traces)
2. Error Level Analysis (ELA) baseline for localized manipulation / copy-move detection
3. OCR extraction for text overlays (e.g. lottery winner screenshots, fake transaction receipts)
4. Detection of embedded QR codes
"""

import io
import time
import logging
from typing import Optional, Dict, Any, List
import numpy as np
from PIL import Image, ImageChops, ImageEnhance
from app.detectors.base import FraudDetector
from app.schemas.analysis import DetectorResult
from app.extraction.ocr import extract_text_with_ocr
from app.extraction.qr import extract_qr_from_bytes

logger = logging.getLogger(__name__)

KNOWN_EDITING_SOFTWARE = [
    "photoshop", "gimp", "canva", "picsart", "lightroom", "pixlr", "snapseed", "midjourney", "stable diffusion", "dall-e"
]


def perform_ela(image: Image.Image, quality: int = 90) -> float:
    """Error Level Analysis (ELA).
    Resaves image at specified JPEG quality and computes pixel difference.
    Returns the average difference ratio across modified blocks.
    """
    try:
        if image.mode != "RGB":
            image = image.convert("RGB")

        # Save to buffer at known quality
        buffer = io.BytesIO()
        image.save(buffer, "JPEG", quality=quality)
        buffer.seek(0)
        resaved = Image.open(buffer)

        # Difference
        diff = ImageChops.difference(image, resaved)
        diff_arr = np.array(diff, dtype=np.float32)
        
        # Standard deviation and max difference across high error areas
        mean_diff = float(np.mean(diff_arr))
        std_diff = float(np.std(diff_arr))
        
        # High std with moderate mean indicates localized resaved regions (splicing/tampering)
        ela_anomaly_score = min(1.0, (std_diff / 25.0) * (1.0 if mean_diff > 3.0 else 0.5))
        return ela_anomaly_score
    except Exception as e:
        logger.debug(f"ELA calculation error: {e}")
        return 0.0


class ImageDetector(FraudDetector):
    @property
    def module_name(self) -> str:
        return "image_fraud"

    @property
    def model_version(self) -> str:
        return "image-ela-metadata-v1"

    async def analyze(self, **kwargs) -> DetectorResult:
        start_t = time.time()
        file_bytes = kwargs.get("file_bytes")

        if not file_bytes:
            return self._create_result(0.0, 1.0, [], 0.0, error="No image bytes provided")

        score = 0.0
        signals = []
        metadata = {}
        extracted_text = ""
        extracted_qrs = []

        try:
            image = Image.open(io.BytesIO(file_bytes))
            metadata["format"] = image.format
            metadata["size"] = f"{image.width}x{image.height}"
            metadata["mode"] = image.mode

            # 1. EXIF Metadata inspection
            exif_data = image.getexif()
            if exif_data:
                exif_dict = {}
                for tag_id, value in exif_data.items():
                    tag_str = str(tag_id)
                    val_str = str(value)
                    exif_dict[tag_str] = val_str
                    val_lower = val_str.lower()
                    for sw in KNOWN_EDITING_SOFTWARE:
                        if sw in val_lower:
                            score += 0.35
                            signals.append(f"Image metadata indicates editing/generation software: '{sw}'")
                metadata["exif"] = exif_dict
            else:
                signals.append("Image EXIF metadata is completely stripped")

            # 2. Error Level Analysis (ELA)
            ela_score = perform_ela(image)
            metadata["ela_anomaly_score"] = round(ela_score, 3)
            if ela_score > 0.6:
                score += 0.35
                signals.append("High Error Level Analysis (ELA) divergence indicating localized pixel tampering")
            elif ela_score > 0.4:
                score += 0.15
                signals.append("Moderate compression inconsistencies detected across image regions")

            # 3. OCR Text Extraction & Fraud Content Evaluation
            ocr_text = extract_text_with_ocr(file_bytes)
            if ocr_text:
                extracted_text = ocr_text
                t_lower = ocr_text.lower()
                signals.append(f"Text overlay detected via OCR ({len(ocr_text)} characters)")

                # Analyze OCR text for scam/phishing signatures
                has_urgency = any(w in t_lower for w in ['urgent', 'immediately', 'within 24 hours', 'blocked today', 'expired', 'warning'])
                has_credentials = any(w in t_lower for w in ['otp', 'password', 'pin', 'pan', 'aadhaar', 'cvv', 'verify now'])
                has_threat = any(w in t_lower for w in ['blocked', 'suspended', 'deactivated', 'legal action', 'police', 'arrest'])
                has_lottery = any(w in t_lower for w in ['congratulations', 'winner', 'won', 'lottery', 'free iphone', '50,000', '₹', 'prize'])
                has_payment = any(w in t_lower for w in ['pay now', 'processing fee', 'shipping fee', 'customs fee', 'upi', 'wire transfer'])

                if (has_urgency or has_threat) and has_credentials:
                    score = max(score, 0.80)
                    signals.append("Image contains urgent account suspension warning demanding OTP/credentials")
                elif 'kyc' in t_lower and ('pan' in t_lower or 'aadhaar' in t_lower or 'otp' in t_lower or has_threat):
                    score = max(score, 0.78)
                    signals.append("Image contains fake KYC verification alert demanding identity credentials")
                elif has_lottery and (has_payment or 'click' in t_lower or 'claim' in t_lower):
                    score = max(score, 0.72)
                    signals.append("Image contains fake prize/lottery notification with payment or claim instructions")
                elif any(p in t_lower for p in ['payment successful', 'transaction successful', 'paid to', 'upi ref', 'google pay', 'phonepe', 'paytm']):
                    score = max(score, 0.40)
                    signals.append("Image appears to be a digital payment receipt or transaction screenshot")

            # 4. Embedded QR code extraction
            qr_results = extract_qr_from_bytes(file_bytes)
            if qr_results:
                extracted_qrs = [qr[0] for qr in qr_results]
                signals.append(f"Found {len(extracted_qrs)} embedded QR code(s) inside image")
                for q_text in extracted_qrs:
                    if any(k in q_text.lower() for k in ['login', 'verify', 'account', 'pay', 'upi://', '.xyz', '.top']):
                        score = max(score, 0.65)
                        signals.append("Embedded QR code points to authentication or financial payload")

        except Exception as e:
            logger.error(f"Image analysis error: {e}", exc_info=True)
            return self._create_result(0.0, 0.5, [], (time.time() - start_t) * 1000, error=str(e))

        if not signals:
            score = 0.05
            signals.append("Clean visual structure, uniform compression, and no fraudulent text overlays detected")

        final_score = min(1.0, max(0.0, score))
        proc_time = (time.time() - start_t) * 1000
        confidence = 0.90 if len(signals) >= 2 else (0.85 if score > 0.1 else 0.92)

        return self._create_result(
            probability=final_score,
            confidence=confidence,
            signals=signals,
            processing_time_ms=proc_time,
            metadata={
                "extracted_text": extracted_text,
                "extracted_qrs": extracted_qrs,
                "image_metadata": metadata,
            }
        )
