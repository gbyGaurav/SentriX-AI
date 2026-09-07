"""Image Fraud & Authenticity Detector Evaluation Script.
Tests Error Level Analysis (ELA), EXIF stripping, and editing software detection.
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
import io
import numpy as np
from PIL import Image
from app.detectors.image.detector import ImageDetector


def create_synthetic_image(tampered: bool = False) -> bytes:
    """Generates synthetic textured image bytes (consistent compression vs spliced inconsistent compression)."""
    # Create textured noise image
    np.random.seed(42)
    base_arr = np.random.randint(50, 220, (300, 300, 3), dtype=np.uint8)
    img = Image.fromarray(base_arr)
    
    if tampered:
        # Create an independently heavily compressed noisy block
        spliced_arr = np.random.randint(10, 250, (120, 120, 3), dtype=np.uint8)
        tampered_block = Image.fromarray(spliced_arr)
        buf = io.BytesIO()
        tampered_block.save(buf, "JPEG", quality=20)
        buf.seek(0)
        resaved_block = Image.open(buf)
        img.paste(resaved_block, (80, 80))

    buf = io.BytesIO()
    if tampered:
        # Include EXIF tag for editing software (e.g. Photoshop / Canva signature)
        exif = img.getexif()
        exif[305] = "Adobe Photoshop 2024 (Windows)"  # Tag 305 = Software
        img.save(buf, "JPEG", quality=85, exif=exif)
    else:
        img.save(buf, "JPEG", quality=95)
    return buf.getvalue()


async def evaluate_image_detector():
    detector = ImageDetector()
    y_true = []
    y_pred = []

    # 10 clean samples
    for _ in range(10):
        b = create_synthetic_image(tampered=False)
        res = await detector.analyze(file_bytes=b)
        y_true.append(0)
        y_pred.append(1 if res.fraud_probability >= 0.3 else 0)

    # 10 tampered samples
    for _ in range(10):
        b = create_synthetic_image(tampered=True)
        res = await detector.analyze(file_bytes=b)
        y_true.append(1)
        y_pred.append(1 if res.fraud_probability >= 0.3 else 0)

    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    tp = np.sum((y_true == 1) & (y_pred == 1))
    fp = np.sum((y_true == 0) & (y_pred == 1))
    fn = np.sum((y_true == 1) & (y_pred == 0))
    tn = np.sum((y_true == 0) & (y_pred == 0))

    accuracy = (tp + tn) / len(y_true)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    print("=" * 60)
    print("      UAMD — Image Authenticity & Fraud Evaluation Report")
    print("=" * 60)
    print(f"Model Version:         {detector.model_version}")
    print(f"Total Test Samples:    {len(y_true)} (50% clean, 50% tampered ELA)")
    print("-" * 60)
    print(f"Accuracy:              {accuracy:.4f}")
    print(f"Precision:             {precision:.4f}")
    print(f"Recall:                {recall:.4f}")
    print(f"F1-Score:              {f1:.4f}")
    print(f"True Positives (TP):   {tp}")
    print(f"False Positives (FP):  {fp}")
    print(f"False Negatives (FN):  {fn}")
    print(f"True Negatives (TN):   {tn}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(evaluate_image_detector())
