import pytest
from app.detectors.text.detector import TextDetector
from app.schemas.analysis import RiskLevel


@pytest.mark.asyncio
async def test_safe_text():
    detector = TextDetector()
    res = await detector.analyze(text="Hi Sarah, are you available for a quick sync at 2 PM?")
    assert res.fraud_probability <= 0.2
    assert res.risk == RiskLevel.SAFE


@pytest.mark.asyncio
async def test_scam_urgency_and_credentials():
    detector = TextDetector()
    scam_msg = (
        "URGENT: Your bank account will be suspended within 24 hours! "
        "Verify your password and OTP immediately to prevent legal action: http://bank-update.xyz"
    )
    res = await detector.analyze(text=scam_msg)
    assert res.fraud_probability >= 0.6
    assert res.risk in (RiskLevel.HIGH, RiskLevel.CRITICAL)
    assert len(res.metadata.get("extracted_urls", [])) > 0
