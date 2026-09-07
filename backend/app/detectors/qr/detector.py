"""QR Fraud Detector.
Analyzes QR codes detected in images for phishing URLs, rogue payment requests,
credential theft deep-links, and obfuscation.
"""

import time
import re
from typing import Optional, List
from app.detectors.base import FraudDetector
from app.schemas.analysis import DetectorResult
from app.extraction.qr import extract_qr_from_bytes


class QRDetector(FraudDetector):
    @property
    def module_name(self) -> str:
        return "qr_fraud"

    @property
    def model_version(self) -> str:
        return "qr-analyzer-v1"

    async def analyze(self, **kwargs) -> DetectorResult:
        start_t = time.time()
        file_bytes = kwargs.get("file_bytes")
        qr_content = kwargs.get("qr_content")

        decoded_items = []
        if file_bytes:
            decoded_items = extract_qr_from_bytes(file_bytes)
        elif qr_content:
            decoded_items = [(qr_content, {"engine": "direct"})]

        if not decoded_items:
            proc_time = (time.time() - start_t) * 1000
            return self._create_result(
                probability=0.0,
                confidence=0.5,
                signals=["No valid QR code could be decoded from this input."],
                processing_time_ms=proc_time,
                metadata={"qr_detected": False},
                error=None,
            )

        score = 0.0
        signals = []
        extracted_urls = []
        extracted_payloads = []

        # Multiple QRs in one image is often used in quishing or redirection tricks
        if len(decoded_items) > 1:
            score += 0.25
            signals.append(f"Multiple QR codes found ({len(decoded_items)}), potential quishing evasion attempt")

        for payload, meta in decoded_items:
            extracted_payloads.append(payload)
            p_lower = payload.lower().strip()

            # Check if payload is a URL
            is_url = bool(re.match(r'^(https?://|www\.)', p_lower))
            if is_url:
                full_url = payload if payload.startswith("http") else f"https://{payload}"
                extracted_urls.append(full_url)
                signals.append(f"QR decodes to web URL: {full_url[:60]}...")

                # Deep URL heuristic inline check
                try:
                    from app.detectors.url.features import extract_url_features
                    url_feat = extract_url_features(full_url)
                    if url_feat.has_suspicious_tld:
                        score = max(score + 0.35, 0.70)
                        signals.append("QR redirects to high-risk top-level domain (.xyz, .top, etc.)")
                    if url_feat.typosquatting_brand:
                        score = max(score + 0.45, 0.80)
                        signals.append(f"QR destination imitates trusted brand: {url_feat.typosquatting_brand.upper()}")
                    elif url_feat.brand_impersonation_score > 0:
                        score = max(score + 0.30, 0.65)
                        signals.append("QR destination displays brand impersonation indicators")
                    if url_feat.has_suspicious_path or url_feat.has_urgency_parameter:
                        score = max(score + 0.30, 0.72)
                        signals.append("QR destination points to sensitive login or account verification page")
                    if url_feat.is_url_shortener:
                        score += 0.20
                        signals.append("QR uses a URL shortener to hide destination website")
                except Exception as e:
                    pass

            # Check for suspicious schemes
            if p_lower.startswith(("data:", "javascript:", "vbscript:", "file:")):
                score = max(score + 0.50, 0.85)
                signals.append(f"Dangerous script/URI scheme in QR: {p_lower[:15]}")

            # Check for payment requests (UPI, Crypto, etc.)
            if p_lower.startswith("upi://pay"):
                score = max(score, 0.45)
                signals.append("QR encodes an immediate UPI payment request")
                if any(w in p_lower for w in ["cashback", "reward", "prize", "refund", "win", "gift"]):
                    score = max(score + 0.40, 0.88)
                    signals.append("Rogue payment trap: Disguising payment debit request as a cashback/reward claim")
            elif p_lower.startswith(("bitcoin:", "ethereum:", "solana:")):
                score = max(score + 0.35, 0.65)
                signals.append("QR directs to direct cryptocurrency transfer")

            # Check for credential login endpoints
            if any(k in p_lower for k in ["login", "signin", "verify", "auth", "pwd", "password", "bank"]):
                score = max(score + 0.30, 0.65)
                signals.append("QR payload targets authentication or credential verification")

            # Obfuscated / IP address payload
            if re.search(r'https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', p_lower):
                score = max(score + 0.35, 0.75)
                signals.append("QR encodes a direct numeric IP destination (evasion technique)")

        if not signals:
            score = 0.05
            signals.append(f"Clean QR code decoded successfully ({decoded_items[0][0][:40]}...)")

        final_score = min(1.0, max(0.0, score))
        proc_time = (time.time() - start_t) * 1000
        confidence = 0.90 if len(signals) >= 2 else (0.85 if score > 0.1 else 0.90)

        return self._create_result(
            probability=final_score,
            confidence=confidence,
            signals=signals,
            processing_time_ms=proc_time,
            metadata={
                "qr_detected": True,
                "decoded_count": len(decoded_items),
                "extracted_urls": extracted_urls,
                "payloads": extracted_payloads,
            },
        )
