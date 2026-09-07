"""Risk scoring engine that converts fused detector outputs into a final risk assessment."""

from app.schemas.analysis import RiskLevel, FraudType, DetectorResult, EvidenceItem
from typing import List, Tuple


class RiskEngine:
    """Calculates final risk score from fused detector outputs, evidence, and cross-modal agreement."""

    THRESHOLDS = [
        (0, 20, RiskLevel.SAFE),
        (21, 40, RiskLevel.LOW),
        (41, 60, RiskLevel.MEDIUM),
        (61, 80, RiskLevel.HIGH),
        (81, 100, RiskLevel.CRITICAL),
    ]

    # Mapping from signal keywords to fraud types
    SIGNAL_FRAUD_MAP = {
        'phishing': FraudType.PHISHING,
        'suspicious url': FraudType.PHISHING,
        'brand impersonation': FraudType.PHISHING,
        'ip address': FraudType.PHISHING,
        'credential': FraudType.IDENTITY_THEFT,
        'password': FraudType.IDENTITY_THEFT,
        'otp': FraudType.IDENTITY_THEFT,
        'urgency': FraudType.SOCIAL_ENGINEERING,
        'threatening': FraudType.SOCIAL_ENGINEERING,
        'impersonation': FraudType.SOCIAL_ENGINEERING,
        'too good': FraudType.SCAM,
        'lottery': FraudType.SCAM,
        'winner': FraudType.SCAM,
        'prize': FraudType.SCAM,
        'free money': FraudType.SCAM,
        'financial': FraudType.FINANCIAL_FRAUD,
        'wire transfer': FraudType.FINANCIAL_FRAUD,
        'bitcoin': FraudType.FINANCIAL_FRAUD,
        'gift card': FraudType.FINANCIAL_FRAUD,
        'cryptocurrency': FraudType.FINANCIAL_FRAUD,
        'deepfake': FraudType.DEEPFAKE,
        'manipulation': FraudType.DEEPFAKE,
        'document': FraudType.DOCUMENT_FRAUD,
        'spam': FraudType.SPAM,
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
        score = int(fused_probability * 100)

        # Bonus for multiple detectors agreeing on high risk
        high_risk_detectors = [d for d in detector_results if d.fraud_probability > 0.6]
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

        # Determine fraud types from signals
        fraud_types = self._detect_fraud_types(detector_results)
        if not fraud_types:
            fraud_types = [FraudType.UNKNOWN]

        return score, level, fraud_types, fused_confidence

    def _detect_fraud_types(self, detector_results: List[DetectorResult]) -> List[FraudType]:
        """Infer fraud types from detector signals."""
        detected = set()

        for det in detector_results:
            if det.fraud_probability < 0.4:
                continue

            # Module-based type inference
            if det.module == 'url_fraud' and det.fraud_probability > 0.5:
                detected.add(FraudType.PHISHING)

            if det.module == 'text_fraud' and det.fraud_probability > 0.5:
                detected.add(FraudType.SCAM)

            # Signal-based type inference
            all_signal_text = " ".join(det.signals).lower()
            for keyword, fraud_type in self.SIGNAL_FRAUD_MAP.items():
                if keyword in all_signal_text:
                    detected.add(fraud_type)

        return list(detected)
