'use client';

import { DetectorResult as DetectorResultType } from '../types';
import RiskBadge from './RiskBadge';
import { useState } from 'react';

interface Props {
  result: DetectorResultType;
}

const MODULE_LABELS: Record<string, string> = {
  url_fraud: 'URL & Link Analysis',
  text_fraud: 'Text & Social Engineering',
  spam_fraud: 'Spam & Scam Classifier',
  qr_fraud: 'QR Code Analysis',
  document_fraud: 'Document Analysis',
  image_fraud: 'Image Forensics & OCR',
  ai_media: 'AI Media & Authenticity',
  video_fraud: 'Video Forensics',
  audio_fraud: 'Audio Analysis',
};

export default function DetectorResultCard({ result }: Props) {
  const [expanded, setExpanded] = useState(false);
  const pct = Math.round(result.fraud_probability * 100);

  const statusLabel =
    pct >= 70 ? 'High Risk' :
    pct >= 40 ? 'Suspicious' :
    pct >= 20 ? 'Low Concern' : 'Clean';

  const barColor =
    pct <= 19 ? 'bg-emerald-500' :
    pct <= 39 ? 'bg-yellow-500' :
    pct <= 69 ? 'bg-orange-500' :
    pct <= 84 ? 'bg-red-500' : 'bg-rose-600';

  return (
    <div className="bg-slate-800/60 rounded-xl border border-slate-700/50 p-5 hover:border-slate-600 transition-all">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h4 className="text-white font-semibold text-base">
            {MODULE_LABELS[result.module] ?? result.module}
          </h4>
          <span className="text-[11px] text-slate-400">Status: {statusLabel}</span>
        </div>
        <RiskBadge level={result.risk} />
      </div>

      {/* Probability bar */}
      <div className="mb-3">
        <div className="flex justify-between text-xs text-slate-400 mb-1">
          <span>Risk Indicator</span>
          <span className="font-mono">{pct}%</span>
        </div>

        <div className="w-full h-2 bg-slate-700 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-700 ease-out ${barColor}`}
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>

      {/* Confidence */}
      <div className="flex justify-between text-xs text-slate-400 mb-3">
        <span>Confidence: {Math.round(result.confidence * 100)}%</span>
        <span>⏱ {result.processing_time_ms.toFixed(0)}ms</span>
      </div>

      {/* Signals */}
      {result.signals.length > 0 && (
        <div>
          <button
            className="text-xs text-cyan-400 hover:text-cyan-300 transition-colors mb-2"
            onClick={() => setExpanded(!expanded)}
          >
            {expanded ? '▾' : '▸'} {result.signals.length} signal{result.signals.length > 1 ? 's' : ''} detected
          </button>
          {expanded && (
            <ul className="space-y-1 mt-1">
              {result.signals.map((signal, i) => (
                <li key={i} className="flex items-start text-sm text-slate-300">
                  <span className="text-cyan-400 mr-2 mt-0.5 shrink-0">✓</span>
                  {signal}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {/* Error state */}
      {result.error && (
        <div className="mt-2 text-xs text-amber-400 bg-amber-500/10 px-3 py-2 rounded-lg">
          ⚠ {result.error}
        </div>
      )}

      {/* Model version */}
      <div className="mt-3 pt-2 border-t border-slate-700/40">
        <span className="text-[10px] text-slate-500 font-mono">
          model: {result.model_version}
        </span>
      </div>
    </div>
  );
}
