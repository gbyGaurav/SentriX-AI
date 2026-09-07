export type InputType = 'URL' | 'QR' | 'IMAGE' | 'VIDEO' | 'PDF' | 'DOCUMENT' | 'AUDIO' | 'TEXT' | 'EMAIL' | 'UNKNOWN';

export type RiskLevel = 'SAFE' | 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export type FraudType =
  | 'PHISHING'
  | 'SCAM'
  | 'SPAM'
  | 'SOCIAL_ENGINEERING'
  | 'DEEPFAKE'
  | 'DOCUMENT_FRAUD'
  | 'IDENTITY_THEFT'
  | 'FINANCIAL_FRAUD'
  | 'MALWARE'
  | 'AI_GENERATED'
  | 'SUSPICIOUS_QR'
  | 'FAKE_DOCUMENT'
  | 'SAFE'
  | 'UNKNOWN';

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

export interface AIMediaResult {
  result: 'LIKELY_AI_GENERATED' | 'POSSIBLY_AI_GENERATED' | 'LIKELY_AUTHENTIC' | 'INCONCLUSIVE';
  confidence: number;
  evidence: string[];
  disclaimer: string;
}

export interface AnalysisResponse {
  analysis_id: string;
  id?: string;
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

  // New Practical User-Friendly Fields
  summary?: string;
  why_suspicious?: string[];
  recommended_actions?: string[];
  primary_threat?: string;
  threats?: string[];
  ai_media?: AIMediaResult | null;
  multimodal_findings?: string[];
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
