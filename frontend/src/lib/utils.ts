import { RiskLevel, InputType } from '../types';

export function getRiskColor(level: RiskLevel): string {
  switch (level) {
    case 'SAFE': return 'text-emerald-400';
    case 'LOW': return 'text-yellow-400';
    case 'MEDIUM': return 'text-orange-400';
    case 'HIGH': return 'text-red-500';
    case 'CRITICAL': return 'text-rose-600';
    default: return 'text-slate-400';
  }
}

export function getRiskBgColor(level: RiskLevel): string {
  switch (level) {
    case 'SAFE': return 'bg-emerald-400/20 text-emerald-400 border-emerald-400/50';
    case 'LOW': return 'bg-yellow-400/20 text-yellow-400 border-yellow-400/50';
    case 'MEDIUM': return 'bg-orange-400/20 text-orange-400 border-orange-400/50';
    case 'HIGH': return 'bg-red-500/20 text-red-500 border-red-500/50';
    case 'CRITICAL': return 'bg-rose-600/20 text-rose-600 border-rose-600/50';
    default: return 'bg-slate-800 text-slate-400 border-slate-700';
  }
}

export function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString(undefined, {
    year: 'numeric', month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit'
  });
}

export function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(2)}s`;
}

export function getInputTypeIcon(type: InputType): string {
  switch (type) {
    case 'URL': return '🌐';
    case 'QR': return '📱';
    case 'IMAGE': return '🖼️';
    case 'VIDEO': return '🎬';
    case 'PDF': return '📄';
    case 'DOCUMENT': return '📝';
    case 'AUDIO': return '🎵';
    case 'TEXT': return '💬';
    case 'EMAIL': return '📧';
    default: return '❓';
  }
}

export function getInputTypeLabel(type: InputType): string {
  switch (type) {
    case 'URL': return 'URL / Link';
    case 'QR': return 'QR Code';
    case 'IMAGE': return 'Image File';
    case 'VIDEO': return 'Video File';
    case 'PDF': return 'PDF Document';
    case 'DOCUMENT': return 'Document File';
    case 'AUDIO': return 'Audio File';
    case 'TEXT': return 'Raw Text';
    case 'EMAIL': return 'Email Message';
    default: return 'Unknown Input';
  }
}
