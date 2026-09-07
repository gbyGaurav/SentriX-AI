'use client';

import { useEffect, useState } from 'react';

export default function AnalysisProgress({ progress }: { progress: number }) {
  const steps = [
    'Detecting input type...',
    'Extracting evidence...',
    'Running fraud models...',
    'Combining results...',
    'Generating intelligence...'
  ];

  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    if (progress < 20) setCurrentStep(0);
    else if (progress < 40) setCurrentStep(1);
    else if (progress < 60) setCurrentStep(2);
    else if (progress < 80) setCurrentStep(3);
    else if (progress < 100) setCurrentStep(4);
    else setCurrentStep(5);
  }, [progress]);

  return (
    <div className="w-full max-w-md mx-auto bg-slate-900 rounded-xl p-6 border border-slate-800 shadow-2xl">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-white">Analyzing Input</h3>
        <span className="text-cyan-400 font-mono">{progress}%</span>
      </div>
      
      {/* Progress Bar */}
      <div className="w-full h-2 bg-slate-800 rounded-full mb-8 overflow-hidden">
        <div 
          className="h-full bg-gradient-to-r from-cyan-500 to-emerald-500 transition-all duration-500 ease-out rounded-full"
          style={{ width: `${progress}%` }}
        />
      </div>

      <div className="space-y-4">
        {steps.map((step, index) => {
          const isComplete = currentStep > index;
          const isActive = currentStep === index;
          
          return (
            <div key={index} className="flex items-center space-x-3">
              <div className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 ${
                isComplete ? 'bg-emerald-500/20 text-emerald-400' :
                isActive ? 'bg-cyan-500/20 text-cyan-400 animate-pulse' :
                'bg-slate-800 text-slate-500'
              }`}>
                {isComplete ? (
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                ) : isActive ? (
                  <div className="w-2 h-2 bg-cyan-400 rounded-full animate-ping" />
                ) : (
                  <div className="w-1.5 h-1.5 bg-slate-500 rounded-full" />
                )}
              </div>
              <span className={`text-sm ${
                isComplete ? 'text-emerald-400/80' :
                isActive ? 'text-white' :
                'text-slate-500'
              }`}>
                {step}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
