'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { getAnalysis } from '../../../lib/api';
import { AnalysisResponse } from '../../../types';
import RiskScore from '../../../components/RiskScore';
import RiskBadge from '../../../components/RiskBadge';
import DetectorResultCard from '../../../components/DetectorResultCard';
import EvidenceList from '../../../components/EvidenceList';
import AIExplanation from '../../../components/AIExplanation';
import ExtractedContent from '../../../components/ExtractedContent';

const INPUT_TYPE_ICONS: Record<string, string> = {
  URL: '🔗', QR: '📱', IMAGE: '🖼️', VIDEO: '🎬', PDF: '📄',
  DOCUMENT: '📝', AUDIO: '🎵', TEXT: '💬', EMAIL: '📧', UNKNOWN: '❓',
};

export default function AnalysisPage() {
  const params = useParams();
  const router = useRouter();
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const rawId = params?.id;
    const id = Array.isArray(rawId) ? rawId[0] : rawId;
    if (!id || id === 'undefined' || id === 'null') {
      setError('Invalid analysis ID.');
      setLoading(false);
      return;
    }

    getAnalysis(id)
      .then(setAnalysis)
      .catch(err => {
        let msg = err.message || 'Failed to load analysis';
        try {
          const parsed = JSON.parse(msg);
          if (parsed.detail) msg = parsed.detail;
        } catch {}
        setError(msg);
      })
      .finally(() => setLoading(false));
  }, [params]);

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-20 flex flex-col items-center justify-center">
        <div className="w-12 h-12 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" />
        <p className="text-slate-400 mt-4">Loading analysis...</p>
      </div>
    );
  }

  if (error || !analysis) {
    return (
      <div className="container mx-auto px-4 py-20 flex flex-col items-center">
        <div className="bg-rose-500/10 border border-rose-500/20 rounded-xl p-6 max-w-md text-center">
          <p className="text-rose-400 text-lg mb-2">Analysis Not Found</p>
          <p className="text-slate-400 text-sm">{error ?? 'The requested analysis could not be loaded.'}</p>
          <button
            onClick={() => router.push('/')}
            className="mt-4 px-6 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg transition-colors text-sm"
          >
            ← Back to Home
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-3">
          <span className="text-3xl">{INPUT_TYPE_ICONS[analysis.input_type] ?? '❓'}</span>
          <div>
            <h1 className="text-xl font-bold text-white">Analysis Report</h1>
            <p className="text-sm text-slate-400">
              {analysis.input_type} • {new Date(analysis.created_at).toLocaleString()} •
              <span className="font-mono ml-1">{analysis.processing_time_ms.toFixed(0)}ms</span>
            </p>
          </div>
        </div>
        <button
          onClick={() => router.push('/')}
          className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg transition-colors text-sm border border-slate-700"
        >
          Analyze Another
        </button>
      </div>

      {/* Risk Score + Fraud Types */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <div className="lg:col-span-1 flex justify-center">
          <RiskScore
            score={analysis.risk_score}
            level={analysis.risk_level}
            confidence={analysis.confidence}
          />
        </div>
        <div className="lg:col-span-2 flex flex-col justify-center">
          <AIExplanation
            riskLevel={analysis.risk_level}
            explanation={analysis.explanation}
            recommendations={analysis.recommendations}
            fraudTypes={analysis.fraud_types}
          />
        </div>
      </div>

      {/* Detector Results */}
      {analysis.detectors.length > 0 && (
        <div className="mb-8">
          <h2 className="text-slate-400 text-sm font-medium uppercase tracking-wider mb-4">
            Detector Breakdown
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {analysis.detectors.map((det, i) => (
              <DetectorResultCard key={i} result={det} />
            ))}
          </div>
        </div>
      )}

      {/* Evidence */}
      {analysis.evidence.length > 0 && (
        <div className="mb-8">
          <EvidenceList evidence={analysis.evidence} />
        </div>
      )}

      {/* Extracted Content */}
      {Object.keys(analysis.extracted_content).length > 0 && (
        <div className="mb-8">
          <ExtractedContent content={analysis.extracted_content} />
        </div>
      )}

      {/* Disclaimer */}
      <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4 text-center">
        <p className="text-xs text-slate-500">{analysis.disclaimer}</p>
        <p className="text-[10px] text-slate-600 mt-1 font-mono">
          Analysis ID: {analysis.analysis_id}
        </p>
      </div>
    </div>
  );
}
