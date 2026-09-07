import { RiskLevel } from '../types';
import { getRiskBgColor } from '../lib/utils';

export default function RiskBadge({ level, className = '' }: { level: RiskLevel, className?: string }) {
  const colorClass = getRiskBgColor(level);
  
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${colorClass} ${className}`}>
      {level}
    </span>
  );
}
