'use client';

import { EvidenceItem } from '../types';
import { useState } from 'react';

interface Props {
  evidence: EvidenceItem[];
}

const severityConfig = {
  info: { icon: 'ℹ️', border: 'border-blue-500/30', bg: 'bg-blue-500/5', text: 'text-blue-400' },
  warning: { icon: '⚠️', border: 'border-yellow-500/30', bg: 'bg-yellow-500/5', text: 'text-yellow-400' },
  critical: { icon: '🚨', border: 'border-red-500/30', bg: 'bg-red-500/5', text: 'text-red-400' },
};

export default function EvidenceList({ evidence }: Props) {
  const [expanded, setExpanded] = useState<Record<number, boolean>>({});

  if (evidence.length === 0) return null;

  const toggleExpand = (idx: number) => {
    setExpanded(prev => ({ ...prev, [idx]: !prev[idx] }));
  };

  return (
    <div className="bg-slate-900 rounded-2xl border border-slate-800 p-6">
      <h3 className="text-slate-400 text-sm font-medium uppercase tracking-wider mb-4">
        Evidence Trail ({evidence.length})
      </h3>
      <div className="space-y-3">
        {evidence.map((item, idx) => {
          const config = severityConfig[item.severity as keyof typeof severityConfig] ?? severityConfig.info;
          const isExpanded = expanded[idx];
          const contentPreview = item.content.length > 100 ? item.content.slice(0, 100) + '...' : item.content;

          return (
            <div
              key={idx}
              className={`rounded-lg border ${config.border} ${config.bg} p-4 transition-all`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-3 flex-1">
                  <span className="text-lg shrink-0">{config.icon}</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={`text-sm font-medium ${config.text}`}>
                        {item.evidence_type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </span>
                      {item.relationship && (
                        <span className="text-xs text-slate-500 bg-slate-800 px-2 py-0.5 rounded">
                          {item.source_modality} → {item.relationship} → {item.target_modality ?? '?'}
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-slate-300 mt-1 font-mono text-xs break-all">
                      {isExpanded ? item.content : contentPreview}
                    </p>
                    {item.content.length > 100 && (
                      <button
                        className="text-xs text-cyan-400 hover:text-cyan-300 mt-1"
                        onClick={() => toggleExpand(idx)}
                      >
                        {isExpanded ? 'Show less' : 'Show more'}
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
