import React from 'react';
import { ShieldCheck, Layers, LayoutDashboard, PlayCircle, ArrowRight } from 'lucide-react';

export default function Navbar({ activePage, setActivePage }) {
  return (
    <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-md border-b border-slate-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        
        {/* Brand Name (Minimalist, no Razorpay logo) */}
        <div 
          onClick={() => setActivePage('landing')}
          className="flex items-center gap-2.5 cursor-pointer select-none"
        >
          <div className="w-8 h-8 rounded-lg bg-[#0C66E4] flex items-center justify-center text-white shadow-xs">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <span className="font-extrabold text-slate-900 tracking-tight text-base">
              AI Chargeback Responder
            </span>
          </div>
        </div>

        {/* Center Page Switcher Pills */}
        <nav className="flex items-center gap-1 bg-slate-100 p-1 rounded-xl border border-slate-200 text-xs">
          <button
            onClick={() => setActivePage('landing')}
            className={`px-3.5 py-1.5 rounded-lg font-semibold transition-all cursor-pointer ${
              activePage === 'landing'
                ? 'bg-white text-slate-900 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Overview
          </button>
          <button
            onClick={() => setActivePage('dashboard')}
            className={`px-3.5 py-1.5 rounded-lg font-semibold transition-all flex items-center gap-1 cursor-pointer ${
              activePage === 'dashboard'
                ? 'bg-white text-slate-900 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <LayoutDashboard className="w-3.5 h-3.5 text-slate-400" />
            Dashboard
          </button>
          <button
            onClick={() => setActivePage('flow')}
            className={`px-3.5 py-1.5 rounded-lg font-semibold transition-all flex items-center gap-1 cursor-pointer ${
              activePage === 'flow'
                ? 'bg-[#0C66E4] text-white shadow-xs'
                : 'text-slate-700 hover:text-slate-900'
            }`}
          >
            <PlayCircle className="w-3.5 h-3.5" />
            Test System Flow
          </button>
          <button
            onClick={() => setActivePage('about')}
            className={`px-3.5 py-1.5 rounded-lg font-semibold transition-all cursor-pointer ${
              activePage === 'about'
                ? 'bg-white text-slate-900 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            About
          </button>
        </nav>

        {/* Right Action / Status */}
        <div className="hidden sm:flex items-center gap-3">
          <button
            onClick={() => setActivePage('flow')}
            className="px-3.5 py-1.5 rounded-xl bg-slate-900 hover:bg-[#0C66E4] text-white text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer shadow-xs"
          >
            <span>Live Flow Demo</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

      </div>
    </header>
  );
}
