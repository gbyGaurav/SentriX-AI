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

  return (
    <div className="bg-slate-900 rounded-2xl border border-slate-800 p-6 space-y-6">
      {/* Why header */}
      <div>
        <h3 className={`text-lg font-bold ${colorClass} mb-1`}>
          Why This Is {riskLevel} Risk
        </h3>
        <p className="text-slate-300 text-sm leading-relaxed whitespace-pre-line">
          {explanation}
        </p>
      </div>

      {/* Fraud types */}
      {fraudTypes.length > 0 && (
        <div>
          <h4 className="text-slate-400 text-xs font-medium uppercase tracking-wider mb-2">
            Detected Fraud Categories
          </h4>
          <div className="flex flex-wrap gap-2">
            {fraudTypes.map((ft, i) => (
              <span
                key={i}
                className="px-3 py-1.5 text-xs font-medium rounded-lg bg-slate-800 border border-slate-700 text-slate-200"
              >
                {ft.replace(/_/g, ' ')}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Recommendations */}
      {recommendations.length > 0 && (
        <div>
          <h4 className="text-slate-400 text-xs font-medium uppercase tracking-wider mb-3">
            Recommended Actions
          </h4>
          <ul className="space-y-2">
            {recommendations.map((rec, i) => (
              <li key={i} className="flex items-start text-sm text-slate-300">
                <span className="text-emerald-400 mr-2 mt-0.5 shrink-0">🛡️</span>
                {rec}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Disclaimer */}
      <div className="pt-4 border-t border-slate-800">
        <p className="text-xs text-slate-500 italic">
          UAMD provides AI-based risk assessment, not definitive proof of fraud.
          Always verify important information through an independent trusted source.
        </p>
      </div>
    </div>
  );
}
