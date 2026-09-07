export default function Footer() {
  return (
    <footer className="w-full py-6 bg-slate-950 border-t border-slate-900 mt-auto">
      <div className="container mx-auto px-4 flex flex-col md:flex-row justify-between items-center text-xs text-slate-500">
        <div className="mb-4 md:mb-0">
          <p className="font-semibold text-slate-400 mb-1">SentriX Framework</p>
          <p>AI-based risk assessment, not definitive proof of fraud.</p>
        </div>
        <div className="flex space-x-6">
          <a href="#" className="hover:text-cyan-400 transition-colors">Documentation</a>
          <a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer" className="hover:text-cyan-400 transition-colors">API</a>
          <a href="https://github.com/gbyGaurav/SentriX-AI" target="_blank" rel="noopener noreferrer" className="hover:text-cyan-400 transition-colors">GitHub</a>
        </div>
      </div>
    </footer>
  );
}
