"""Performance & ML monitoring module.
Tracks latency, throughput, fraud score distributions, and system errors in-memory.
"""

import time
from typing import Dict, Any, List
from collections import deque


class MonitoringManager:
    def __init__(self, max_history: int = 500):
        self.max_history = max_history
        self.request_times: deque = deque(maxlen=max_history)
        self.score_distribution: Dict[str, int] = {
            "SAFE": 0,
            "LOW": 0,
            "MEDIUM": 0,
            "HIGH": 0,
            "CRITICAL": 0,
        }
        self.modality_counts: Dict[str, int] = {}
        self.total_requests = 0
        self.total_errors = 0

    def record_analysis(self, input_type: str, risk_level: str, duration_ms: float):
        self.total_requests += 1
        self.request_times.append(duration_ms)
        if risk_level in self.score_distribution:
            self.score_distribution[risk_level] += 1
        self.modality_counts[input_type] = self.modality_counts.get(input_type, 0) + 1

    def record_error(self):
        self.total_errors += 1

    def get_metrics_summary(self) -> Dict[str, Any]:
        latencies = list(self.request_times)
        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
        p95_latency = (
            sorted(latencies)[int(len(latencies) * 0.95)] if len(latencies) >= 20 else avg_latency
        )

        return {
            "total_requests": self.total_requests,
            "total_errors": self.total_errors,
            "error_rate": (
                round(self.total_errors / max(1, self.total_requests), 4)
            ),
            "avg_latency_ms": round(avg_latency, 2),
            "p95_latency_ms": round(p95_latency, 2),
            "score_distribution": dict(self.score_distribution),
            "modality_breakdown": dict(self.modality_counts),
        }


# Global monitoring singleton
monitoring_manager = MonitoringManager()
