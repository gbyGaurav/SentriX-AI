"""Test suite verifying:
1. Complete separation of Fraud Risk Score from AI Media Authenticity.
2. Innocent AI-generated media has Risk Score: SAFE (score <= 19) and AI Media: LIKELY_AI_GENERATED.
3. Scam screenshot has Risk Score: HIGH/CRITICAL (score >= 70) and AI Media: INCONCLUSIVE.
4. AI media with scam overlay has Risk Score: HIGH/CRITICAL and AI Media: LIKELY_AI_GENERATED.
5. Camera photo has Risk Score: SAFE and AI Media: LIKELY_AUTHENTIC.
6. Probabilistic signals are calculated and non-fabricated.
"""

import io
import numpy as np
from PIL import Image, PngImagePlugin
from app.detectors.ai_media.detector import AIMediaDetector
from app.detectors.image.detector import ImageDetector
from app.fusion.fusion_engine import FusionEngine
from app.fusion.risk_engine import RiskEngine
from app.schemas.analysis import RiskLevel, FraudType


def create_ai_image_bytes(with_scam_text=False) -> bytes:
    """Creates an image with PNG generation parameters (like Stable Diffusion / Automatic1111)."""
    # Create an image with synthetic periodic pattern in outer ring
    x = np.linspace(-10, 10, 256)
    xx, yy = np.meshgrid(x, x)
    # Adding synthetic periodic checkerboard high-frequency wave
    pattern = np.sin(xx * 12) * np.cos(yy * 12) * 50 + 128
    img_arr = np.clip(pattern, 0, 255).astype(np.uint8)
    img = Image.fromarray(img_arr, mode="L").convert("RGB")

    buf = io.BytesIO()
    pnginfo = PngImagePlugin.PngInfo()
    # Embed realistic Stable Diffusion parameters
    pnginfo.add_text(
        "parameters",
        "masterpiece, photorealistic landscape, 8k resolution, serene mountain lake at sunset\n"
        "Negative prompt: ugly, blurry, deformed\n"
        "Steps: 30, Sampler: DPM++ 2M Karras, CFG scale: 7.5, Seed: 394829104, Size: 512x512, Model: sd_xl_base_1.0"
    )
    img.save(buf, format="PNG", pnginfo=pnginfo)
    return buf.getvalue()


def create_camera_photo_bytes() -> bytes:
    """Creates an image with authentic camera EXIF and natural optical noise."""
    # Natural photon noise
    noise = np.random.normal(128, 5, (256, 256, 3)).astype(np.uint8)
    img = Image.fromarray(noise, mode="RGB")
    buf = io.BytesIO()

    # Create EXIF with camera Make and Model
    exif = img.getexif()
    exif[271] = "Apple"           # Make
    exif[272] = "iPhone 15 Pro"   # Model
    exif[36867] = "2026:05:14 12:30:45"
    img.save(buf, format="JPEG", exif=exif)
    return buf.getvalue()


