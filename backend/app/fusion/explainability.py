"""Enhanced explainability engine that generates evidence-based explanations."""

from app.schemas.analysis import RiskLevel, FraudType, DetectorResult, EvidenceItem
from typing import List


MODULE_DISPLAY_NAMES = {
    'url_fraud': 'URL Analysis',
    'text_fraud': 'Text/NLP Analysis',
    'qr_fraud': 'QR Code Analysis',
    'document_fraud': 'Document Analysis',
    'image_fraud': 'Image Analysis',
    'video_fraud': 'Video Analysis',
    'audio_fraud': 'Audio Analysis',
}


class ExplainabilityEngine:
    """Generates human-readable explanations from actual detector outputs.
    
    Every explanation references real signals — no fabricated reasons.
    """

    def generate_explanation(
        self,
        risk_score: int,
        risk_level: RiskLevel,
        fraud_types: List[FraudType],
        detector_results: List[DetectorResult],
        evidence: List[EvidenceItem],
    ) -> str:
        if risk_score <= 20:
            return (
                "The analysis indicates a low likelihood of fraud. "
                "No significant suspicious patterns were detected across the analyzed content."
            )

        lines = []
        lines.append(
            f"This content has been assessed as {risk_level.value} risk "
            f"with a score of {risk_score}/100."
        )

        # Summarize which detectors flagged issues
        flagging_detectors = [
            d for d in detector_results
            if d.fraud_probability > 0.4 and not d.error
        ]
        if flagging_detectors:
            names = [MODULE_DISPLAY_NAMES.get(d.module, d.module) for d in flagging_detectors]
            if len(names) == 1:
                lines.append(f"\n{names[0]} identified suspicious indicators.")
            else:
                lines.append(
                    f"\n{len(names)} independent detectors flagged suspicious content: "
                    + ", ".join(names) + "."
                )

        # List key signals from all detectors
        all_signals = []
        for d in detector_results:
            for s in d.signals:
                all_signals.append(s)

        if all_signals:
            lines.append("\nKey indicators found:")
            for signal in all_signals[:8]:
                lines.append(f"  ✓ {signal}")
            remaining = len(all_signals) - 8
            if remaining > 0:
                lines.append(f"  ... and {remaining} additional signal(s).")

        # Cross-modal agreement note
        if len(flagging_detectors) > 1:
            lines.append(
                f"\n⚡ Multiple independent analysis modules agree on the risk assessment, "
                f"which increases confidence in this result."
            )

        # Evidence relationships
        if evidence:
            relationships = [e for e in evidence if e.relationship]
            if relationships:
                lines.append("\nCross-modal evidence chain detected:")
                for ev in relationships[:3]:
                    lines.append(
                        f"  → {ev.source_modality} {ev.relationship} {ev.target_modality or 'content'}"
                    )

        return "\n".join(lines)

    def generate_recommendations(
        self,
        risk_level: RiskLevel,
        fraud_types: List[FraudType],
        signals: List[str],
    ) -> List[str]:
        recs = []

        if risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            recs.append("Do not click any links or download attachments from this content.")
            recs.append("Do not provide personal information, passwords, or financial details.")

        if FraudType.PHISHING in fraud_types:
            recs.append("Do not click the URL or enter credentials on the linked page.")
            recs.append("If this appears to be from a known company, visit their official website directly instead.")

        if FraudType.SCAM in fraud_types or FraudType.SOCIAL_ENGINEERING in fraud_types:
            recs.append("Be skeptical of unsolicited messages requesting money or personal data.")
            recs.append("Do not send money via gift cards, wire transfers, or cryptocurrency to unknown parties.")

        if FraudType.FINANCIAL_FRAUD in fraud_types:
            recs.append("Do not make any payments or transfers based on this communication.")
            recs.append("Contact your bank directly using their official phone number if concerned.")

        if FraudType.DEEPFAKE in fraud_types:
            recs.append("Verify the identity of the person through an independent channel (e.g., phone call).")

        if FraudType.DOCUMENT_FRAUD in fraud_types:
            recs.append("Verify the document's authenticity with the issuing organization directly.")

        # Signal-specific recommendations
        signal_text = " ".join(signals).lower()
        if 'otp' in signal_text or 'password' in signal_text:
            recs.append("Never share OTPs, passwords, or PINs with anyone — legitimate organizations will never ask for these.")

        if 'urgency' in signal_text or 'urgent' in signal_text:
            recs.append("Take time to verify — legitimate organizations rarely pressure you with artificial urgency.")

        # Always include
        recs.append("Verify the sender's identity through an independent trusted channel.")
        recs.append("Report suspicious content to the relevant platform and local authorities if appropriate.")

        # Deduplicate while preserving order
        seen = set()
        unique_recs = []
        for r in recs:
            if r not in seen:
                seen.add(r)
                unique_recs.append(r)

        return unique_recs
