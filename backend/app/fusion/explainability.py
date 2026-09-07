"""SentriX Explainability Engine.
Generates comprehensive, structured, professional cybersecurity intelligence reports
from multimodal detector outputs, relational evidence graphs, and threat classifications.
Works completely offline without requiring any external paid API keys.
"""

from typing import List, Dict, Any, Optional
from app.schemas.analysis import RiskLevel, FraudType, DetectorResult, EvidenceItem

MODULE_DISPLAY_NAMES = {
    'url_fraud': 'URL & Domain Analysis',
    'text_fraud': 'Social Engineering & NLP Analysis',
    'qr_fraud': 'QR Payload & Quishing Analysis',
    'document_fraud': 'Document Authenticity & Structure',
    'image_fraud': 'Visual Forensics & ELA Inspection',
    'video_fraud': 'Video Temporal Consistency Analysis',
    'audio_fraud': 'Acoustic & Transcription Analysis',
}

FRAUD_TYPE_DESCRIPTIONS = {
    FraudType.PHISHING: "Deceptive attempt to steal credentials, account access, or sensitive credentials via spoofed interfaces.",
    FraudType.SCAM: "Fraudulent scheme designed to solicit unauthorized payments, fake prizes, or bogus investments.",
    FraudType.SOCIAL_ENGINEERING: "Psychological manipulation exploiting urgency, fear, authority, or trust to compel user action.",
    FraudType.IDENTITY_THEFT: "Unlawful harvesting of personal identifiers (SSN, OTP, Passwords, banking numbers).",
    FraudType.FINANCIAL_FRAUD: "Direct fraudulent transaction demands, fake invoice billing, or wire transfer coercion.",
    FraudType.DEEPFAKE: "Synthetic media generation or digital manipulation mimicking authentic individuals.",
    FraudType.DOCUMENT_FRAUD: "Structural forgery, fabricated invoice headers, or manipulated document metadata.",
    FraudType.MALWARE: "Potential distribution of malicious executables, dangerous scripts, or exploit payloads.",
    FraudType.SPAM: "Unsolicited mass messaging promoting unverified third-party services.",
    FraudType.UNKNOWN: "Uncategorized anomaly requiring independent verification.",
}


class ExplainabilityEngine:
    """Generates structured, zero-hallucination cybersecurity intelligence reports."""

    def generate_explanation(
        self,
        risk_score: int,
        risk_level: RiskLevel,
        fraud_types: List[FraudType],
        detector_results: List[DetectorResult],
        evidence: List[EvidenceItem],
    ) -> str:
        """Produces a comprehensive multi-section threat intelligence summary."""
        if risk_score <= 20 and risk_level == RiskLevel.SAFE:
            return (
                "### Executive Threat Assessment: SAFE\n"
                "The SentriX multi-vector inspection pipeline analyzed all provided artifacts and found "
                "no malicious signatures, abnormal entropy patterns, credential harvesting hooks, or "
                "cross-modal inconsistencies. The analyzed content conforms to legitimate baseline profiles."
            )

        sections = []

        # 1. Executive Summary
        type_str = ", ".join(f.value.replace("_", " ") for f in fraud_types if f != FraudType.UNKNOWN) or "POTENTIAL THREAT"
        sections.append(
            f"### Executive Summary: {risk_level.value} RISK ({risk_score}/100)\n"
            f"SentriX threat intelligence engines classified this artifact under **{type_str}**. "
            f"The computed risk score of **{risk_score}/100** indicates strong indicators of hostile or deceptive intent."
        )

        # 2. Inferred Threat Methodology
        methodology_lines = []
        for ft in fraud_types:
            if ft in FRAUD_TYPE_DESCRIPTIONS and ft != FraudType.UNKNOWN:
                methodology_lines.append(f"- **{ft.value.replace('_', ' ')}**: {FRAUD_TYPE_DESCRIPTIONS[ft]}")
        if methodology_lines:
            sections.append(
                "### Inferred Attack Methodology\n" + "\n".join(methodology_lines)
            )

        # 3. Key Forensic Indicators
        forensic_lines = []
        for d in detector_results:
            d_name = MODULE_DISPLAY_NAMES.get(d.module, d.module)
            if d.signals:
                forensic_lines.append(f"**{d_name}** (Risk: {d.risk.value}, Probability: {d.fraud_probability:.0%}):")
                for s in d.signals[:4]:
                    forensic_lines.append(f"  - {s}")
        if forensic_lines:
            sections.append(
                "### Key Forensic Indicators\n" + "\n".join(forensic_lines)
            )

        # 4. Cross-Modal Correlation & Provenance
        if evidence:
            ev_lines = []
            for ev in evidence[:4]:
                if ev.relationship:
                    ev_lines.append(
                        f"  -> `{ev.source_modality}` {ev.relationship.replace('_', ' ')} `{ev.target_modality or 'payload'}`: *{ev.content[:80]}*"
                    )
            if ev_lines:
                sections.append(
                    "### Cross-Modal Correlation Trail\n"
                    "Automated cascading traced secondary threat vectors across modalities:\n"
                    + "\n".join(ev_lines)
                )

        # 5. Multi-Engine Agreement Assessment
        flagging_detectors = [d for d in detector_results if d.fraud_probability >= 0.4 and not d.error]
        if len(flagging_detectors) > 1:
            det_names = [MODULE_DISPLAY_NAMES.get(d.module, d.module) for d in flagging_detectors]
            sections.append(
                f"### Corroboration & Multi-Engine Agreement\n"
                f"{len(flagging_detectors)} independent specialized detection modules ({', '.join(det_names)}) "
                f"concurred on the high-risk classification. Cross-module agreement significantly lowers false positive probability."
            )

        return "\n\n".join(sections)

    def generate_recommendations(
        self,
        risk_level: RiskLevel,
        fraud_types: List[FraudType],
        signals: List[str],
    ) -> List[str]:
        recs = []

        if risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            recs.append("Do not click any embedded links, enter credentials, or open secondary attachments.")
            recs.append("Never share One-Time Passwords (OTPs), PINs, or account passwords under any circumstance.")

        if FraudType.PHISHING in fraud_types:
            recs.append("If this claims to originate from a known institution (e.g. bank, tech provider), navigate to their official website directly via a new browser window.")
            recs.append("Inspect sender domain records carefully — look for subtle character substitutions or unusual top-level domains.")

        if FraudType.FINANCIAL_FRAUD in fraud_types:
            recs.append("Halt all wire transfers, gift card purchases, and cryptocurrency payments immediately.")
            recs.append("Verify invoice routing and account numbers by contacting the vendor via an independently verified telephone number.")

        if FraudType.SOCIAL_ENGINEERING in fraud_types:
            recs.append("Resist artificial urgency: fraudulent actors manufacture time-sensitive panic to bypass rational verification.")

        if FraudType.DOCUMENT_FRAUD in fraud_types:
            recs.append("Request a cryptographically signed original or confirm document authenticity directly with the issuing department.")

        # Always include universal protective best practices
        recs.append("Report the fraudulent artifact to your security operations team or relevant consumer protection agency.")
        recs.append("Verify the sender's identity through an independent, pre-established communication channel.")

        # Deduplicate while preserving order
        seen = set()
        unique_recs = []
        for r in recs:
            if r not in seen:
                seen.add(r)
                unique_recs.append(r)

        return unique_recs
