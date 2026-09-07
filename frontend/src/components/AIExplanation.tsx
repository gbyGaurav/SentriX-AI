'use client';

import { RiskLevel, FraudType, AIMediaResult } from '../types';
import { getRiskColor } from '../lib/utils';

interface Props {
  riskLevel: RiskLevel;
  explanation: string;
  recommendations: string[];
  fraudTypes: FraudType[];
  summary?: string;
  whySuspicious?: string[];
  recommendedActions?: string[];
  multimodalFindings?: string[];
  primaryThreat?: string;
  threats?: string[];
  aiMedia?: AIMediaResult | null;
}

export default function AIExplanation({
  riskLevel,
  explanation,
  recommendations,
  fraudTypes,
  summary,
  whySuspicious = [],
  recommendedActions = [],
  multimodalFindings = [],
  primaryThreat,
  threats = [],
  aiMedia,
}: Props) {
  const isSafe = riskLevel === 'SAFE';

  // Effective threat list
  const activeThreats =
    threats.length > 0
      ? threats
      : fraudTypes
          .filter((f) => f !== 'UNKNOWN' && f !== 'SAFE')
          .map((f) => f.replace(/_/g, ' '));

  // Effective recommendations
  const effectiveRecs =
    recommendedActions.length > 0 ? recommendedActions : recommendations;

  // Effective why suspicious points
  const effectiveWhy = whySuspicious.length > 0 ? whySuspicious : [];

  return (
    <div className="bg-slate-900 rounded-2xl border border-slate-800 p-6 space-y-6 shadow-xl">
      {/* 1. Threat Header & Badges */}
      <div>
        <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
          <div className="flex items-center gap-2">
            <span className="text-xs uppercase tracking-wider font-semibold text-slate-400">
              Security Assessment
            </span>
            {primaryThreat && primaryThreat !== 'UNKNOWN' && (
              <span className={`text-xs px-2.5 py-0.5 rounded-full font-medium ${
                isSafe ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
              }`}>
                {primaryThreat}
              </span>
            )}
          </div>
          <span className="text-xs px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700">
            Offline Intelligence Engine
          </span>
        </div>

        {/* Plain-English Summary */}
        <div className={`p-4 rounded-xl border ${
          isSafe
            ? 'bg-emerald-950/20 border-emerald-500/20 text-emerald-200'
            : riskLevel === 'HIGH' || riskLevel === 'CRITICAL'
            ? 'bg-rose-950/20 border-rose-500/20 text-rose-200'
            : 'bg-amber-950/20 border-amber-500/20 text-amber-200'
        }`}>
          <p className="text-sm font-medium leading-relaxed">
            {summary || explanation.split('\n\n')[0].replace(/### [^\n]+\n/, '')}
          </p>
        </div>
      </div>

      {/* 2. Detected Threat Tags */}
      {activeThreats.length > 0 && (
        <div>
          <h4 className="text-slate-400 text-xs font-semibold uppercase tracking-wider mb-2">
            {isSafe ? 'Status Classification' : 'Identified Threat Vectors'}
          </h4>
          <div className="flex flex-wrap gap-2">
            {activeThreats.map((threat, i) => (
              <span
                key={i}
                className={`px-3 py-1 text-xs font-medium rounded-lg border ${
                  isSafe
                    ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-300'
                    : 'bg-slate-800 border-slate-700 text-cyan-300'
                }`}
              >
                {threat}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* 3. Why Suspicious / Why Safe */}
      {effectiveWhy.length > 0 ? (
        <div className="pt-2 border-t border-slate-800/80">
          <h4 className="text-slate-400 text-xs font-semibold uppercase tracking-wider mb-3 flex items-center gap-1.5">
            <span>{isSafe ? '🟢 Why This Is Safe' : '⚠️ Why It Was Flagged'}</span>
          </h4>
          <ul className="space-y-2">
            {effectiveWhy.map((point, i) => (
              <li key={i} className="flex items-start text-sm text-slate-300">
                <span className={`mr-2.5 mt-0.5 shrink-0 ${isSafe ? 'text-emerald-400' : 'text-amber-400'}`}>
                  {isSafe ? '✓' : '•'}
                </span>
                <span className="leading-snug">{point}</span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {/* 4. Multimodal Findings (OCR text, QR payload, links found) */}
      {multimodalFindings.length > 0 && (
        <div className="pt-2 border-t border-slate-800/80">
          <h4 className="text-slate-400 text-xs font-semibold uppercase tracking-wider mb-3 flex items-center gap-1.5">
            <span>🔍 Multimodal Findings</span>
          </h4>
          <div className="bg-slate-950/60 rounded-xl p-3 border border-slate-800/60 space-y-2">
            {multimodalFindings.map((finding, i) => (
              <div key={i} className="text-xs text-slate-300 flex items-start gap-2">
                <span className="text-cyan-400 shrink-0">↳</span>
                <span className="font-mono text-slate-300">{finding}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 5. Dedicated AI-Generated Media Result (if present) */}
      {aiMedia && (
        <div className="pt-2 border-t border-slate-800/80">
          <h4 className="text-slate-400 text-xs font-semibold uppercase tracking-wider mb-3 flex items-center gap-1.5">
            <span>🤖 AI Media & Authenticity Inspection</span>
          </h4>
          <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-4 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400">Verdict:</span>
              <span
                className={`text-xs font-bold px-2.5 py-1 rounded ${
                  aiMedia.result === 'LIKELY_AI_GENERATED'
                    ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                    : aiMedia.result === 'POSSIBLY_AI_GENERATED'
                    ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                    : aiMedia.result === 'LIKELY_AUTHENTIC'
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                    : 'bg-slate-800 text-slate-300 border border-slate-700'
                }`}
              >
                {aiMedia.result.replace(/_/g, ' ')}
              </span>
            </div>
            <div className="flex items-center justify-between text-xs text-slate-400">
              <span>Analysis Confidence:</span>
              <span className="font-mono text-white">{aiMedia.confidence}%</span>
            </div>
            {aiMedia.evidence && aiMedia.evidence.length > 0 && (
              <div className="pt-2 text-xs text-slate-400">
                <span className="font-medium text-slate-300">Observed Signals:</span>
                <ul className="mt-1 space-y-1 list-disc list-inside text-slate-400">
                  {aiMedia.evidence.map((ev, i) => (
                    <li key={i}>{ev}</li>
                  ))}
                </ul>
              </div>
            )}
            <p className="text-[11px] text-slate-500 italic pt-2 border-t border-slate-800/60">
              ⚠️ {aiMedia.disclaimer || 'AI media detection is probabilistic and not definitive proof.'}
            </p>
          </div>
        </div>
      )}

      {/* 6. What Should You Do? (Recommended Actions) */}
      {effectiveRecs.length > 0 && (
        <div className="pt-2 border-t border-slate-800/80">
          <h4 className="text-slate-400 text-xs font-semibold uppercase tracking-wider mb-3 flex items-center gap-1.5">
            <span>🛡️ What Should You Do?</span>
          </h4>
          <ul className="space-y-2">
            {effectiveRecs.map((rec, i) => (
              <li key={i} className="flex items-start text-sm text-slate-300">
                <span className="text-emerald-400 mr-2 mt-0.5 shrink-0">▸</span>
                <span className="leading-snug">{rec}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

