"""Cross-Modal Evidence Graph & Relationship Aggregator.
Tracks provenance chains between extracted modalities and calculates cross-modal agreement bonuses.
Example:
    Document -> contains -> QR -> resolves_to -> URL -> URL detector flags High Risk
"""

from typing import List, Dict, Any, Set, Tuple
from app.schemas.analysis import EvidenceItem, DetectorResult


class EvidenceGraph:
    """Manages cross-modal nodes, relationships, and agreement metrics."""

    def __init__(self):
        self.evidence: List[EvidenceItem] = []
        self.nodes: Set[str] = set()
        self.edges: List[Dict[str, Any]] = []

    def add_relationship(
        self,
        source: str,
        relationship: str,
        target: str,
        content: str,
        severity: str = "info"
    ) -> EvidenceItem:
        """Adds a directional evidence relationship between modalities or entities."""
        item = EvidenceItem(
            evidence_type=f"{source.lower()}_{relationship.lower()}_{target.lower()}",
            source_modality=source,
            target_modality=target,
            content=content,
            severity=severity,
            relationship=relationship,
        )
        self.evidence.append(item)
        self.nodes.add(source)
        self.nodes.add(target)
        self.edges.append({
            "source": source,
            "relationship": relationship,
            "target": target,
            "content": content,
            "severity": severity,
        })
        return item

    def add_evidence(self, item: EvidenceItem):
        self.evidence.append(item)
        self.nodes.add(item.source_modality)
        if item.target_modality:
            self.nodes.add(item.target_modality)
        if item.relationship:
            self.edges.append({
                "source": item.source_modality,
                "relationship": item.relationship,
                "target": item.target_modality,
                "content": item.content,
                "severity": item.severity,
            })

    def compute_cross_modal_bonus(self, detector_results: List[DetectorResult]) -> Tuple[int, float]:
        """Calculates a risk score bonus (0-20) and confidence multiplier
        based on cross-modal agreement and chain complexity.
        """
        if not self.evidence or len(detector_results) <= 1:
            return 0, 1.0

        bonus = 0
        conf_multiplier = 1.0

        # Check if multiple modalities produced high risk
        high_risk_mods = [d.module for d in detector_results if d.fraud_probability >= 0.5]
        if len(high_risk_mods) >= 2:
            bonus += 10
            conf_multiplier += 0.15

        # Check for cascading link traversal (e.g. Doc/Image -> QR -> URL)
        has_qr_chain = any("qr" in e.get("source", "").lower() or "qr" in e.get("target", "").lower() for e in self.edges)
        has_url_chain = any("url" in e.get("target", "").lower() for e in self.edges)

        if has_qr_chain and has_url_chain:
            bonus += 5
            conf_multiplier += 0.1

        # Critical severity edges (e.g. credentials, rogue payment)
        critical_count = sum(1 for e in self.evidence if e.severity == "critical")
        bonus += min(10, critical_count * 5)

        return min(25, bonus), min(1.3, conf_multiplier)

    def get_evidence_summary(self) -> List[EvidenceItem]:
        return self.evidence

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_count": len(self.nodes),
            "nodes": list(self.nodes),
            "edge_count": len(self.edges),
            "edges": self.edges,
            "evidence": [e.model_dump() for e in self.evidence],
        }
