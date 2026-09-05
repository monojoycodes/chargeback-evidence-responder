import React from 'react';
import { ArrowDown, Shield, Sparkles, TrendingUp, Sliders, CheckCircle2 } from 'lucide-react';

export default function HeroSection({ onExploreQueue, onOpenSimulator, stats }) {
  return (
    <section className="relative overflow-hidden bg-gradient-to-b from-blue-50/60 via-slate-50/30 to-white pt-12 pb-16 border-b border-slate-200">
      {/* Decorative subtle background elements */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-7xl h-96 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-blue-200/25 via-transparent to-transparent pointer-events-none -z-10" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col items-center text-center">
        
        {/* Top Centered Pill Badge */}
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white border border-slate-200 shadow-sm mb-6">
          <span className="flex h-2 w-2 rounded-full bg-[#0C66E4]" />
          <span className="text-xs font-bold tracking-wider uppercase text-slate-800">
            Autonomous Chargeback Defense
          </span>
        </div>

        {/* Lowercase Bold Hero Headline (Matches Reference Image 1) */}
        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-[#0C2340] max-w-4xl leading-[1.1] mb-6">
          turn dispute losses <br />
          <span className="bg-gradient-to-r from-[#0C66E4] via-blue-600 to-indigo-600 bg-clip-text text-transparent">
            into recovered margin
          </span>
        </h1>

        {/* Tracked Uppercase Subtitle (Matches Reference Image 1) */}
        <p className="text-xs sm:text-sm font-semibold tracking-widest text-slate-500 uppercase max-w-2xl leading-relaxed mb-8">
          AUTONOMOUS CHARGEBACK VERIFIER & AUTO-RESPONDER. SYSTEM A GATES BY FINANCIAL EXPECTED VALUE. SYSTEM B ASSEMBLES 4-PAGE BANK-COMPLIANT PACKAGES.
        </p>

        {/* CTA Button Row flanked by subtle divider lines */}
        <div className="w-full max-w-md flex items-center justify-center gap-4 mb-12">
          <div className="h-[1px] flex-1 bg-gradient-to-r from-transparent to-slate-300" />
          <div className="flex items-center gap-3">
            <button
              onClick={onExploreQueue}
              className="px-6 py-3 rounded-xl bg-[#0C2340] hover:bg-[#0C66E4] text-white text-sm font-semibold shadow-lg shadow-blue-900/15 hover:shadow-blue-600/25 transition-all flex items-center gap-2 group cursor-pointer"
            >
              <span>Explore Live Disputes</span>
              <ArrowDown className="w-4 h-4 group-hover:translate-y-0.5 transition-transform" />
            </button>
            <button
              onClick={onOpenSimulator}
              className="px-5 py-3 rounded-xl bg-white hover:bg-slate-50 text-slate-700 text-sm font-semibold border border-slate-200 shadow-sm transition-all flex items-center gap-2 cursor-pointer"
            >
              <Sliders className="w-4 h-4 text-[#0C66E4]" />
              <span>What-If Simulator</span>
            </button>
          </div>
          <div className="h-[1px] flex-1 bg-gradient-to-l from-transparent to-slate-300" />
        </div>

        {/* Floating Hero Preview Container (Mirrors Bottom Peek in Reference Image 1) */}
        <div className="w-full max-w-5xl rounded-2xl bg-white/95 p-4 sm:p-6 border border-slate-200/80 shadow-2xl shadow-slate-900/5 card-elevation text-left">
          <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-100 mb-5">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-blue-50 border border-blue-200 flex items-center justify-center text-[#0C66E4]">
                <Shield className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-900">Held-Out Test Set Operational Summary</h3>
                <p className="text-xs text-slate-500">Evaluated on 1,500 unobserved chargeback cases</p>
              </div>
            </div>
            <div className="flex items-center gap-2 text-xs">
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-emerald-50 text-emerald-700 font-semibold border border-emerald-200">
                <CheckCircle2 className="w-3.5 h-3.5" />
                Zero Fake Accuracy
              </span>
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-blue-50 text-[#0C66E4] font-semibold border border-blue-200">
                <Sparkles className="w-3.5 h-3.5" />
                Option B Contradiction Audited
              </span>
            </div>
          </div>

          {/* Quick Metrics Bar */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="p-3.5 rounded-xl bg-slate-50/70 border border-slate-100">
              <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Held-out PR-AUC</div>
              <div className="text-2xl font-black text-slate-900 mt-1">0.8147</div>
              <div className="text-[11px] text-emerald-600 font-medium mt-0.5">+0.5647 over baseline</div>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-50/70 border border-slate-100">
              <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Decision Precision</div>
              <div className="text-2xl font-black text-slate-900 mt-1">72.93%</div>
              <div className="text-[11px] text-slate-500 font-medium mt-0.5">When fighting, wins 73%</div>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-50/70 border border-slate-100">
              <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Decision Recall</div>
              <div className="text-2xl font-black text-slate-900 mt-1">71.15%</div>
              <div className="text-[11px] text-slate-500 font-medium mt-0.5">Captures winnable volume</div>
            </div>

            <div className="p-3.5 rounded-xl bg-emerald-50/50 border border-emerald-100">
              <div className="text-[11px] font-bold text-emerald-700 uppercase tracking-wider">Net Margin Added</div>
              <div className="text-2xl font-black text-emerald-700 mt-1">+₹381,448</div>
              <div className="text-[11px] text-emerald-600 font-medium mt-0.5">vs. Blind "Fight All"</div>
            </div>
          </div>
        </div>

      </div>
    </section>
  );
}
