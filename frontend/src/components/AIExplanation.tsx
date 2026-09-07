'use client';

import { RiskLevel, FraudType } from '../types';
import { getRiskColor } from '../lib/utils';

interface Props {
  riskLevel: RiskLevel;
  explanation: string;
  recommendations: string[];
  fraudTypes: FraudType[];
}

export default function AIExplanation({ riskLevel, explanation, recommendations, fraudTypes }: Props) {
  const colorClass = getRiskColor(riskLevel);

  // Simple clean markdown formatter for sections and bold text
  const formatContent = (text: string) => {
    return text.split('\n\n').map((paragraph, pIdx) => {
      if (paragraph.startsWith('### ')) {
        const title = paragraph.replace('### ', '');
        return (
          <h4 key={pIdx} className="text-sm font-bold text-cyan-300 mt-4 mb-1.5 uppercase tracking-wide flex items-center gap-1.5">
            {title}
          </h4>
        );
      }
      return (
        <p key={pIdx} className="text-slate-300 text-sm leading-relaxed whitespace-pre-line mb-3">
          {paragraph.split('**').map((segment, sIdx) => 
            sIdx % 2 === 1 ? <strong key={sIdx} className="text-white font-semibold">{segment}</strong> : segment
          )}
        </p>
      );
    });
  };

  return (
    <div className="bg-slate-900 rounded-2xl border border-slate-800 p-6 space-y-6">
      {/* Investigation Report header */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs uppercase tracking-wider font-semibold text-slate-400">
            Threat Intelligence Summary
          </span>
          <span className="text-xs px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
            AI Automated Reasoning (Zero-Key)
          </span>
        </div>
        <div className="prose prose-invert max-w-none">
          {formatContent(explanation)}
        </div>
      </div>

      {/* Fraud types */}
      {fraudTypes.length > 0 && fraudTypes[0] !== 'UNKNOWN' && (
        <div>
          <h4 className="text-slate-400 text-xs font-medium uppercase tracking-wider mb-2">
            Identified Threat Classifications
          </h4>
          <div className="flex flex-wrap gap-2">
            {fraudTypes.map((ft, i) => (
              <span
                key={i}
                className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-800/90 border border-slate-700 text-cyan-300 shadow-sm"
              >
                {ft.replace(/_/g, ' ')}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Recommendations */}
      {recommendations.length > 0 && (
        <div className="pt-2 border-t border-slate-800/80">
          <h4 className="text-slate-400 text-xs font-medium uppercase tracking-wider mb-3">
            Recommended Defensive Actions
          </h4>
          <ul className="space-y-2">
            {recommendations.map((rec, i) => (
              <li key={i} className="flex items-start text-sm text-slate-300">
                <span className="text-emerald-400 mr-2 mt-0.5 shrink-0">🛡️</span>
                <span>{rec}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Disclaimer */}
      <div className="pt-4 border-t border-slate-800">
        <p className="text-xs text-slate-500 italic">
          SentriX provides AI-based risk assessment, not definitive proof of fraud.
          Always verify important information through an independent trusted source.
        </p>
      </div>
    </div>
  );
}
