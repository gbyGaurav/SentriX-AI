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
        
        def match_patterns(patterns, weight, msg):
            nonlocal score
            matches = sum(1 for p in patterns if p in t_lower)
            if matches > 0:
                score += weight * min(matches, 3)
                signals.append(f"{msg} ({matches} matches)")
                
        match_patterns(URGENCY_PATTERNS, 0.15, "High urgency language")
        match_patterns(CREDENTIAL_PATTERNS, 0.2, "Requests sensitive credentials")
        match_patterns(FINANCIAL_PATTERNS, 0.15, "Mentions high-risk financial instruments")
        match_patterns(THREAT_PATTERNS, 0.25, "Contains threatening language")
        match_patterns(TOO_GOOD_PATTERNS, 0.15, "Too good to be true promises")
        match_patterns(IMPERSONATION_PATTERNS, 0.2, "Potential impersonation of authority/brand")
        match_patterns(SUSPICIOUS_CTA_PATTERNS, 0.1, "Suspicious call to action")
        
        if crypto:
            score += 0.3
            signals.append("Contains cryptocurrency addresses")
            
        final_score = min(1.0, max(0.0, score))
        proc_time = (time.time() - start_t) * 1000
        
        meta = {
            'extracted_urls': extracted_urls,
            'extracted_emails': emails,
            'extracted_phones': phones
        }
        
        return self._create_result(final_score, 0.8, signals, proc_time, metadata=meta)
