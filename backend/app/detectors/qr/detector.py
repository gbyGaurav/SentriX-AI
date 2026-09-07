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
            score += 0.2
            signals.append(f"Multiple QR codes found ({len(decoded_items)}), potential quishing ambiguity")

        for payload, meta in decoded_items:
            extracted_payloads.append(payload)
            p_lower = payload.lower().strip()

            # Check if payload is a URL
            is_url = bool(re.match(r'^(https?://|www\.)', p_lower))
            if is_url:
                full_url = payload if payload.startswith("http") else f"https://{payload}"
                extracted_urls.append(full_url)
                signals.append(f"QR decodes to URL: {full_url[:60]}...")
            
            # Check for suspicious schemes
            if p_lower.startswith(("data:", "javascript:", "vbscript:", "file:")):
                score += 0.5
                signals.append(f"Dangerous URI scheme in QR: {p_lower[:15]}")
            
            # Check for payment requests (UPI, Crypto, etc.)
            if p_lower.startswith(("upi://", "bitcoin:", "ethereum:", "solana:")):
                score += 0.35
                signals.append("QR directs to immediate payment or cryptocurrency transfer")

            # Check for credential login endpoints
            if any(k in p_lower for k in ["login", "signin", "verify", "auth", "pwd", "password", "bank"]):
                score += 0.25
                signals.append("QR payload targets authentication / credential verification")

            # Obfuscated / IP address payload
            if re.search(r'https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', p_lower):
                score += 0.3
                signals.append("QR encodes an IP-based destination (high evasion risk)")

        final_score = min(1.0, max(0.0, score))
        proc_time = (time.time() - start_t) * 1000

        return self._create_result(
            probability=final_score,
            confidence=0.85,
            signals=signals,
            processing_time_ms=proc_time,
            metadata={
                "qr_detected": True,
                "decoded_count": len(decoded_items),
                "extracted_urls": extracted_urls,
                "payloads": extracted_payloads,
            },
        )
