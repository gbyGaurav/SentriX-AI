from urllib.parse import urlparse
import tldextract
import math
import re
from dataclasses import dataclass

SUSPICIOUS_TLDS = ['tk', 'ml', 'ga', 'cf', 'gq', 'xyz', 'top', 'club', 'work', 'buzz']
SUSPICIOUS_KEYWORDS = ['login', 'signin', 'verify', 'account', 'update', 'secure', 'banking', 'confirm', 'password', 'credential', 'suspended', 'unusual', 'limited', 'unlock']
BRAND_KEYWORDS = ['paypal', 'apple', 'google', 'microsoft', 'amazon', 'facebook', 'netflix', 'bank', 'chase', 'wells']
URL_SHORTENERS = ['bit.ly', 'tinyurl.com', 'goo.gl', 't.co', 'ow.ly']

@dataclass
class URLFeatures:
    url_length: int
    domain_length: int
    path_length: int
    query_length: int
    fragment_length: int
    num_dots: int
    num_hyphens: int
    num_underscores: int
    num_slashes: int
    num_question_marks: int
    num_equals: int
    num_ampersands: int
    num_at_symbols: int
    num_digits: int
    num_special_chars: int
    digit_ratio: float
    letter_ratio: float
    num_subdomains: int
    has_ip_address: bool
    is_https: bool
    has_port: bool
    domain_entropy: float
    path_entropy: float
    has_suspicious_tld: bool
    has_suspicious_keywords: bool
    is_url_shortener: bool
    has_double_slash_redirect: bool
    has_at_symbol: bool
    suspicious_keyword_count: int
    brand_impersonation_score: float
    
    def to_feature_vector(self) -> list[float]:
        return [self.url_length, self.domain_length, self.has_ip_address, self.has_suspicious_tld]

def shannon_entropy(data: str) -> float:
    if not data: return 0.0
    entropy = 0.0
    for x in set(data):
        p_x = float(data.count(x)) / len(data)
        entropy -= p_x * math.log(p_x, 2)
    return entropy

def extract_url_features(url: str) -> URLFeatures:
    parsed = urlparse(url)
    ext = tldextract.extract(url)
    domain = ext.domain
    
    is_ip = re.match(r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$', domain) is not None
    
    suspicious_count = sum(1 for kw in SUSPICIOUS_KEYWORDS if kw in url.lower())
    brand_score = 0.0
    for brand in BRAND_KEYWORDS:
        if brand in url.lower() and brand not in domain:
            brand_score += 0.5
            
    return URLFeatures(
        url_length=len(url),
        domain_length=len(parsed.netloc),
        path_length=len(parsed.path),
        query_length=len(parsed.query),
        fragment_length=len(parsed.fragment),
        num_dots=url.count('.'),
        num_hyphens=url.count('-'),
        num_underscores=url.count('_'),
        num_slashes=url.count('/'),
        num_question_marks=url.count('?'),
        num_equals=url.count('='),
        num_ampersands=url.count('&'),
        num_at_symbols=url.count('@'),
        num_digits=sum(c.isdigit() for c in url),
        num_special_chars=sum(not c.isalnum() for c in url),
        digit_ratio=sum(c.isdigit() for c in url) / max(1, len(url)),
        letter_ratio=sum(c.isalpha() for c in url) / max(1, len(url)),
        num_subdomains=len(ext.subdomain.split('.')) if ext.subdomain else 0,
        has_ip_address=is_ip,
        is_https=parsed.scheme == 'https',
        has_port=parsed.port is not None,
        domain_entropy=shannon_entropy(parsed.netloc),
        path_entropy=shannon_entropy(parsed.path),
        has_suspicious_tld=ext.suffix in SUSPICIOUS_TLDS,
        has_suspicious_keywords=suspicious_count > 0,
        is_url_shortener=parsed.netloc in URL_SHORTENERS,
        has_double_slash_redirect='//' in parsed.path,
        has_at_symbol='@' in url,
        suspicious_keyword_count=suspicious_count,
        brand_impersonation_score=min(1.0, brand_score)
    )
