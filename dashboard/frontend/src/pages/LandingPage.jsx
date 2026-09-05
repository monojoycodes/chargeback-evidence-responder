import React from 'react';
import { ArrowRight, ShieldCheck, FileCheck, Sliders, TrendingUp, CheckCircle, Scale } from 'lucide-react';

export default function LandingPage({ onNavigate }) {
  return (
    <div className="space-y-16 pb-12">
      {/* Hero Section */}
      <section className="pt-12 sm:pt-16 pb-8 text-center max-w-4xl mx-auto px-4">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-blue-50 border border-blue-200 text-[#0C66E4] text-xs font-semibold mb-6">
          <span className="w-2 h-2 rounded-full bg-[#0C66E4]"></span>
          <span>Intelligent Dispute Management</span>
        </div>

        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-[#0C2340] tracking-tight leading-[1.15] mb-6">
          Fight the chargebacks you can win. <br />
          <span className="text-[#0C66E4]">Concede the ones you can't.</span>
        </h1>

        <p className="text-base sm:text-lg text-slate-600 max-w-2xl mx-auto leading-relaxed mb-8 font-normal">
          Every chargeback is a trade-off. Contesting unwinnable disputes wastes non-refundable representment fees,
          while surrendering valid claims quietly drains your margins. This system evaluates the expected recovery
          first, audits your evidence for internal contradictions, and compiles bank-ready response packages.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
          <button
            onClick={() => onNavigate('flow')}
            className="w-full sm:w-auto px-6 py-3 rounded-xl bg-[#0C66E4] hover:bg-blue-700 text-white font-semibold text-sm shadow-md shadow-blue-500/20 transition-all flex items-center justify-center gap-2 cursor-pointer"
          >
            <span>Test System Flow Live</span>
            <ArrowRight className="w-4 h-4" />
          </button>
          <button
            onClick={() => onNavigate('dashboard')}
            className="w-full sm:w-auto px-6 py-3 rounded-xl bg-white hover:bg-slate-50 text-slate-700 font-semibold text-sm border border-slate-200 transition-all cursor-pointer"
          >
            View Dispute Dashboard
          </button>
        </div>
      </section>

      {/* 3-Step Process Architecture */}
      <section className="max-w-6xl mx-auto px-4">
        <div className="text-center mb-8">
          <h2 className="text-xs uppercase font-bold tracking-widest text-slate-400">The Workflow</h2>
          <p className="text-xl font-bold text-slate-900 mt-1">From Dispute Alert to Bank Submission</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Step 1 */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm hover:shadow-md transition-shadow">
            <div className="w-10 h-10 rounded-xl bg-blue-50 text-[#0C66E4] flex items-center justify-center font-bold text-sm mb-4">
              01
            </div>
            <h3 className="text-base font-bold text-slate-900 mb-2">Pre-Fight Financial Assessment</h3>
            <p className="text-xs text-slate-600 leading-relaxed mb-4">
              Before risking a ₹1,700 network fee on a ₹300 order, the system calculates win confidence against dispute value.
              If fighting yields negative expected value, it concedes immediately to protect cash flow.
            </p>
            <div className="p-2.5 rounded-lg bg-slate-50 font-mono text-[11px] text-slate-700 border border-slate-100">
              Net Value = (Win % × Amount) − (Loss % × Fee)
            </div>
          </div>

          {/* Step 2 */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm hover:shadow-md transition-shadow">
            <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-700 flex items-center justify-center font-bold text-sm mb-4">
              02
            </div>
            <h3 className="text-base font-bold text-slate-900 mb-2">Evidence Contradiction Screen</h3>
            <p className="text-xs text-slate-600 leading-relaxed mb-4">
              Raw support transcripts often contain innocent staff notes like "delayed dispatch" that prompt card issuers to reject claims.
              The engine screens internal records and withholds conflicting notes from the bank submission.
            </p>
            <div className="p-2.5 rounded-lg bg-emerald-50/50 font-mono text-[11px] text-emerald-800 border border-emerald-100">
              Screens chats, invoices, carrier logs &amp; OTPs
            </div>
          </div>

          {/* Step 3 */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm hover:shadow-md transition-shadow">
            <div className="w-10 h-10 rounded-xl bg-slate-100 text-slate-800 flex items-center justify-center font-bold text-sm mb-4">
              03
            </div>
            <h3 className="text-base font-bold text-slate-900 mb-2">Clean Bank-Ready Dossier</h3>
            <p className="text-xs text-slate-600 leading-relaxed mb-4">
              Compiles an official legal response letter, realistic commercial tax invoice, and verified delivery or 3DS authentication logs.
              All internal model scores are decoupled so issuers receive a pristine legal draft.
            </p>
            <div className="p-2.5 rounded-lg bg-slate-50 font-mono text-[11px] text-slate-700 border border-slate-100">
              Format: Official Georgia Typography PDF
            </div>
          </div>
        </div>
      </section>

      {/* Proof Metrics */}
      <section className="max-w-5xl mx-auto px-4">
        <div className="bg-white rounded-2xl border border-slate-200 p-8 shadow-sm">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-8 text-center divide-y sm:divide-y-0 sm:divide-x divide-slate-100">
            <div className="pt-4 sm:pt-0">
              <div className="text-3xl font-black text-slate-900">72.9%</div>
              <div className="text-xs font-semibold text-slate-700 mt-1">Decision Precision</div>
              <div className="text-[11px] text-slate-400 mt-0.5">Recovery rate on contested cases</div>
            </div>
            <div className="pt-4 sm:pt-0 sm:pl-8">
              <div className="text-3xl font-black text-emerald-600">+₹381,448</div>
              <div className="text-xs font-semibold text-slate-700 mt-1">Net Margin Saved</div>
              <div className="text-[11px] text-slate-400 mt-0.5">Versus contesting every claim blindly</div>
            </div>
            <div className="pt-4 sm:pt-0 sm:pl-8">
              <div className="text-3xl font-black text-[#0C66E4]">100% Clean</div>
              <div className="text-xs font-semibold text-slate-700 mt-1">Decoupled Bank Packets</div>
              <div className="text-[11px] text-slate-400 mt-0.5">Zero internal AI scores exposed to issuers</div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
