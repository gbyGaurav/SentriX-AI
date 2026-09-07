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
            score += 0.35
            signals.append("IP address used as destination instead of domain name")
        if features.has_suspicious_tld:
            score += 0.20
            signals.append("High-risk Top Level Domain (.xyz, .top, .live, etc.)")
        if features.typosquatting_brand:
            score += 0.40
            signals.append(f"Lookalike / typosquatting domain imitating {features.typosquatting_brand.upper()}")
        elif features.brand_impersonation_score > 0:
            score += 0.30
            signals.append("Potential brand impersonation in URL structure")
        if features.has_suspicious_path:
            score += 0.20
            signals.append("Authentication / account-verification path pattern detected")
        if features.has_urgency_parameter:
            score += 0.25
            signals.append("Urgency or account-suspension parameter in query string")
        if features.is_free_hosting:
            score += 0.25
            signals.append("Hosted on ephemeral dynamic hosting service frequently abused for attacks")
        if features.suspicious_keyword_count > 0:
            kw_score = min(0.30, 0.08 * features.suspicious_keyword_count)
            score += kw_score
            signals.append(f"Contains {features.suspicious_keyword_count} sensitive/phishing keywords")
        if features.url_length > 75:
            score += 0.10
            signals.append("Abnormally long URL (> 75 characters)")
        if not features.is_https:
            score += 0.15
            signals.append("Not using HTTPS encryption")
        if features.domain_entropy > 4.0:
            score += 0.15
            signals.append("High domain entropy (randomly generated string)")
        if features.is_url_shortener:
            score += 0.15
            signals.append("Uses an obfuscating URL shortener")
        if features.has_at_symbol:
            score += 0.20
            signals.append("Contains '@' symbol redirect trick")
        if features.num_subdomains > 3:
            score += 0.15
            signals.append("Excessive subdomain depth (> 3 subdomains)")

        # Phishing combination floor
        if (features.has_suspicious_path or features.has_urgency_parameter) and (features.suspicious_keyword_count > 0 or features.has_suspicious_tld):
            score = max(score, 0.68)
            signals.append("Synergy pattern: Verification/login pattern paired with suspicious domain indicators")

        if not signals:
            score = 0.05
            signals.append("Legitimate domain structure, standard path, and no phishing indicators found")

        final_score = min(1.0, max(0.0, score))
        proc_time = (time.time() - start_t) * 1000
        confidence = 0.90 if len(signals) >= 2 else (0.85 if score > 0.1 else 0.92)

        return self._create_result(
            final_score,
            confidence,
            signals,
            proc_time,
            metadata={
                'url': url,
                'typosquatting_target': features.typosquatting_brand,
                'has_suspicious_path': features.has_suspicious_path,
                'has_urgency_parameter': features.has_urgency_parameter,
            }
        )