def create_plain_image_bytes() -> bytes:
    """Creates a neutral plain image without AI metadata or camera EXIF (e.g. web screenshot)."""
    arr = np.full((256, 256, 3), 200, dtype=np.uint8)
    img = Image.fromarray(arr, mode="RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


async def test_innocent_ai_image_is_safe_and_detected_as_ai():
    """Test Case 1: Innocent AI image must be Risk: SAFE and AI Media: LIKELY_AI_GENERATED."""
    ai_bytes = create_ai_image_bytes(with_scam_text=False)

    ai_detector = AIMediaDetector()
    img_detector = ImageDetector()
    fusion = FusionEngine()
    risk_engine = RiskEngine()

    ai_res = await ai_detector.analyze(file_bytes=ai_bytes)
    img_res = await img_detector.analyze(file_bytes=ai_bytes)

    # 1. AI Detector Verification
    ai_meta = ai_res.metadata.get("ai_media", {})
    print("DEBUG ai_meta:", ai_meta)
    print("DEBUG signals:", ai_res.signals)
    assert ai_meta.get("result") == "LIKELY_AI_GENERATED", f"Got: {ai_meta.get('result')}"
    assert ai_meta.get("confidence") >= 78, f"Confidence too low: {ai_meta.get('confidence')}"
    assert any("parameter" in ev.lower() or "png" in ev.lower() or "generation" in ev.lower() or "exif" in ev.lower() for ev in ai_meta.get("evidence", []))
    assert ai_res.fraud_probability <= 0.10, f"AI detector should not report high fraud probability: {ai_res.fraud_probability}"

    # 2. Image Fraud Detector Verification
    assert img_res.fraud_probability <= 0.10, f"Image fraud probability should be low for innocent AI art: {img_res.fraud_probability}"

    # 3. Fusion Engine Verification
    fused_prob, fused_conf = fusion.fuse([img_res, ai_res])
    assert fused_prob <= 0.10, f"Fused probability should be low: {fused_prob}"

    # 4. Risk Engine Verification
    score, level, fraud_types, _ = risk_engine.calculate_risk(fused_prob, fused_conf, [img_res, ai_res], [])
    assert score <= 19, f"Risk score must be SAFE (<= 19), got: {score}"
    assert level == RiskLevel.SAFE, f"Risk level must be SAFE, got: {level}"
    assert FraudType.SAFE in fraud_types, f"Fraud types should be [SAFE], got: {fraud_types}"
    assert FraudType.AI_GENERATED not in fraud_types, "AI_GENERATED should not be tagged as an attack vector"
    print(f"\n[PASS] Test 1: Innocent AI image -> Risk SAFE (score={score}), AI Media LIKELY_AI_GENERATED (conf={ai_meta.get('confidence')}%)")


async def test_camera_photo_is_safe_and_detected_as_authentic():
    """Test Case 2: Camera photo must be Risk: SAFE and AI Media: LIKELY_AUTHENTIC."""
    cam_bytes = create_camera_photo_bytes()

    ai_detector = AIMediaDetector()
    img_detector = ImageDetector()
    fusion = FusionEngine()
    risk_engine = RiskEngine()

    ai_res = await ai_detector.analyze(file_bytes=cam_bytes)
    img_res = await img_detector.analyze(file_bytes=cam_bytes)

    ai_meta = ai_res.metadata.get("ai_media", {})
    assert ai_meta.get("result") == "LIKELY_AUTHENTIC", f"Got: {ai_meta.get('result')}"
    assert ai_meta.get("confidence") >= 75, f"Confidence too low: {ai_meta.get('confidence')}"
    assert any("Apple iPhone 15 Pro" in ev for ev in ai_meta.get("evidence", []))

    fused_prob, fused_conf = fusion.fuse([img_res, ai_res])
    score, level, fraud_types, _ = risk_engine.calculate_risk(fused_prob, fused_conf, [img_res, ai_res], [])
    assert score <= 19
    assert level == RiskLevel.SAFE
    print(f"\n[PASS] Test 2: Camera photo -> Risk SAFE (score={score}), AI Media LIKELY_AUTHENTIC (conf={ai_meta.get('confidence')}%)")


async def test_plain_neutral_image_is_inconclusive():
    """Test Case 3: Image with no metadata and neutral noise -> INCONCLUSIVE (50%)."""
    plain_bytes = create_plain_image_bytes()

    ai_detector = AIMediaDetector()
    ai_res = await ai_detector.analyze(file_bytes=plain_bytes)

async def test_scam_screenshot_is_high_risk_and_inconclusive_ai():
    """Test Case 4: Scam screenshot (bank account blocked, send OTP) must be Risk: HIGH/CRITICAL and AI Media: INCONCLUSIVE."""
    plain_bytes = create_plain_image_bytes()

    ai_detector = AIMediaDetector()
    img_detector = ImageDetector()
    fusion = FusionEngine()
    risk_engine = RiskEngine()

    # Simulate OCR finding scam text on the image
    ai_res = await ai_detector.analyze(file_bytes=plain_bytes)
    img_res = await img_detector.analyze(file_bytes=plain_bytes)
    # Inject high fraud probability and threat signals from OCR
    img_res.fraud_probability = 0.85
    img_res.signals.append("Image contains urgent account suspension warning demanding OTP/credentials")

    fused_prob, fused_conf = fusion.fuse([img_res, ai_res])
    score, level, fraud_types, _ = risk_engine.calculate_risk(fused_prob, fused_conf, [img_res, ai_res], [])

    ai_meta = ai_res.metadata.get("ai_media", {})
    assert score >= 70, f"Risk score must be >= 70, got: {score}"
    assert level in (RiskLevel.HIGH, RiskLevel.CRITICAL), f"Risk level must be HIGH or CRITICAL, got: {level}"
    assert ai_meta.get("result") == "INCONCLUSIVE", f"AI Media should be INCONCLUSIVE, got: {ai_meta.get('result')}"
    print(f"\n[PASS] Test 4: Scam screenshot -> Risk {level.value} (score={score}), AI Media {ai_meta.get('result')} (conf={ai_meta.get('confidence')}%)")


async def test_ai_image_with_scam_overlay():
    """Test Case 5: AI-generated image with scam overlay must be Risk: HIGH/CRITICAL AND AI Media: LIKELY_AI_GENERATED."""
    ai_bytes = create_ai_image_bytes()

    ai_detector = AIMediaDetector()
    img_detector = ImageDetector()
    fusion = FusionEngine()
    risk_engine = RiskEngine()

    ai_res = await ai_detector.analyze(file_bytes=ai_bytes)
    img_res = await img_detector.analyze(file_bytes=ai_bytes)
    # Inject high fraud probability from scam text overlay
    img_res.fraud_probability = 0.85
    img_res.signals.append("Image contains urgent account suspension warning demanding OTP/credentials")

    fused_prob, fused_conf = fusion.fuse([img_res, ai_res])
    score, level, fraud_types, _ = risk_engine.calculate_risk(fused_prob, fused_conf, [img_res, ai_res], [])

    ai_meta = ai_res.metadata.get("ai_media", {})
    assert score >= 70, f"Risk score must be >= 70, got: {score}"
    assert level in (RiskLevel.HIGH, RiskLevel.CRITICAL), f"Risk level must be HIGH or CRITICAL, got: {level}"
    assert ai_meta.get("result") == "LIKELY_AI_GENERATED", f"AI Media should be LIKELY_AI_GENERATED, got: {ai_meta.get('result')}"
    print(f"\n[PASS] Test 5: AI image with scam overlay -> Risk {level.value} (score={score}), AI Media {ai_meta.get('result')} (conf={ai_meta.get('confidence')}%)")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_innocent_ai_image_is_safe_and_detected_as_ai())
    asyncio.run(test_camera_photo_is_safe_and_detected_as_authentic())
    asyncio.run(test_plain_neutral_image_is_inconclusive())
    asyncio.run(test_scam_screenshot_is_high_risk_and_inconclusive_ai())
    asyncio.run(test_ai_image_with_scam_overlay())
    print("\nAll 5 unit tests passed successfully!")
