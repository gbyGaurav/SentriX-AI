export type InputType = 'URL' | 'QR' | 'IMAGE' | 'VIDEO' | 'PDF' | 'DOCUMENT' | 'AUDIO' | 'TEXT' | 'EMAIL' | 'UNKNOWN';

export type RiskLevel = 'SAFE' | 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export type FraudType = 'PHISHING' | 'SCAM' | 'SPAM' | 'SOCIAL_ENGINEERING' | 'DEEPFAKE' | 'DOCUMENT_FRAUD' | 'IDENTITY_THEFT' | 'FINANCIAL_FRAUD' | 'MALWARE' | 'UNKNOWN';

export interface DetectorResult {
  module: string;
  fraud_probability: number;
  confidence: number;
  risk: RiskLevel;
  signals: string[];
  model_version: string;
  processing_time_ms: number;
  metadata: Record<string, any>;
  error: string | null;
}

export interface EvidenceItem {
  evidence_type: string;
  source_modality: string;
  target_modality: string | null;
  content: string;
  severity: 'info' | 'warning' | 'critical';
  relationship: string | null;
}

export interface AnalysisResponse {
  analysis_id: string;
  input_type: InputType;
  risk_score: number;
  risk_level: RiskLevel;
  fraud_types: FraudType[];
  confidence: number;
  detectors: DetectorResult[];
  evidence: EvidenceItem[];
  explanation: string;
  recommendations: string[];
  extracted_content: Record<string, any>;
  processing_time_ms: number;
  created_at: string;
  disclaimer: string;
}

export interface HistoryItem {
  analysis_id: string;
  input_type: InputType;
  risk_score: number;
  risk_level: RiskLevel;
  fraud_types: FraudType[];
  processing_time_ms: number;
  created_at: string;
}

export interface HistoryResponse {
  items: HistoryItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface HealthResponse {
  status: string;
  version: string;
  uptime_seconds: number;
  models_loaded: Record<string, boolean>;
  database_connected: boolean;
}
