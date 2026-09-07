import time
from app.detectors.base import FraudDetector
from app.schemas.analysis import DetectorResult
from app.detectors.url.features import extract_url_features
import os

class URLDetector(FraudDetector):
    @property
    def module_name(self) -> str: return "url_fraud"
    
    @property
    def model_version(self) -> str: return "url-heuristic-v1"
    
    async def analyze(self, **kwargs) -> DetectorResult:
        start_t = time.time()
        url = kwargs.get('url', '')
        if not url:
            return self._create_result(0.0, 1.0, [], 0, error="No URL provided")
            
        features = extract_url_features(url)
        score = 0.0
        signals = []
        
        if features.has_ip_address:
            score += 0.3
            signals.append("IP address used instead of domain")
        if features.has_suspicious_tld:
            score += 0.15
            signals.append("Suspicious Top Level Domain")
        if features.brand_impersonation_score > 0:
            score += 0.25
            signals.append("Potential brand impersonation")
        if features.suspicious_keyword_count > 0:
            kw_score = min(0.25, 0.05 * features.suspicious_keyword_count)
            score += kw_score
            signals.append(f"Contains {features.suspicious_keyword_count} suspicious keywords")
        if features.url_length > 75:
            score += 0.1
            signals.append("Abnormally long URL")
        if not features.is_https:
            score += 0.1
            signals.append("Not using HTTPS")
        if features.domain_entropy > 4.0:
            score += 0.1
            signals.append("High domain entropy (likely randomly generated)")
        if features.is_url_shortener:
            score += 0.1
            signals.append("Uses a URL shortener")
        if features.has_at_symbol:
            score += 0.15
            signals.append("Contains @ symbol, common in phishing")
        if features.num_subdomains > 3:
            score += 0.1
            signals.append("Excessive number of subdomains")
            
        final_score = min(1.0, max(0.0, score))
        proc_time = (time.time() - start_t) * 1000
        
        return self._create_result(final_score, 0.8, signals, proc_time, metadata={'url': url})
