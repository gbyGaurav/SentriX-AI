'use client';

import { useState } from 'react';

interface Props {
  content: Record<string, unknown>;
}

type TabKey = 'text' | 'urls' | 'entities' | 'metadata';

export default function ExtractedContent({ content }: Props) {
  const [activeTab, setActiveTab] = useState<TabKey>('text');

  const texts = content.extracted_text as string | undefined;
  const urls = content.extracted_urls as string[] | undefined;
  const emails = content.extracted_emails as string[] | undefined;
  const phones = content.extracted_phones as string[] | undefined;
  const metadata = content.metadata as Record<string, unknown> | undefined;

  const hasText = !!texts;
  const hasUrls = urls && urls.length > 0;
  const hasEntities = (emails && emails.length > 0) || (phones && phones.length > 0);
  const hasMetadata = metadata && Object.keys(metadata).length > 0;

  if (!hasText && !hasUrls && !hasEntities && !hasMetadata) return null;

  const tabs: { key: TabKey; label: string; show: boolean }[] = [
    { key: 'text', label: 'Text', show: hasText },
    { key: 'urls', label: `URLs${hasUrls ? ` (${urls!.length})` : ''}`, show: !!hasUrls },
    { key: 'entities', label: 'Entities', show: !!hasEntities },
    { key: 'metadata', label: 'Metadata', show: !!hasMetadata },
  ];

  const visibleTabs = tabs.filter(t => t.show);
  if (visibleTabs.length > 0 && !visibleTabs.find(t => t.key === activeTab)) {
    setActiveTab(visibleTabs[0].key);
  }

  return (
    <div className="bg-slate-900 rounded-2xl border border-slate-800 p-6">
      <h3 className="text-slate-400 text-sm font-medium uppercase tracking-wider mb-4">
        Extracted Content
      </h3>

      {/* Tab bar */}
      <div className="flex gap-1 mb-4 bg-slate-800/50 rounded-lg p-1">
        {visibleTabs.map(tab => (
          <button
            key={tab.key}
            className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all ${
              activeTab === tab.key
                ? 'bg-slate-700 text-white'
                : 'text-slate-400 hover:text-slate-300'
            }`}
            onClick={() => setActiveTab(tab.key)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="min-h-[100px]">
        {activeTab === 'text' && hasText && (
          <pre className="text-sm text-slate-300 whitespace-pre-wrap font-mono bg-slate-800/50 rounded-lg p-4 max-h-64 overflow-y-auto">
            {texts}
          </pre>
        )}

        {activeTab === 'urls' && hasUrls && (
          <div className="space-y-2">
            {urls!.map((url, i) => (
              <div key={i} className="flex items-center gap-2 bg-slate-800/50 rounded-lg px-4 py-2">
                <span className="text-amber-400 shrink-0">⚠️</span>
                <span className="text-sm text-slate-300 font-mono break-all">{url}</span>
              </div>
            ))}
            <p className="text-xs text-slate-500 mt-2 italic">
              ⚠ Exercise caution — these URLs were extracted from potentially suspicious content.
            </p>
          </div>
        )}

        {activeTab === 'entities' && hasEntities && (
          <div className="space-y-3">
            {emails && emails.length > 0 && (
              <div>
                <span className="text-xs text-slate-500 uppercase tracking-wider">Emails</span>
                <div className="flex flex-wrap gap-2 mt-1">
                  {emails.map((e, i) => (
                    <span key={i} className="px-2 py-1 text-xs bg-slate-800 rounded border border-slate-700 text-slate-300 font-mono">
                      {e}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {phones && phones.length > 0 && (
              <div>
                <span className="text-xs text-slate-500 uppercase tracking-wider">Phone Numbers</span>
                <div className="flex flex-wrap gap-2 mt-1">
                  {phones.map((p, i) => (
                    <span key={i} className="px-2 py-1 text-xs bg-slate-800 rounded border border-slate-700 text-slate-300 font-mono">
                      {p}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'metadata' && hasMetadata && (
          <div className="bg-slate-800/50 rounded-lg p-4">
            <table className="w-full text-sm">
              <tbody>
                {Object.entries(metadata!).map(([key, val]) => (
                  <tr key={key} className="border-b border-slate-700/30 last:border-0">
                    <td className="py-1.5 pr-4 text-slate-500 font-mono text-xs whitespace-nowrap">{key}</td>
                    <td className="py-1.5 text-slate-300 text-xs break-all">{String(val)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
