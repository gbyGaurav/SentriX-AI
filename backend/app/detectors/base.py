from abc import ABC, abstractmethod
from app.schemas.analysis import DetectorResult, RiskLevel
from typing import Any, Dict, List, Optional

class FraudDetector(ABC):
    @abstractmethod
    async def analyze(self, **kwargs) -> DetectorResult:
        pass
    
    @property
    @abstractmethod
    def module_name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def model_version(self) -> str:
        pass
    
    def _calculate_risk_level(self, probability: float) -> RiskLevel:
        if probability <= 0.20: return RiskLevel.SAFE
        elif probability <= 0.40: return RiskLevel.LOW
        elif probability <= 0.60: return RiskLevel.MEDIUM
        elif probability <= 0.80: return RiskLevel.HIGH
        else: return RiskLevel.CRITICAL
    
    def _create_result(self, probability: float, confidence: float, signals: List[str], processing_time_ms: float, metadata: Dict[str, Any] = {}, error: Optional[str] = None) -> DetectorResult:
        return DetectorResult(
            module=self.module_name,
            fraud_probability=round(probability, 4),
            confidence=round(confidence, 4),
            risk=self._calculate_risk_level(probability),
            signals=signals,
            model_version=self.model_version,
            processing_time_ms=round(processing_time_ms, 2),
            metadata=metadata,
            error=error
        )
