"""Video Fraud & Temporal Consistency Evaluation Script.
Evaluates frame sampling, temporal discontinuity metrics, and low-framerate loop detection.
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
import io
import tempfile
import numpy as np
import cv2
from app.detectors.video.detector import VideoDetector


def create_synthetic_video(anomaly: bool = False) -> bytes:
    """Generates synthetic test video bytes (smooth motion vs jump-cut flicker / low fps loop)."""
    tmp_path = os.path.join(tempfile.gettempdir(), f"eval_vid_{os.getpid()}_{np.random.randint(10000)}.mp4")
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    fps = 10.0 if anomaly else 25.0
    out = cv2.VideoWriter(tmp_path, fourcc, fps, (160, 120))

    for i in range(15):
        frame = np.ones((120, 160, 3), dtype=np.uint8) * (50 + i * 5)
        if anomaly and i > 8:
            # Flash / temporal discontinuity
            frame[:, :] = 250
        out.write(frame)
    out.release()

    with open(tmp_path, 'rb') as f:
        vid_bytes = f.read()

    try:
        os.remove(tmp_path)
    except Exception:
        pass

    return vid_bytes


async def evaluate_video_detector():
    detector = VideoDetector()
    y_true = []
    y_pred = []

    # 5 clean samples
    for _ in range(5):
        b = create_synthetic_video(anomaly=False)
        res = await detector.analyze(file_bytes=b)
        y_true.append(0)
        y_pred.append(1 if res.fraud_probability >= 0.15 else 0)

    # 5 anomaly samples
    for _ in range(5):
        b = create_synthetic_video(anomaly=True)
        res = await detector.analyze(file_bytes=b)
        y_true.append(1)
        y_pred.append(1 if res.fraud_probability >= 0.15 else 0)

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
    print("      UAMD — Video Fraud & Temporal Evaluation Report")
    print("=" * 60)
    print(f"Model Version:         {detector.model_version}")
    print(f"Total Test Samples:    {len(y_true)} (50% clean, 50% temporal anomaly)")
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
    asyncio.run(evaluate_video_detector())
