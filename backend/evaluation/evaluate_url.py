"""URL Fraud Detector Evaluation Script.
Measures Accuracy, Precision, Recall, F1-Score, False Positive Rate, and ROC-AUC
on a balanced benchmark of legitimate and phishing URLs.
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
import numpy as np
from app.detectors.url.detector import URLDetector

BENCHMARK_URLS = [
    # Legitimate
    ("https://www.google.com/search?q=cybersecurity", 0),
    ("https://github.com/torvalds/linux", 0),
    ("https://en.wikipedia.org/wiki/Phishing", 0),
    ("https://stackoverflow.com/questions/tagged/python", 0),
    ("https://www.nytimes.com/section/technology", 0),
    ("https://docs.python.org/3/library/urllib.parse.html", 0),
    ("https://www.microsoft.com/en-us/software-download", 0),
    ("https://aws.amazon.com/free/", 0),
    ("https://fastapi.tiangolo.com/tutorial/", 0),
    ("https://pypi.org/project/scikit-learn/", 0),
    # Phishing / Malicious
    ("http://192.168.1.100/secure-bank-login/update-info.html", 1),
    ("http://paypal-verification-center.xyz/signin?id=49812", 1),
    ("http://appleid-support-account-update.tk/verify", 1),
    ("http://chase-bank-unusual-activity-alert.top/auth", 1),
    ("http://login.microsoftonline.account-verify.gq/login.php", 1),
    ("http://wellsfargo-security-alert-card.club/verify-pin", 1),
    ("http://netflix-billing-update-subscription.xyz/reactivate", 1),
    ("http://amazon-prime-delivery-failed-claim.work/order", 1),
    ("http://secure-login-account-suspended.cf/unlock", 1),
    ("http://bit.ly/3xXQFakeBankLoginRedirector", 1),
]


async def evaluate_url_detector(threshold: float = 0.4):
    detector = URLDetector()
    y_true = []
    y_pred = []
    y_scores = []

    for url, label in BENCHMARK_URLS:
        res = await detector.analyze(url=url)
        prob = res.fraud_probability
        pred = 1 if prob >= threshold else 0
        y_true.append(label)
        y_pred.append(pred)
        y_scores.append(prob)

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
    print("      UAMD — URL Fraud Detector Evaluation Report")
    print("=" * 55)
    print(f"Model Version:         {detector.model_version}")
    print(f"Total Test Samples:    {len(y_true)} (50% benign, 50% phishing)")
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
    asyncio.run(evaluate_url_detector())
