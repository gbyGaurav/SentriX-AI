import time
import re
from app.detectors.base import FraudDetector
from app.schemas.analysis import DetectorResult
from app.detectors.text.patterns import *

class TextDetector(FraudDetector):
    @property
    def module_name(self) -> str: return "text_fraud"
    
    @property
    def model_version(self) -> str: return "text-pattern-v1"
    
    async def analyze(self, **kwargs) -> DetectorResult:
        start_t = time.time()
        text = kwargs.get('text', '')
        if not text:
            return self._create_result(0.0, 1.0, [], 0, error="No text provided")
            
        t_lower = text.lower()
        score = 0.0
        signals = []
        
        extracted_urls = re.findall(URL_REGEX, text)
        emails = re.findall(EMAIL_REGEX, text)
        phones = re.findall(PHONE_REGEX, text)
        crypto = re.findall(CRYPTO_REGEX, text)
        
        has_urgency = False
        has_credentials = False
        has_threat = False
        has_too_good = False
        has_financial = False
        has_impersonation = False
        has_cta = False

        def match_patterns(patterns, weight, msg):
            nonlocal score
            matches = sum(1 for p in patterns if p in t_lower)
            if matches > 0:
                score += weight * min(matches, 3)
                signals.append(f"{msg} ({matches} match{'es' if matches > 1 else ''})")
                return True
            return False

        has_urgency = match_patterns(URGENCY_PATTERNS, 0.20, "Urgent or time-pressuring language")
        has_credentials = match_patterns(CREDENTIAL_PATTERNS, 0.25, "Requests passwords, OTP, PIN, PAN or Aadhaar")
        has_financial = match_patterns(FINANCIAL_PATTERNS, 0.20, "Mentions payments, prizes, fees, or funds")
        has_threat = match_patterns(THREAT_PATTERNS, 0.30, "Threatens account suspension, block, or legal penalties")
        has_too_good = match_patterns(TOO_GOOD_PATTERNS, 0.20, "Unrealistic prizes, free gifts, or guaranteed lottery")
        has_impersonation = match_patterns(IMPERSONATION_PATTERNS, 0.20, "Impersonates bank, security desk, or authority")
        has_cta = match_patterns(SUSPICIOUS_CTA_PATTERNS, 0.15, "Directs user to click link, call, or take action")

        if crypto:
            score += 0.35
            signals.append("Contains cryptocurrency addresses")

        # Multi-signal synergy boosts
        if has_threat and has_credentials:
            score = max(score + 0.30, 0.78)
            signals.append("Dangerous combination: Account threat combined with credential/OTP demand")
        elif has_urgency and has_credentials:
            score = max(score + 0.25, 0.72)
            signals.append("Dangerous combination: Artificial urgency coupled with credential/OTP harvesting")

        if has_too_good and (has_financial or has_cta):
            score = max(score + 0.25, 0.70)
            signals.append("Scam pattern: Lottery/gift claim paired with payment fee or immediate link")

        if ('kyc' in t_lower or 'pan' in t_lower or 'aadhaar' in t_lower) and (has_urgency or has_threat or has_credentials):
            score = max(score + 0.30, 0.75)
            signals.append("Targeted KYC verification or identity theft scam pattern")

        # Clean message handling
        if not signals:
            score = 0.05
            signals.append("No suspicious keywords, credential requests, or coercive patterns found")

        final_score = min(1.0, max(0.0, score))
        proc_time = (time.time() - start_t) * 1000

        meta = {
            'extracted_urls': extracted_urls,
            'extracted_emails': emails,
            'extracted_phones': phones,
            'has_urgency': has_urgency,
            'has_credentials': has_credentials,
            'has_financial': has_financial,
        }

        confidence = 0.90 if len(signals) >= 2 else (0.85 if score > 0.1 else 0.92)
        return self._create_result(final_score, confidence, signals, proc_time, metadata=meta)
