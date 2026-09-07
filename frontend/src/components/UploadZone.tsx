'use client';

import { useState, useRef, DragEvent, ChangeEvent, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAnalysis } from '../hooks/useAnalysis';
import AnalysisProgress from './AnalysisProgress';

export default function UploadZone() {
  const router = useRouter();
  const { isAnalyzing, progress, error, submitFile, submitText, submitUrl } = useAnalysis();
  
  const [dragActive, setDragActive] = useState(false);
  const [textInput, setTextInput] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = async (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      setSelectedFile(file);
      await processFile(file);
    }
  };

  const handleChange = async (e: ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      await processFile(file);
    }
  };

  const processFile = async (file: File) => {
    const res = await submitFile(file);
    const targetId = res?.analysis_id || res?.id;
    if (targetId) {
      router.push(`/analysis/${targetId}`);
    }
  };

  const handleTextSubmit = async () => {
    if (!textInput.trim()) return;
    
    const isUrl = /^(https?:\/\/|[a-z0-9]+([\-\.]{1}[a-z0-9]+)*\.[a-z]{2,5}(:[0-9]{1,5})?(\/.*)?$)/i.test(textInput.trim());
    
    const res = isUrl ? await submitUrl(textInput.trim()) : await submitText(textInput);
    const targetId = res?.analysis_id || res?.id;
    if (targetId) {
      router.push(`/analysis/${targetId}`);
    }
  };

  if (isAnalyzing) {
    return (
      <div className="w-full flex justify-center py-12">
        <AnalysisProgress progress={progress} />
      </div>
    );
  }

  return (
    <div className="w-full">
      {/* File Drop Zone */}
      <div 
        className={`relative w-full h-64 md:h-80 rounded-2xl border-2 border-dashed transition-all duration-300 flex flex-col items-center justify-center cursor-pointer overflow-hidden group
          ${dragActive ? 'border-cyan-400 bg-cyan-950/20 scale-[1.02]' : 'border-slate-700 hover:border-slate-500 bg-slate-900/50 hover:bg-slate-900'}
        `}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/5 to-emerald-500/5 opacity-0 group-hover:opacity-100 transition-opacity" />
        
        <div className="z-10 flex flex-col items-center p-6 text-center">
          <div className="w-16 h-16 rounded-full bg-slate-800 flex items-center justify-center mb-4 shadow-lg group-hover:scale-110 transition-transform">
            <svg className="w-8 h-8 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <h3 className="text-xl font-medium text-white mb-2">
            Upload File for Analysis
          </h3>
          <p className="text-slate-400 text-sm max-w-xs">
            Drag & drop or click to select a file.
          </p>
          
          <div className="flex flex-wrap justify-center gap-2 mt-6">
            {['PDF', 'Image', 'Video', 'Audio', 'Doc'].map(ext => (
              <span key={ext} className="px-2 py-1 text-xs rounded-md bg-slate-800 border border-slate-700 text-slate-300">
                {ext}
              </span>
            ))}
          </div>
        </div>
        
        <input 
          ref={fileInputRef}
          type="file" 
          className="hidden" 
          onChange={handleChange}
          accept=".pdf,.jpg,.jpeg,.png,.webp,.mp4,.mov,.webm,.mp3,.wav,.m4a,.docx,.txt"
        />
      </div>

      {error && (
        <div className="mt-4 p-4 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm flex items-start">
          <svg className="w-5 h-5 mr-2 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          {error}
        </div>
      )}

      {/* Text / URL Input */}
      <div className="mt-6 flex flex-col md:flex-row gap-4">
        <input 
          type="text" 
          value={textInput}
          onChange={(e) => setTextInput(e.target.value)}
          placeholder="Or paste a URL or text here..."
          className="flex-grow bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-all"
          onKeyDown={(e) => e.key === 'Enter' && handleTextSubmit()}
        />
        <button 
          onClick={handleTextSubmit}
          disabled={!textInput.trim() || isAnalyzing}
          className="px-6 py-3 bg-cyan-600 hover:bg-cyan-500 text-white font-medium rounded-xl border border-cyan-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap shadow-lg shadow-cyan-950/50"
        >
          Analyze Text / URL
        </button>
      </div>

      {/* Quick Test Samples */}
      <div className="mt-5 pt-4 border-t border-slate-800/80">
        <span className="text-xs text-slate-500 uppercase tracking-wider block mb-2 font-medium">Quick Test Scenarios:</span>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => setTextInput('http://verify-secure-bank-login.xyz/invoice/pay?account=98124')}
            className="text-xs px-3 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-800 text-rose-300 border border-rose-900/30 hover:border-rose-500/50 transition-all flex items-center gap-1.5"
          >
            <span>🚨</span> Phishing Bank URL
          </button>
          <button
            type="button"
            onClick={() => setTextInput('URGENT: Your account will be suspended within 24 hours! Verify your password and OTP immediately to avoid legal action: http://secure-restore-bank.top')}
            className="text-xs px-3 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-800 text-amber-300 border border-amber-900/30 hover:border-amber-500/50 transition-all flex items-center gap-1.5"
          >
            <span>⚠️</span> Urgent Scam SMS
          </button>
          <button
            type="button"
            onClick={() => setTextInput('Congratulations! You have been selected as the winner of $500,000 lottery! Double your money with our guaranteed cryptocurrency returns: 0x71C8A6634C286f784e1b4b20E2333b218D5D5514')}
            className="text-xs px-3 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-800 text-orange-300 border border-orange-900/30 hover:border-orange-500/50 transition-all flex items-center gap-1.5"
          >
            <span>💰</span> Lottery / Crypto Scam
          </button>
          <button
            type="button"
            onClick={() => setTextInput('Hi Sarah, here are the meeting notes from today\'s product design review. Let me know if you have any questions.')}
            className="text-xs px-3 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-800 text-emerald-300 border border-emerald-900/30 hover:border-emerald-500/50 transition-all flex items-center gap-1.5"
          >
            <span>🛡️</span> Benign Message
          </button>
        </div>
      </div>
    </div>
  );
}
