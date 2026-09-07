'use client';

import UploadZone from '../components/UploadZone';

export default function Home() {
  return (
    <div className="container mx-auto px-4 py-12 flex flex-col items-center justify-center min-h-[calc(100vh-8rem)]">
      <div className="text-center mb-10">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-950/60 border border-cyan-500/30 text-cyan-400 text-xs font-semibold mb-4 tracking-wider uppercase">
          AI-Powered Threat Defense
        </div>
        <h1 className="text-4xl md:text-5xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 via-teal-300 to-emerald-400 mb-4 tracking-tight">
          SentriX
        </h1>
        <p className="text-xl text-slate-200 font-medium max-w-2xl mx-auto mb-2">
          Unified Multimodal Fraud Intelligence Framework
        </p>
        <p className="text-slate-400 max-w-2xl mx-auto text-sm">
          Autonomous multi-vector detection analyzing URLs, documents, images, video, text, and QR codes to uncover sophisticated fraud patterns.
        </p>
      </div>

      <div className="w-full max-w-4xl">
        <UploadZone />
      </div>
    </div>
  );
}
