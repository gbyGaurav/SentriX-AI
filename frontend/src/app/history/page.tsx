'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { getHistory } from '../../lib/api';
import { HistoryItem, HistoryResponse } from '../../types';
import RiskBadge from '../../components/RiskBadge';

export default function HistoryPage() {
  const router = useRouter();
  const [history, setHistory] = useState<HistoryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const pageSize = 20;

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

  return (
    <div className="container mx-auto px-4 py-8 max-w-5xl">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-2xl font-bold text-white">Analysis History</h1>
        <button
          onClick={() => router.push('/')}
          className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg transition-colors text-sm border border-slate-700"
        >
          ← New Analysis
        </button>
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
      ) : (
        <>
          <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-800">
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">ID</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Type</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Risk</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Level</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Categories</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-slate-500 uppercase tracking-wider">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {history.items.map((item: HistoryItem) => (
                  <tr
                    key={item.analysis_id}
                    className="hover:bg-slate-800/50 cursor-pointer transition-colors"
                    onClick={() => router.push(`/analysis/${item.analysis_id}`)}
                  >
                    <td className="px-4 py-3 text-sm font-mono text-slate-400">
                      {item.analysis_id.slice(0, 8)}…
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-300">
                      <span className="mr-1">{inputTypeIcons[item.input_type] ?? '❓'}</span>
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
                      <div className="flex flex-wrap gap-1">
                        {item.fraud_types.slice(0, 2).map((ft, i) => (
                          <span key={i} className="text-[10px] px-1.5 py-0.5 bg-slate-800 rounded text-slate-400">
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
                    <td className="px-4 py-3 text-right text-xs text-slate-500">
                      {new Date(item.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {history.total > pageSize && (
            <div className="flex justify-center gap-2 mt-6">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-3 py-1.5 bg-slate-800 text-slate-300 rounded-lg text-sm disabled:opacity-50 hover:bg-slate-700 transition-colors"
              >
                Previous
              </button>
              <span className="px-3 py-1.5 text-sm text-slate-400">
                Page {page} of {Math.ceil(history.total / pageSize)}
              </span>
              <button
                onClick={() => setPage(p => p + 1)}
                disabled={page * pageSize >= history.total}
                className="px-3 py-1.5 bg-slate-800 text-slate-300 rounded-lg text-sm disabled:opacity-50 hover:bg-slate-700 transition-colors"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
