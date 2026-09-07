import pytest
from app.detectors.url.detector import URLDetector
from app.schemas.analysis import RiskLevel


@pytest.mark.asyncio
async def test_safe_url():
    detector = URLDetector()
    res = await detector.analyze(url="https://www.google.com/search?q=cybersecurity")
    assert res.module == "url_fraud"
    assert res.fraud_probability < 0.3
    assert res.risk in (RiskLevel.SAFE, RiskLevel.LOW)


@pytest.mark.asyncio
async def test_phishing_url_ip_address():
    detector = URLDetector()
    res = await detector.analyze(url="http://192.168.1.1/paypal-login/update.html")
    assert res.fraud_probability > 0.4
    assert any("IP address" in s for s in res.signals)


@pytest.mark.asyncio
async def test_phishing_url_suspicious_tld_and_keywords():
    detector = URLDetector()
    res = await detector.analyze(url="http://secure-account-verify.xyz/login?user=admin")
    assert res.fraud_probability >= 0.4
    assert res.risk in (RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL)
