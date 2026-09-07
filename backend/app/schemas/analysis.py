from enum import Enum
from pydantic import BaseModel
from typing import List, Optional, Any, Dict

class InputType(str, Enum):
    URL = 'URL'
    QR = 'QR'
    IMAGE = 'IMAGE'
    VIDEO = 'VIDEO'
    PDF = 'PDF'
    DOCUMENT = 'DOCUMENT'
    AUDIO = 'AUDIO'
    TEXT = 'TEXT'
    EMAIL = 'EMAIL'
    UNKNOWN = 'UNKNOWN'

class RiskLevel(str, Enum):
    SAFE = 'SAFE'
    LOW = 'LOW'
    MEDIUM = 'MEDIUM'
    HIGH = 'HIGH'
    CRITICAL = 'CRITICAL'

class FraudType(str, Enum):
    PHISHING = 'PHISHING'
    SCAM = 'SCAM'
    SPAM = 'SPAM'
    SOCIAL_ENGINEERING = 'SOCIAL_ENGINEERING'
    DEEPFAKE = 'DEEPFAKE'
    DOCUMENT_FRAUD = 'DOCUMENT_FRAUD'
    IDENTITY_THEFT = 'IDENTITY_THEFT'
    FINANCIAL_FRAUD = 'FINANCIAL_FRAUD'
    MALWARE = 'MALWARE'
    UNKNOWN = 'UNKNOWN'

class DetectorResult(BaseModel):
    module: str
    fraud_probability: float
    confidence: float
    risk: RiskLevel
    signals: List[str]
    model_version: str
    processing_time_ms: float
    metadata: Dict[str, Any] = {}
    error: Optional[str] = None

class EvidenceItem(BaseModel):
    evidence_type: str
    source_modality: str
    target_modality: Optional[str] = None
    content: str
    severity: str
    relationship: Optional[str] = None

class AnalysisRequest(BaseModel):
    text: Optional[str] = None
    url: Optional[str] = None

class AnalysisResponse(BaseModel):
    analysis_id: str
    input_type: InputType
    risk_score: int
    risk_level: RiskLevel
    fraud_types: List[FraudType]
    confidence: float
    detectors: List[DetectorResult]
    evidence: List[EvidenceItem]
    explanation: str
    recommendations: List[str]
    extracted_content: Dict[str, Any] = {}
    processing_time_ms: float
    created_at: str
    disclaimer: str = 'SentriX provides AI-based risk assessment, not definitive proof of fraud. Always verify important information through an independent trusted source.'

class HistoryItem(BaseModel):
    analysis_id: str
    input_type: InputType
    risk_score: int
    risk_level: RiskLevel
    fraud_types: List[FraudType]
    processing_time_ms: float
    created_at: str

class HistoryResponse(BaseModel):
    items: List[HistoryItem]
    total: int
    page: int
    page_size: int

class HealthResponse(BaseModel):
    status: str
    version: str
    uptime_seconds: float
    models_loaded: Dict[str, bool]
    database_connected: bool
