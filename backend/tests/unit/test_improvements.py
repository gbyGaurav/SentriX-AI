import pytest
import io
import numpy as np
from PIL import Image, ImageDraw

from app.schemas.analysis import InputType, RiskLevel, FraudType
from app.detectors.spam.detector import SpamDetector
from app.detectors.text.detector import TextDetector
from app.detectors.url.detector import URLDetector
from app.detectors.qr.detector import QRDetector
from app.detectors.ai_media.detector import AIMediaDetector
from app.fusion.fusion_engine import FusionEngine
from app.fusion.risk_engine import RiskEngine
from app.fusion.explainability import ExplainabilityEngine
from app.router.modality_router import ModalityRouter


@pytest.mark.asyncio
async def test_safe_text_assessment():
    router = ModalityRouter()
    fusion = FusionEngine()
    risk_eng = RiskEngine()
    expl = ExplainabilityEngine()

    safe_text = 'Hi Sarah, are we still meeting for lunch at 12:30 PM tomorrow?'
    dets, ev, ext = await router.route_and_analyze(InputType.TEXT, text=safe_text)
    prob, conf = fusion.fuse(dets)
    score, level, ftypes, fconf = risk_eng.calculate_risk(prob, conf, dets, ev)

    assert score <= 19
    assert level == RiskLevel.SAFE
    assert ftypes == [FraudType.SAFE]
    assert FraudType.UNKNOWN not in ftypes

    summary = expl.generate_summary(score, level, ftypes, InputType.TEXT)
    assert 'SAFE' in summary.upper()

    why = expl.generate_why_suspicious(dets, ev, ftypes, level)
    assert len(why) > 0
    assert any('No phishing' in w or 'No requests' in w for w in why)


@pytest.mark.asyncio
async def test_spam_detector_categories():
    spam_det = SpamDetector()

    # KYC Scam
    kyc_res = await spam_det.analyze(text='Dear customer, your SBI account will be blocked today. Update KYC immediately or send OTP.')
    assert kyc_res.fraud_probability >= 0.70
    assert any('KYC' in s for s in kyc_res.signals)

    # Lottery Scam
    lottery_res = await spam_det.analyze(text='Congratulations! You have won Rs 50,000 in lucky draw. Click here to claim your prize.')
    assert lottery_res.fraud_probability >= 0.70
    assert any('lottery' in s.lower() or 'prize' in s.lower() for s in lottery_res.signals)

    # Job Scam
    job_res = await spam_det.analyze(text='Earn Rs 5000 daily with part time work from home. Like youtube videos on telegram. No experience needed.')
    assert job_res.fraud_probability >= 0.70
    assert any('job' in s.lower() for s in job_res.signals)

    # Delivery Scam
    deliv_res = await spam_det.analyze(text='Your IndiaPost parcel cannot be delivered. Pay shipping fee Rs 499 to reschedule.')
    assert deliv_res.fraud_probability >= 0.70
    assert any('delivery' in s.lower() or 'courier' in s.lower() for s in deliv_res.signals)


@pytest.mark.asyncio
async def test_url_detector_lookalike_and_params():
    url_det = URLDetector()

    # Lookalike with sensitive path and urgency
    res = await url_det.analyze(url='http://paypa1-security-verification.xyz/login/verify?action=urgent')
    assert res.fraud_probability >= 0.75
    assert any('lookalike' in s.lower() or 'typosquatting' in s.lower() for s in res.signals)
    assert any('login' in s.lower() or 'urgency' in s.lower() for s in res.signals)


@pytest.mark.asyncio
async def test_qr_detector_upi_trap():
    qr_det = QRDetector()

    # Rogue UPI debit request disguised as reward
    upi_payload = 'upi://pay?pa=scammer@okhdfcbank&pn=Cashback%20Reward&am=2500&cu=INR'
    res = await qr_det.analyze(qr_content=upi_payload)
    assert res.fraud_probability >= 0.75
    assert any('upi' in s.lower() or 'payment' in s.lower() for s in res.signals)



@pytest.mark.asyncio
async def test_ai_media_detector_probabilistic():
    ai_det = AIMediaDetector()

    # Create a simple solid image
    img = Image.new('RGB', (256, 256), color=(128, 128, 128))
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    raw_bytes = buf.getvalue()

    res = await ai_det.analyze(file_bytes=raw_bytes)
    ai_media = res.metadata.get('ai_media', {})

    # Verdict must strictly be one of 4 approved categories
    assert ai_media.get('result') in ('LIKELY_AI_GENERATED', 'POSSIBLY_AI_GENERATED', 'LIKELY_AUTHENTIC', 'INCONCLUSIVE')
    # Must have disclaimer
    assert 'disclaimer' in ai_media
    # Confidence must not be 100%
    assert ai_media.get('confidence', 0) <= 95
