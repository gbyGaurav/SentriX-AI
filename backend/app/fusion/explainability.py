"""SentriX Plain-English Explainability Engine.
Generates clear, human-understandable fraud intelligence reports
from multimodal detector outputs and cross-modal evidence.
Eliminates robotic jargon in favor of actionable, practical guidance.
Works completely offline without requiring any external paid API keys.
"""

from typing import List, Dict, Any, Optional
from app.schemas.analysis import RiskLevel, FraudType, DetectorResult, EvidenceItem

MODULE_DISPLAY_NAMES = {
    'url_fraud': 'URL & Link Security',
    'text_fraud': 'Message & Social Engineering Analysis',
    'spam_fraud': 'Spam & Scam Classification',
    'qr_fraud': 'QR Code Inspection',
    'document_fraud': 'Document Authenticity',
    'image_fraud': 'Image Forensics & OCR',
    'ai_media': 'AI Media & Synthetic Generation Check',
    'video_fraud': 'Video Forensics',
    'audio_fraud': 'Audio Analysis',
}

FRAUD_TYPE_DESCRIPTIONS = {
    FraudType.PHISHING: "Deceptive link or spoofed page attempting to steal login credentials or personal data.",
    FraudType.SCAM: "Deceptive scheme designed to trick you into sending money, paying fake fees, or sharing info.",
    FraudType.SPAM: "Unsolicited marketing or mass spam message pushing unverified promotions.",
    FraudType.SOCIAL_ENGINEERING: "Psychological manipulation using urgency, fear, or false authority to rush your decisions.",
    FraudType.IDENTITY_THEFT: "Attempt to harvest confidential personal identifiers such as OTP, PAN, Aadhaar, or passwords.",
    FraudType.FINANCIAL_FRAUD: "Direct fraudulent transaction request, suspicious UPI transfer, or fake invoice demand.",
    FraudType.DEEPFAKE: "Digital media manipulated or generated to impersonate a real person.",
    FraudType.AI_GENERATED: "Synthetic image or video created using generative AI models.",
    FraudType.DOCUMENT_FRAUD: "Altered or forged document structure, mismatched metadata, or fake official certificate.",
    FraudType.SUSPICIOUS_QR: "QR code pointing to an untrusted payment trap or malicious destination.",
    FraudType.MALWARE: "Potential malicious file download or suspicious redirection.",
    FraudType.SAFE: "No malicious patterns or security threats detected.",
    FraudType.UNKNOWN: "Unusual content requiring careful manual review.",
}


