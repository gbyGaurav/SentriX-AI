"""Text & NLP Fraud Detector Evaluation Script.
Evaluates precision, recall, F1, and confusion matrix on diverse text scams:
urgency, fake lottery, bank fraud, and benign interpersonal messages.
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
import numpy as np
from app.detectors.text.detector import TextDetector

BENCHMARK_TEXTS = [
    # Benign
    ("Hey, are we still meeting for lunch at 12:30 pm today?", 0),
    ("Please find attached the Q3 project update notes for our engineering sync.", 0),
    ("Happy birthday! Wishing you a fantastic year ahead full of happiness.", 0),
    ("Can you review this pull request whenever you have a free moment? Thanks!", 0),
    ("The library book you reserved is now ready for pickup at the front desk.", 0),
    ("Here is the recipe we talked about yesterday. Let me know if you try making it.", 0),
    ("Meeting notes: agreed to postpone sprint planning to Thursday morning.", 0),
    ("Your package has been delivered to your front porch by USPS.", 0),
    ("Doctor appointment confirmation for Dr. Miller on Friday at 3:00 PM.", 0),
    ("Your flight check-in is now open. Confirmation code: ABC123XYZ.", 0),
    # Fraudulent / Scam
    ("URGENT: Your bank account has been suspended! Click immediately to verify your identity.", 1),
    ("Congratulations! You have been selected as the winner of $1,000,000 lottery! Claim now.", 1),
    ("Action required within 24 hours: Unusual activity detected. Send your password and OTP.", 1),
    ("IRS Final Warning: A warrant has been issued for your arrest. Pay immediately via gift card.", 1),
    ("Guaranteed returns: Double your bitcoin in 48 hours with our automated trading system.", 1),
    ("From Apple Support: Your AppleID is disabled. Click the link below to enter your credentials.", 1),
    ("You have won a free gift card! Only 10 minutes left before this exclusive offer expires.", 1),
    ("Your Netflix subscription will be closed. Update payment method right now or face termination.", 1),
    ("Wire transfer notice: To release your unclaimed inheritance fund of $2.5M, pay the clearance fee.", 1),
    ("Security Alert: Unauthorized access from Russia. Click here to confirm your social security number.", 1),
]


async def evaluate_text_detector(threshold: float = 0.4):
    detector = TextDetector()
    y_true = []
    y_pred = []

    for text, label in BENCHMARK_TEXTS:
        res = await detector.analyze(text=text)
        prob = res.fraud_probability
        pred = 1 if prob >= threshold else 0
        y_true.append(label)
        y_pred.append(pred)

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
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0

    print("=" * 55)
    print("     UAMD — Text/NLP Fraud Detector Evaluation Report")
    print("=" * 55)
    print(f"Model Version:         {detector.model_version}")
    print(f"Total Test Samples:    {len(y_true)} (50% benign, 50% scam)")
    print(f"Decision Threshold:    {threshold}")
    print("-" * 55)
    print(f"Accuracy:              {accuracy:.4f}")
    print(f"Precision:             {precision:.4f}")
    print(f"Recall:                {recall:.4f}")
    print(f"F1-Score:              {f1:.4f}")
    print(f"False Positive Rate:   {fpr:.4f}")
    print(f"True Positives (TP):   {tp}")
    print(f"False Positives (FP):  {fp}")
    print(f"False Negatives (FN):  {fn}")
    print(f"True Negatives (TN):   {tn}")
    print("=" * 55)


if __name__ == "__main__":
    asyncio.run(evaluate_text_detector())
