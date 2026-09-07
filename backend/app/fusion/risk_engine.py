"""Risk scoring engine that converts fused detector outputs into a final risk assessment."""

from app.schemas.analysis import RiskLevel, FraudType, DetectorResult, EvidenceItem
from typing import List, Tuple


class RiskEngine:
    """Calculates final risk score from fused detector outputs, evidence, and cross-modal agreement."""

    THRESHOLDS = [
        (0, 19, RiskLevel.SAFE),
        (20, 39, RiskLevel.LOW),
        (40, 69, RiskLevel.MEDIUM),
        (70, 84, RiskLevel.HIGH),
        (85, 100, RiskLevel.CRITICAL),
    ]

    # Mapping from signal keywords to fraud types
    SIGNAL_FRAUD_MAP = {
        'phishing': FraudType.PHISHING,
        'suspicious url': FraudType.PHISHING,
        'brand impersonation': FraudType.PHISHING,
        'ip address': FraudType.PHISHING,
        'typosquatting': FraudType.PHISHING,
        'lookalike': FraudType.PHISHING,
        'credential': FraudType.IDENTITY_THEFT,
        'password': FraudType.IDENTITY_THEFT,
        'otp': FraudType.IDENTITY_THEFT,
        'kyc': FraudType.IDENTITY_THEFT,
        'pan': FraudType.IDENTITY_THEFT,
        'aadhaar': FraudType.IDENTITY_THEFT,
        'urgency': FraudType.SOCIAL_ENGINEERING,
        'threatening': FraudType.SOCIAL_ENGINEERING,
        'impersonation': FraudType.SOCIAL_ENGINEERING,
        'too good': FraudType.SCAM,
        'lottery': FraudType.SCAM,
        'winner': FraudType.SCAM,
        'prize': FraudType.SCAM,
        'job': FraudType.SCAM,
        'loan': FraudType.SCAM,
        'delivery': FraudType.SCAM,
        'courier': FraudType.SCAM,
        'parcel': FraudType.SCAM,
        'free money': FraudType.SCAM,
        'financial': FraudType.FINANCIAL_FRAUD,
        'wire transfer': FraudType.FINANCIAL_FRAUD,
        'upi': FraudType.FINANCIAL_FRAUD,
        'bitcoin': FraudType.FINANCIAL_FRAUD,
        'gift card': FraudType.FINANCIAL_FRAUD,
        'cryptocurrency': FraudType.FINANCIAL_FRAUD,
        'deepfake': FraudType.DEEPFAKE,
        'qr': FraudType.SUSPICIOUS_QR,
        'document': FraudType.DOCUMENT_FRAUD,
        'spam': FraudType.SPAM,
        'promotional': FraudType.SPAM,
        'malware': FraudType.MALWARE,
    }

    def calculate_risk(
        self,
        fused_probability: float,
        fused_confidence: float,
        detector_results: List[DetectorResult],
        evidence: List[EvidenceItem],
    ) -> Tuple[int, RiskLevel, List[FraudType], float]:
        """Calculate final risk score, level, fraud types, and confidence.
        
        Returns:
            (risk_score 0-100, risk_level, fraud_types, confidence)
        """
        # Base score from fused probability
        score = int(round(fused_probability * 100))

        # Bonus for multiple fraud detectors agreeing on high risk (excluding ai_media authenticity check)
        high_risk_detectors = [d for d in detector_results if d.module != 'ai_media' and d.fraud_probability > 0.55]
        if len(high_risk_detectors) > 1:
            agreement_bonus = min(15, len(high_risk_detectors) * 5)
            score = min(100, score + agreement_bonus)

        # Bonus for cross-modal evidence
        if evidence:
            cross_modal = [e for e in evidence if e.target_modality and e.target_modality != e.source_modality]
            if cross_modal:
                score = min(100, score + min(10, len(cross_modal) * 3))

        # Bonus for critical-severity evidence
        critical_evidence = [e for e in evidence if e.severity == 'critical']
        if critical_evidence:
            score = min(100, score + min(10, len(critical_evidence) * 5))

        # Determine risk level from thresholds
        level = RiskLevel.SAFE
        for min_val, max_val, risk_level in self.THRESHOLDS:
            if min_val <= score <= max_val:
                level = risk_level
                break

        # Determine fraud types
        if level == RiskLevel.SAFE or score <= 19:
            level = RiskLevel.SAFE
            fraud_types = [FraudType.SAFE]
        else:
            fraud_types = self._detect_fraud_types(detector_results)
            if not fraud_types:
                fraud_types = [FraudType.SCAM if score >= 40 else FraudType.SPAM]

        return score, level, fraud_types, fused_confidence

    def _detect_fraud_types(self, detector_results: List[DetectorResult]) -> List[FraudType]:
        """Infer fraud types from detector signals (excluding ai_media authenticity check)."""
        detected = set()

        for det in detector_results:
            if det.module == 'ai_media' or det.fraud_probability < 0.35:
                continue

            # Module-based type inference
            if det.module == 'url_fraud' and det.fraud_probability >= 0.45:
                detected.add(FraudType.PHISHING)

            if det.module == 'text_fraud' and det.fraud_probability >= 0.45:
                detected.add(FraudType.SCAM)

            if det.module == 'spam_fraud' and det.fraud_probability >= 0.35:
                detected.add(FraudType.SPAM)

            if det.module == 'qr_fraud' and det.fraud_probability >= 0.40:
                detected.add(FraudType.SUSPICIOUS_QR)

            if det.module == 'document_fraud' and det.fraud_probability >= 0.45:
                detected.add(FraudType.DOCUMENT_FRAUD)

            # Signal-based type inference
            all_signal_text = " ".join(det.signals).lower()
            for keyword, fraud_type in self.SIGNAL_FRAUD_MAP.items():
                if keyword in all_signal_text:
                    detected.add(fraud_type)

        return list(detected)

