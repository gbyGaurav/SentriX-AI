'use client';

import { useEffect, useState, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { getHistory } from '../../lib/api';
import { HistoryItem, HistoryResponse, RiskLevel, InputType } from '../../types';
import RiskBadge from '../../components/RiskBadge';

const RISK_FILTERS = ['ALL', 'SAFE', 'LOW', 'MEDIUM', 'HIGH'] as const;
const MODALITY_FILTERS = ['ALL', 'TEXT', 'URL', 'QR', 'IMAGE', 'VIDEO', 'PDF'] as const;

export default function HistoryPage() {
  const router = useRouter();
  const [history, setHistory] = useState<HistoryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [selectedRisk, setSelectedRisk] = useState<string>('ALL');
  const [selectedModality, setSelectedModality] = useState<string>('ALL');
  const pageSize = 50;

  useEffect(() => {
    setLoading(true);
    getHistory(page, pageSize)
      .then(setHistory)
      .catch(() => setHistory(null))
      .finally(() => setLoading(false));
  }, [page]);

  const inputTypeIcons: Record<string, string> = {
    URL: '🔗', QR: '📱', IMAGE: '🖼️', VIDEO: '🎬', PDF: '📄',
    DOCUMENT: '📝', AUDIO: '🎵', TEXT: '💬', EMAIL: '📧', UNKNOWN: '❓',
  };

  const filteredItems = useMemo(() => {
    if (!history || !history.items) return [];
    return history.items.filter((item) => {
      // Risk filter
      if (selectedRisk !== 'ALL') {
        if (selectedRisk === 'HIGH') {
          if (item.risk_level !== 'HIGH' && item.risk_level !== 'CRITICAL') return false;
        } else if (item.risk_level !== selectedRisk) {
          return false;
        }
      }
      // Modality filter
      if (selectedModality !== 'ALL') {
        if (item.input_type !== selectedModality) return false;
      }
      return true;
    });
  }, [history, selectedRisk, selectedModality]);

  return (
    <div className="container mx-auto px-4 py-8 max-w-5xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Analysis History</h1>
          <p className="text-xs text-slate-400 mt-1">Review previously audited links, media, and text artifacts</p>
        </div>
        <button
          onClick={() => router.push('/')}
          className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg transition-colors text-sm border border-slate-700"
        >
          ← New Analysis
        </button>
      </div>

      {/* Filter Controls */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 mb-6 space-y-3">
        {/* Risk Level Filter */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider mr-2">Risk:</span>
          {RISK_FILTERS.map((r) => (
            <button
              key={r}
              onClick={() => setSelectedRisk(r)}
              className={`px-3 py-1 rounded-lg text-xs font-medium transition-all ${
                selectedRisk === r
                  ? 'bg-cyan-500 text-black font-bold shadow'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700/60'
              }`}
            >
              {r}
            </button>
          ))}
        </div>

        {/* Modality Filter */}
        <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-800/80">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider mr-2">Type:</span>
          {MODALITY_FILTERS.map((m) => (
            <button
              key={m}
              onClick={() => setSelectedModality(m)}
              className={`px-3 py-1 rounded-lg text-xs font-medium transition-all ${
                selectedModality === m
                  ? 'bg-cyan-500 text-black font-bold shadow'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700/60'
              }`}
            >
              {m}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-20">
          <div className="w-8 h-8 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : !history || history.items.length === 0 ? (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-12 text-center">
          <p className="text-slate-400 text-lg mb-2">No analyses yet</p>
          <p className="text-slate-500 text-sm">Upload something suspicious to get started.</p>
          <button
            onClick={() => router.push('/')}
            className="mt-4 px-6 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg transition-colors text-sm"
          >
            Start Analyzing
          </button>
        </div>
      ) : filteredItems.length === 0 ? (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 text-center">
          <p className="text-slate-400 text-sm mb-2">No past records matched the selected filters.</p>
          <button
            onClick={() => {
              setSelectedRisk('ALL');
              setSelectedModality('ALL');
            }}
            className="text-xs text-cyan-400 hover:underline"
          >
            Clear all filters
          </button>
        </div>
      ) : (
        <>
          <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-lg">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-800">
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">ID</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Type</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Score</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Level</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">AI Authenticity</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Threats</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-slate-500 uppercase tracking-wider">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {filteredItems.map((item: HistoryItem) => (
                  <tr
                    key={item.analysis_id}
                    className="hover:bg-slate-800/50 cursor-pointer transition-colors"
                    onClick={() => router.push(`/analysis/${item.analysis_id}`)}
                  >
                    <td className="px-4 py-3 text-sm font-mono text-cyan-400 hover:underline">
                      {item.analysis_id.slice(0, 8)}…
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-300">
                      <span className="mr-1.5">{inputTypeIcons[item.input_type] ?? '❓'}</span>
                      {item.input_type}
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-sm font-bold font-mono text-white">{item.risk_score}</span>
                      <span className="text-xs text-slate-500">/100</span>
                    </td>
                    <td className="px-4 py-3">
                      <RiskBadge level={item.risk_level} />
                    </td>
                    <td className="px-4 py-3">
                      {item.ai_media ? (
                        <span
                          className={`text-[10px] font-bold px-2 py-0.5 rounded whitespace-nowrap ${
                            item.ai_media.result === 'LIKELY_AI_GENERATED'
                              ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30'
                              : item.ai_media.result === 'POSSIBLY_AI_GENERATED'
                              ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30'
                              : item.ai_media.result === 'LIKELY_AUTHENTIC'
                              ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                              : 'bg-slate-800 text-slate-400 border border-slate-700'
                          }`}
                        >
                          {item.ai_media.result === 'LIKELY_AI_GENERATED'
                            ? '🤖 LIKELY AI'
                            : item.ai_media.result === 'POSSIBLY_AI_GENERATED'
                            ? '🤖 POSSIBLY AI'
                            : item.ai_media.result === 'LIKELY_AUTHENTIC'
                            ? '📷 AUTHENTIC'
                            : '⚪ INCONCLUSIVE'}
                        </span>
                      ) : (
                        <span className="text-slate-600 text-xs">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-1">
                        {item.fraud_types.slice(0, 2).map((ft, i) => (
                          <span
                            key={i}
                            className={`text-[10px] px-1.5 py-0.5 rounded ${
                              ft === 'SAFE'
                                ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20'
                                : 'bg-slate-800 text-slate-300'
                            }`}
                          >
                            {ft.replace(/_/g, ' ')}
                          </span>
                        ))}
                        {item.fraud_types.length > 2 && (
                          <span className="text-[10px] px-1.5 py-0.5 bg-slate-800 rounded text-slate-500">
                            +{item.fraud_types.length - 2}
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-right text-xs text-slate-400">
                      {new Date(item.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}

