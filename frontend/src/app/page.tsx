'use client';

import UploadZone from '../components/UploadZone';

export default function Home() {
  return (
    <div className="container mx-auto px-4 py-12 flex flex-col items-center justify-center min-h-[calc(100vh-8rem)]">
      <div className="text-center mb-10">
        <h1 className="text-4xl md:text-5xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 to-emerald-400 mb-4 tracking-tight">
          Unified AI Multimodal Fraud Intelligence
        </h1>
        <p className="text-slate-400 max-w-2xl mx-auto text-lg">
          Advanced detection framework analyzing URLs, documents, images, text, and multimedia to uncover sophisticated fraud patterns.
        </p>
      </div>

      <div className="w-full max-w-4xl">
        <UploadZone />
      </div>
    </div>
  );
}
