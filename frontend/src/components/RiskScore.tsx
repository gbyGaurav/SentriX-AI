'use client';

import { useEffect, useState } from 'react';
import { RiskLevel } from '../types';
import { getRiskColor } from '../lib/utils';

interface RiskScoreProps {
  score: number;
  level: RiskLevel;
  confidence: number;
}

export default function RiskScore({ score, level, confidence }: RiskScoreProps) {
  const [animatedScore, setAnimatedScore] = useState(0);
  const size = 200;
  const strokeWidth = 12;
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  
  useEffect(() => {
    // Animate from 0 to actual score on mount
    const timeout = setTimeout(() => {
      setAnimatedScore(score);
    }, 100);
    return () => clearTimeout(timeout);
  }, [score]);
  
  const strokeDashoffset = circumference - (animatedScore / 100) * circumference;
  
  // Map level to a tailwind color for the SVG stroke (using hardcoded colors for SVG)
  const getStrokeColor = (level: RiskLevel) => {
    switch(level) {
      case 'SAFE': return '#34d399'; // emerald-400
      case 'LOW': return '#facc15'; // yellow-400
      case 'MEDIUM': return '#fb923c'; // orange-400
      case 'HIGH': return '#ef4444'; // red-500
      case 'CRITICAL': return '#e11d48'; // rose-600
      default: return '#94a3b8'; // slate-400
    }
  };

  const colorClass = getRiskColor(level);
  
  return (
    <div className="relative flex flex-col items-center justify-center p-6 bg-slate-900 rounded-2xl border border-slate-800 shadow-xl">
      <h3 className="text-slate-400 text-sm font-medium uppercase tracking-wider mb-4">Overall Risk Score</h3>
      
      <div className="relative" style={{ width: size, height: size }}>
        {/* Background circle */}
        <svg className="transform -rotate-90 w-full h-full">
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="currentColor"
            strokeWidth={strokeWidth}
            className="text-slate-800"
          />
          {/* Progress circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={getStrokeColor(level)}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            className="transition-all duration-1000 ease-out"
          />
        </svg>
        
        {/* Center text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={`text-5xl font-bold ${colorClass}`}>
            {Math.round(animatedScore)}
          </span>
          <span className="text-slate-500 text-sm mt-1">/ 100</span>
        </div>
      </div>
      
      <div className="mt-6 text-center">
        <div className={`text-xl font-bold tracking-wide uppercase ${colorClass}`}>
          {level} RISK
        </div>
        <div className="text-slate-400 text-sm mt-1">
          {Math.round(confidence * 100)}% Confidence
        </div>
      </div>
    </div>
  );
}
