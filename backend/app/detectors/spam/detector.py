"""Dedicated Spam Fraud Detector.
Detects promotional spam, SMS spam, lottery/giveaway scams, job scams,
loan scams, fake delivery/courier messages, fake KYC, and crypto investment spam.
"""

import re
import time
from typing import Dict, Any, List, Optional
from app.detectors.base import FraudDetector
from app.schemas.analysis import DetectorResult, RiskLevel

# 1. Lottery, Giveaways & Fake Prizes
LOTTERY_GIVEAWAY_PATTERNS = [
    r'congratulations?\b', r'you(?:\'ve|\s+have)\s+won', r'selected\s+(?:as|for)\s+(?:the\s+)?winner',
    r'lucky\s+draw', r'free\s+iphone', r'won\s+(?:rs\.?|inr|₹|\$)\s*[\d,]+',
    r'claim\s+(?:your\s+)?(?:prize|reward|cashback|gift)', r'spin\s+(?:and|&)\s+win',
    r'reward\s+of\s+(?:rs\.?|inr|₹|\$)', r'lottery\s+(?:winner|ticket|number)',
    r'1st\s+prize', r'unclaimed\s+(?:funds|reward|prize)', r'exclusive\s+gift',
]

# 2. Fake Job & Task Scams
JOB_SCAM_PATTERNS = [
    r'part[- ]?time\s+(?:job|work)', r'work\s+from\s+home\s+(?:job|opportunity)?',
    r'earn\s+(?:rs\.?|inr|₹|\$)?\s*[\d,]+\s*(?:-|to)\s*(?:rs\.?|inr|₹|\$)?\s*[\d,]+\s*(?:daily|per\s+day)',
    r'daily\s+(?:payout|earning|salary|income)', r'telegram\s+(?:task|group|channel)',
    r'like\s+(?:youtube\s+)?videos?\s+(?:to\s+earn|and\s+get)', r'subscribe\s+(?:and\s+earn|channel)',
    r'data\s+entry\s+job', r'simple\s+(?:online\s+)?tasks', r'no\s+experience\s+(?:needed|required)',
    r'earn\s+money\s+(?:easily|fast|online)', r'guaranteed\s+(?:daily\s+)?income',
]

# 3. Loan & Credit Card Scams
LOAN_SCAM_PATTERNS = [
    r'pre[- ]?approved\s+loan', r'instant\s+loan\s+(?:approved|disbursal)',
    r'loan\s+of\s+(?:rs\.?|inr|₹)\s*[\d,]+', r'0%?\s*interest\s+(?:loan|rate)',
    r'no\s+cibil\s+(?:required|check)', r'pay\s+processing\s+fee\s+for\s+loan',
    r'sanction\s+letter', r'credit\s+card\s+limit\s+increase',
    r'loan\s+disbursement\s+pending',
]

# 4. Fake Delivery & Courier Notices
FAKE_DELIVERY_PATTERNS = [
    r'parcel\s+(?:on\s+hold|delayed|stuck|cannot\s+be\s+delivered)',
    r'package\s+(?:held|pending|delayed|undelivered)',
    r'pay\s+(?:customs?|shipping|delivery|handling)\s+fee',
    r'(?:shipping|courier)\s+fee\s+(?:rs\.?|inr|₹|\$)\s*[\d,]+',
    r'reschedule\s+(?:your\s+)?delivery', r'update\s+(?:your\s+)?delivery\s+address',
    r'indiapost\s+alert', r'fedex\s+package', r'dhl\s+shipment', r'warehouse\s+holding',
]

# 5. Fake KYC & Banking Alerts
FAKE_KYC_BANKING_PATTERNS = [
    r'kyc\s+(?:has\s+)?expired', r'update\s+(?:your\s+)?kyc\s+(?:immediately|now|urgently)',
    r'(?:bank\s+account|account)\s+will\s+be\s+(?:blocked|suspended|deactivated|frozen)',
    r'(?:blocked|suspended)\s+today', r'send\s+(?:your\s+)?(?:pan|aadhaar|otp)',
    r'link\s+pan\s+(?:with\s+)?aadhaar', r'debit\s+card\s+(?:blocked|expired)',
    r'yono\s+(?:account|app)\s+(?:blocked|suspended)', r'verify\s+(?:your\s+)?otp\s+now',
    r'netbanking\s+(?:disabled|blocked)', r'unauthorized\s+login\s+attempt',
]

