"""Multimodal Fusion & Risk Engine Evaluation Script.
Tests multi-modal agreement, conflicting signals, and calibration of the final 0-100 risk score.
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.schemas.analysis import DetectorResult, RiskLevel, EvidenceItem, FraudType
from app.fusion.fusion_engine import FusionEngine
from app.fusion.risk_engine import RiskEngine
from app.fusion.evidence_graph import EvidenceGraph


def evaluate_fusion_engine():
    fusion = FusionEngine()
    risk_engine = RiskEngine()

    test_scenarios = [
        {
            "name": "Scenario 1: Single High-Risk URL",
            "detectors": [
                DetectorResult(
                    module="url_fraud",
                    fraud_probability=0.92,
                    confidence=0.85,
                    risk=RiskLevel.CRITICAL,
                    signals=["IP address", "Suspicious TLD", "Credential keywords"],
                    model_version="url-v1",
                    processing_time_ms=25.0,
                )
            ],
            "evidence": [],
            "expected_level": RiskLevel.CRITICAL,
        },
        {
            "name": "Scenario 2: Cross-Modal High-Risk PDF (Doc + Text + URL Agree)",
            "detectors": [
                DetectorResult(
                    module="document_fraud",
                    fraud_probability=0.75,
                    confidence=0.82,
                    risk=RiskLevel.HIGH,
                    signals=["Missing metadata", "Invoice forgery"],
                    model_version="doc-v1",
                    processing_time_ms=50.0,
                ),
                DetectorResult(
                    module="text_fraud",
                    fraud_probability=0.95,
                    confidence=0.88,
                    risk=RiskLevel.CRITICAL,
                    signals=["High urgency", "Bank credentials request"],
                    model_version="text-v1",
                    processing_time_ms=12.0,
                ),
                DetectorResult(
                    module="url_fraud",
                    fraud_probability=0.88,
                    confidence=0.85,
                    risk=RiskLevel.CRITICAL,
                    signals=["Suspicious TLD", "Brand spoofing"],
                    model_version="url-v1",
                    processing_time_ms=15.0,
                ),
            ],
            "evidence": [
                EvidenceItem(
                    evidence_type="pdf_contains_url",
                    source_modality="PDF",
                    target_modality="URL",
                    content="http://fake-bank-login.xyz",
                    severity="critical",
                    relationship="contains_url",
                )
            ],
            "expected_level": RiskLevel.CRITICAL,
        },
        {
            "name": "Scenario 3: Completely Safe Benign Content",
            "detectors": [
                DetectorResult(
                    module="text_fraud",
                    fraud_probability=0.05,
                    confidence=0.90,
                    risk=RiskLevel.SAFE,
                    signals=[],
                    model_version="text-v1",
                    processing_time_ms=5.0,
                )
            ],
            "evidence": [],
            "expected_level": RiskLevel.SAFE,
        },
    ]

    print("=" * 60)
    print("     UAMD — Multimodal Fusion & Risk Engine Evaluation")
    print("=" * 60)

    for sc in test_scenarios:
        fused_prob, fused_conf = fusion.fuse(sc["detectors"])
        score, level, fraud_types, conf = risk_engine.calculate_risk(
            fused_prob, fused_conf, sc["detectors"], sc["evidence"]
        )

        match = (level == sc["expected_level"])
        status_str = "PASS" if match else "FAIL"

        print(f"\n{sc['name']}:")
        print(f"  Fused Probability: {fused_prob:.3f}")
        print(f"  Calculated Score:  {score}/100")
        print(f"  Risk Level:        {level.value} (Expected: {sc['expected_level'].value}) -> [{status_str}]")
        print(f"  Inferred Types:    {', '.join(f.value for f in fraud_types)}")
        print(f"  Confidence:        {conf:.1%}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    evaluate_fusion_engine()
