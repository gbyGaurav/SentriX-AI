from urllib.parse import urlparse
import tldextract
import math
import re
from dataclasses import dataclass

SUSPICIOUS_TLDS = ['tk', 'ml', 'ga', 'cf', 'gq', 'xyz', 'top', 'club', 'work', 'buzz', 'live', 'online', 'site', 'cam', 'rest']
SUSPICIOUS_KEYWORDS = ['login', 'signin', 'verify', 'account', 'update', 'secure', 'banking', 'confirm', 'password', 'credential', 'suspended', 'unusual', 'limited', 'unlock', 'invoice', 'pay', 'kyc', 'otp', 'recovery', 'billing', 'auth']
BRAND_KEYWORDS = ['paypal', 'apple', 'google', 'microsoft', 'amazon', 'facebook', 'netflix', 'bank', 'chase', 'wells', 'sbi', 'hdfc', 'icici', 'axis', 'instagram', 'whatsapp']
URL_SHORTENERS = ['bit.ly', 'tinyurl.com', 'goo.gl', 't.co', 'ow.ly', 'is.gd', 'buff.ly', 'rebrand.ly']
FREE_HOSTING_DOMAINS = ['ngrok.io', 'duckdns.org', '000webhostapp.com', 'weebly.com', 'pages.dev', 'firebaseapp.com', 'glitch.me', 'repl.co']

TYPOSQUAT_MAP = {
    'paypa1': 'paypal', 'pay-pal': 'paypal', 'paypql': 'paypal',
    'arnazon': 'amazon', 'amazn': 'amazon', 'amzon': 'amazon',
    'goog1e': 'google', 'go0gle': 'google',
    'app1e': 'apple', 'apple-id': 'apple',
    'micros0ft': 'microsoft', 'netf1ix': 'netflix',
    'sbi-yono': 'sbi', 'sbi-kyc': 'sbi', 'sbionline-verify': 'sbi',
    'hdfc-kyc': 'hdfc', 'hdfc-netbanking': 'hdfc',
}

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
    has_suspicious_path: bool = False
    has_urgency_parameter: bool = False
    is_free_hosting: bool = False
    typosquatting_brand: str = ""

    def to_feature_vector(self) -> list[float]:
        return [self.url_length, self.domain_length, float(self.has_ip_address), float(self.has_suspicious_tld)]

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
    domain = ext.domain.lower()
    full_host = parsed.netloc.lower()
    path_lower = parsed.path.lower()
    query_lower = parsed.query.lower()

    is_ip = bool(re.match(r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$', domain)) or bool(re.match(r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$', full_host.split(':')[0]))

    suspicious_count = sum(1 for kw in SUSPICIOUS_KEYWORDS if kw in url.lower())

    # Brand impersonation & Typosquatting
    brand_score = 0.0
    typosquat_brand = ""
    for typo, target in TYPOSQUAT_MAP.items():
        if typo in domain or typo in full_host:
            brand_score = 0.85
            typosquat_brand = target
            break

    if not typosquat_brand:
        for brand in BRAND_KEYWORDS:
            if brand in url.lower() and brand != domain:
                brand_score = max(brand_score, 0.6)
                typosquat_brand = brand

    # Suspicious path indicators
    suspicious_paths = ['login', 'signin', 'verify', 'account', 'update', 'invoice', 'pay', 'auth', 'wp-admin', 'kyc', 'otp']
    has_susp_path = any(p in path_lower for p in suspicious_paths)

    # Urgency parameters
    urgency_params = ['verify=urgent', 'action=suspend', 'account=', 'otp=', 'token=', 'urgent', 'blocked']
    has_urgency = any(p in query_lower for p in urgency_params)

    # Free hosting check
    is_free = any(h in full_host for h in FREE_HOSTING_DOMAINS)

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
        has_suspicious_tld=ext.suffix.lower() in SUSPICIOUS_TLDS,
        has_suspicious_keywords=suspicious_count > 0,
        is_url_shortener=any(s in full_host for s in URL_SHORTENERS),
        has_double_slash_redirect='//' in parsed.path,
        has_at_symbol='@' in url,
        suspicious_keyword_count=suspicious_count,
        brand_impersonation_score=brand_score,
        has_suspicious_path=has_susp_path,
        has_urgency_parameter=has_urgency,
        is_free_hosting=is_free,
        typosquatting_brand=typosquat_brand,
    )