# 6. Cryptocurrency & Investment Scams
CRYPTO_INVESTMENT_PATTERNS = [
    r'guaranteed\s+(?:returns|profit)', r'double\s+your\s+(?:money|crypto|bitcoin|investment)',
    r'(?:100%|200%|500%)\s+(?:profit|returns)', r'vip\s+(?:trading|crypto|forex)\s+group',
    r'binary\s+trading', r'mining\s+pool\s+investment', r'send\s+crypto\s+to\s+receive',
    r'zero\s+risk\s+investment',
]

# 7. Promotional / Mass Marketing Spam
PROMOTIONAL_SPAM_PATTERNS = [
    r'flat\s+\d+%\s+off', r'limited\s+time\s+offer', r'hurry\s+up\b', r'flash\s+sale',
    r'use\s+promo\s+code', r'grab\s+(?:it\s+)?now', r'offer\s+valid\s+till',
    r'buy\s+1\s+get\s+1', r'click\s+here\s+to\s+avail', r'exclusive\s+discount',
    r'special\s+discount', r'reply\s+stop\s+to\s+opt\s*out',
]


class SpamDetector(FraudDetector):
    """Detects and categorizes unsolicited spam, scam text, and social engineering messages."""

    @property
    def module_name(self) -> str:
        return "spam_fraud"

    @property
    def model_version(self) -> str:
        return "spam-classifier-v2"

    async def analyze(self, **kwargs) -> DetectorResult:
        start_t = time.time()
        text = kwargs.get("text", "")

        if not text or len(text.strip()) < 5:
            return self._create_result(0.0, 0.9, ["No text content to analyze for spam"], 0.0)

        t_lower = text.lower().strip()
        matched_categories = []
        signals = []
        category_weights = {}

        def check_patterns(category_name: str, patterns: list, weight: float, label: str):
            count = 0
            for pat in patterns:
                if re.search(pat, t_lower, re.IGNORECASE):
                    count += 1
            if count > 0:
                category_weights[category_name] = weight * min(count, 3)
                matched_categories.append(category_name)
                signals.append(f"{label} ({count} pattern match{'es' if count > 1 else ''})")

        check_patterns("FAKE_KYC_BANKING", FAKE_KYC_BANKING_PATTERNS, 0.45, "Fake KYC or banking urgency alert")
        check_patterns("LOTTERY_GIVEAWAY", LOTTERY_GIVEAWAY_PATTERNS, 0.40, "Fake prize, reward, or lottery claim")
        check_patterns("JOB_SCAM", JOB_SCAM_PATTERNS, 0.35, "Deceptive high-earning task or job offer")
        check_patterns("LOAN_SCAM", LOAN_SCAM_PATTERNS, 0.35, "Unsolicited loan or pre-approval claim")
        check_patterns("FAKE_DELIVERY", FAKE_DELIVERY_PATTERNS, 0.35, "Suspicious parcel delivery / customs fee demand")
        check_patterns("CRYPTO_INVESTMENT", CRYPTO_INVESTMENT_PATTERNS, 0.40, "Unrealistic high-yield investment / crypto promise")
        check_patterns("PROMOTIONAL_SPAM", PROMOTIONAL_SPAM_PATTERNS, 0.20, "Unsolicited promotional / marketing messaging")

        # Artificial urgency amplifiers
        has_urgency = any(w in t_lower for w in ["urgent", "immediately", "within 24 hours", "today", "now", "hurry", "expire"])
        has_payment_or_fee = any(w in t_lower for w in ["pay", "fee", "₹", "rs.", "inr", "$", "transfer", "shipping"])
        has_credentials = any(w in t_lower for w in ["otp", "pin", "password", "pan", "aadhaar", "cvv"])

        base_score = sum(category_weights.values())

        if has_credentials and ("FAKE_KYC_BANKING" in matched_categories or "LOTTERY_GIVEAWAY" in matched_categories):
            base_score += 0.25
            signals.append("Explicit request for OTP, PIN, or sensitive government credentials")

        if has_urgency and has_payment_or_fee:
            base_score += 0.15
            signals.append("Artificial urgency combined with fee/payment request")

        # Cap and normalize score
        final_probability = min(1.0, max(0.0, base_score))

        # Determine primary spam category
        primary_category = matched_categories[0] if matched_categories else "NONE"
        if final_probability < 0.15:
            final_probability = 0.05
            signals = ["No significant spam or unsolicited promotional patterns detected"]

        confidence = 0.88 if len(matched_categories) >= 2 else (0.80 if matched_categories else 0.85)
        proc_time = (time.time() - start_t) * 1000

        return self._create_result(
            probability=final_probability,
            confidence=confidence,
            signals=signals,
            processing_time_ms=proc_time,
            metadata={
                "is_spam": final_probability >= 0.35,
                "spam_categories": matched_categories,
                "primary_category": primary_category,
            }
        )