class ExplainabilityEngine:
    """Generates plain-English, actionable fraud intelligence reports."""

    def generate_summary(
        self,
        risk_score: int,
        risk_level: RiskLevel,
        fraud_types: List[FraudType],
        input_type: Any,
    ) -> str:
        """Generates a concise 1-2 sentence executive assessment readable in 5 seconds."""
        if risk_level == RiskLevel.SAFE or risk_score <= 19:
            return (
                "🟢 SAFE / LOW CONCERN: SentriX analyzed this content and found no malicious links, "
                "credential requests, or scam indicators. The content appears benign."
            )

        active_types = [
            f.value.replace("_", " ").title()
            for f in fraud_types
            if f not in (FraudType.UNKNOWN, FraudType.SAFE)
        ]
        threat_str = ", ".join(active_types) if active_types else "Suspicious Activity"

        if risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL) or risk_score >= 70:
            return (
                f"🚨 HIGH RISK ({risk_score}/100): High likelihood of {threat_str.lower()}. "
                f"Immediate caution is required. Do not click links, make payments, or share sensitive information."
            )
        elif risk_level == RiskLevel.MEDIUM or risk_score >= 40:
            return (
                f"⚠️ SUSPICIOUS CONTENT ({risk_score}/100): Moderate risk of {threat_str.lower()}. "
                f"Contains warning signs commonly associated with unsolicited spam or fraudulent schemes."
            )
        else:
            return (
                f"🟡 LOW RISK ({risk_score}/100): Minor anomalies or promotional indicators detected. "
                f"Exercise standard caution before trusting unverified claims."
            )

    def generate_why_suspicious(
        self,
        detector_results: List[DetectorResult],
        evidence: List[EvidenceItem],
        fraud_types: List[FraudType],
        risk_level: RiskLevel,
    ) -> List[str]:
        """Generates concise, plain-English bullet points explaining why the content was flagged.
        For safe content, explains clearly why it was determined safe.
        """
        if risk_level == RiskLevel.SAFE:
            safe_points = [
                "No phishing links, lookalike domains, or spoofed URLs detected.",
                "No requests for confidential credentials, passwords, or One-Time Passwords (OTPs).",
                "No artificial urgency, fake lottery prizes, or extortion threats found.",
                "Formatting and structural characteristics match normal authentic communication.",
            ]
            return safe_points

        points: List[str] = []

        # 1. Collect signals from firing detectors
        for det in detector_results:
            if det.fraud_probability >= 0.35 and det.signals:
                for sig in det.signals:
                    # Clean up signal strings to ensure plain English readability
                    clean_sig = sig.strip()
                    if clean_sig and clean_sig not in points:
                        points.append(clean_sig)

        # 2. Add high-level summaries if detector signals are brief
        if not points:
            for ft in fraud_types:
                if ft in FRAUD_TYPE_DESCRIPTIONS and ft not in (FraudType.UNKNOWN, FraudType.SAFE):
                    points.append(f"{ft.value.replace('_', ' ').title()}: {FRAUD_TYPE_DESCRIPTIONS[ft]}")

        # Limit to top 6 most relevant points
        return points[:6]

    def generate_recommendations(
        self,
        risk_level: RiskLevel,
        fraud_types: List[FraudType],
        signals: List[str],
    ) -> List[str]:
        """Generates concrete, practical steps the user should take."""
        recs = []

        if risk_level == RiskLevel.SAFE:
            return [
                "Safe to interact with under normal conditions.",
                "As a general precaution, never share passwords, OTPs, or banking PINs with anyone.",
                "Verify sender details if any unexpected attachments or links are received later.",
            ]

        if risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            recs.append("Do NOT click any links, open attachments, or download files from this message.")
            recs.append("Never share One-Time Passwords (OTPs), UPI PINs, passwords, or card numbers.")

        if FraudType.PHISHING in fraud_types or any("url" in s.lower() or "domain" in s.lower() for s in signals):
            recs.append("Navigate to the official service website directly by typing the known address in your browser.")
            recs.append("Inspect the exact website domain name for subtle misspellings or extra characters.")

        if FraudType.FINANCIAL_FRAUD in fraud_types or any("upi" in s.lower() or "payment" in s.lower() for s in signals):
            recs.append("Do not authorize any UPI payment requests or enter your UPI PIN to 'receive' money.")
            recs.append("Halt any wire transfers, gift card purchases, or processing fee payments.")

        if FraudType.SPAM in fraud_types:
            recs.append("Block the sender and report the message as spam.")
            recs.append("Avoid replying to spam messages, as replying confirms your contact information is active.")

        if FraudType.AI_GENERATED in fraud_types:
            recs.append("Treat this media with skepticism; visual forensic signals indicate potential synthetic generation.")

        # Universal protective action
        recs.append("If unsure, contact the organization directly using their official, published customer care number.")

        # Deduplicate while preserving order
        seen = set()
        unique_recs = []
        for r in recs:
            if r not in seen:
                seen.add(r)
                unique_recs.append(r)

        return unique_recs[:5]

    def generate_multimodal_findings(
        self,
        evidence: List[EvidenceItem],
        detector_results: List[DetectorResult],
        extracted_content: Dict[str, Any],
    ) -> List[str]:
        """Explains in plain English what was extracted and examined across modalities."""
        findings = []

        # Check extracted text from image OCR or documents
        ext_text = extracted_content.get("extracted_text", "").strip()
        if ext_text:
            text_preview = ext_text[:120].replace("\n", " ") + ("..." if len(ext_text) > 120 else "")
            findings.append(f"Text Extracted via OCR: \"{text_preview}\"")

        # Check extracted URLs
        ext_urls = extracted_content.get("extracted_urls", [])
        if ext_urls:
            findings.append(f"Discovered {len(ext_urls)} embedded link(s) for safety inspection: {', '.join(ext_urls[:2])}")

        # Check extracted phone / email
        ext_phones = extracted_content.get("extracted_phones", [])
        if ext_phones:
            findings.append(f"Detected contact number(s): {', '.join(ext_phones[:2])}")

        # Check QR codes
        for ev in evidence:
            if ev.relationship == "contains_qr" or ev.source_modality == "QR":
                findings.append(f"Decoded QR Code payload: {ev.content[:100]}")
                break

        # Check AI Media detection
        for det in detector_results:
            if det.module == "ai_media" and det.metadata and "ai_media" in det.metadata:
                ai_meta = det.metadata["ai_media"]
                verdict = ai_meta.get("result", "").replace("_", " ")
                conf = ai_meta.get("confidence", 50)
                findings.append(f"Visual Authenticity Check: {verdict} ({conf}% confidence)")

        if not findings:
            findings.append("Inspected direct input payload across all security validation engines.")

        return findings

    def generate_explanation(
        self,
        risk_score: int,
        risk_level: RiskLevel,
        fraud_types: List[FraudType],
        detector_results: List[DetectorResult],
        evidence: List[EvidenceItem],
        extracted_content: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Produces a clean, human-readable markdown report without robotic buzzwords."""
        ext = extracted_content or {}
        summary = self.generate_summary(risk_score, risk_level, fraud_types, None)
        why_list = self.generate_why_suspicious(detector_results, evidence, fraud_types, risk_level)
        recs_list = self.generate_recommendations(risk_level, fraud_types, [s for d in detector_results for s in d.signals])
        findings_list = self.generate_multimodal_findings(evidence, detector_results, ext)

        sections = []
        sections.append(f"### Security Assessment\n{summary}")

        if why_list:
            why_md = "\n".join(f"- {w}" for w in why_list)
            header = "Why This Is Considered Safe" if risk_level == RiskLevel.SAFE else "Key Warning Signs Detected"
            sections.append(f"### {header}\n{why_md}")

        if findings_list:
            findings_md = "\n".join(f"- {f}" for f in findings_list)
            sections.append(f"### What SentriX Inspected\n{findings_md}")

        if recs_list:
            recs_md = "\n".join(f"{i+1}. {r}" for i, r in enumerate(recs_list))
            sections.append(f"### Recommended Actions\n{recs_md}")

        return "\n\n".join(sections)

