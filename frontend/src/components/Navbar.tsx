'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function Navbar() {
  const pathname = usePathname();

  return (
    <nav className="fixed top-0 w-full z-50 bg-slate-950/80 backdrop-blur-md border-b border-slate-800">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center space-x-2">
          <div className="w-8 h-8 rounded bg-gradient-to-br from-cyan-500 to-emerald-500 flex items-center justify-center font-bold text-white shadow-[0_0_15px_rgba(6,182,212,0.5)]">
            S
          </div>
          <span className="font-semibold text-xl tracking-wide text-white">SentriX</span>
        </Link>
        <div className="flex space-x-6">
          <Link 
            href="/" 
            className={`text-sm font-medium transition-colors ${pathname === '/' ? 'text-cyan-400' : 'text-slate-400 hover:text-white'}`}
          >
            Analyze
          </Link>
          <Link 
            href="/history" 
            className={`text-sm font-medium transition-colors ${pathname === '/history' ? 'text-cyan-400' : 'text-slate-400 hover:text-white'}`}
          >
            History
          </Link>
        </div>
      </div>
    </nav>
  );
}
