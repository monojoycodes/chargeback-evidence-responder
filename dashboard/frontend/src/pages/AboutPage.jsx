import React from 'react';
import { ShieldCheck, Scale, Cpu, FileText, CheckCircle2, AlertTriangle, ArrowRight, TrendingUp } from 'lucide-react';

export default function AboutPage({ onNavigateToFlow }) {
  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-16 pb-24">
      {/* Header */}
      <div className="text-center max-w-3xl mx-auto space-y-3">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-50 border border-blue-200 text-[#0C66E4] text-xs font-semibold">
          <span>About the System</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-black text-[#0C2340] tracking-tight">
          How Intelligent Chargeback Defense Works
        </h1>
        <p className="text-sm text-slate-600 leading-relaxed font-normal">
          Designed to eliminate margin loss from invalid cardholder disputes while protecting merchants from wasted dispute processing fees.
        </p>
      </div>

      {/* The Core Problem */}
      <section className="bg-white rounded-2xl border border-slate-200 p-8 shadow-xs space-y-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-amber-50 border border-amber-200 text-amber-700 flex items-center justify-center">
            <AlertTriangle className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-slate-900">The Problem: The Margin Drain of Payment Disputes</h2>
            <p className="text-xs text-slate-500">Why standard chargeback handling hurts merchant profitability</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5 text-xs text-slate-600 leading-relaxed">
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-100 space-y-2">
            <div className="font-bold text-slate-900 text-sm">1. The Representment Fee Trap</div>
            <p>
              When a merchant contests a chargeback and loses, card networks levy non-refundable fees (ranging from ₹300 on UPI up to ₹1,700 on card schemes). Blindly contesting a ₹400 dispute with a ₹1,700 fee penalty guarantees negative unit economics.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 border border-slate-100 space-y-2">
            <div className="font-bold text-slate-900 text-sm">2. The Passive Concede Drain</div>
            <p>
              Surrendering disputes forfeits 100% of the sale value and physical inventory. On legitimately fulfilled orders where the buyer authenticated via 3DS or signed for delivery, conceding blindly costs businesses 1–3% of top-line revenue.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 border border-slate-100 space-y-2">
            <div className="font-bold text-slate-900 text-sm">3. The Self-Incrimination Trap</div>
            <p>
              Merchants frequently attach unreviewed support transcripts where an agent wrote "sorry for the delay" or offered a replacement. Card issuers inspect these records, cite the admission, and dismiss the merchant's claim immediately.
            </p>
          </div>
        </div>
      </section>

      {/* Two-Tier Architecture */}
      <section className="space-y-6">
        <div className="text-center">
          <h2 className="text-xs uppercase font-bold tracking-widest text-slate-400">System Architecture</h2>
          <p className="text-xl font-bold text-slate-900 mt-1">Two Specialized Decision &amp; Assembly Layers</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* System A Card */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-blue-50 text-[#0C66E4] flex items-center justify-center font-bold text-sm">
                  A
                </div>
                <div>
                  <h3 className="text-base font-bold text-slate-900">System A: Pre-Fight Financial Gating</h3>
                  <p className="text-xs text-slate-500">Calibrated ML &amp; Expected Value Optimization</p>
                </div>
              </div>
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-blue-50 text-blue-700 border border-blue-200">
                Decision Gating
              </span>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed">
              Trained on 30 merchant fulfillment signals with 5-fold Isotonic Probability Calibration.
              Calculates net expected recovery before any representment is initiated:
            </p>

            <div className="p-3 rounded-xl bg-slate-900 text-white font-mono text-xs space-y-1">
              <div className="text-slate-400 text-[10px] uppercase font-sans font-bold">The Optimization Formula</div>
              <div className="text-blue-300">Net EV = (P(win) × Dispute Amount) − ((1 − P(win)) × Loss Fee)</div>
              <div className="text-slate-400 text-[11px] pt-1">
                Rule: <span className="text-emerald-400 font-bold">FIGHT</span> if Net EV &gt; 0, otherwise <span className="text-slate-300 font-bold">CONCEDE</span> immediately.
              </div>
            </div>

            <div className="text-xs text-slate-700 space-y-1 pt-1">
              <div className="flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span><strong>0.8147 PR-AUC</strong> on held-out test data (+0.56 vs base)</span>
              </div>
              <div className="flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span><strong>72.93% Win Precision</strong> (contests only when mathematically profitable)</span>
              </div>
            </div>
          </div>

          {/* System B Card */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-700 flex items-center justify-center font-bold text-sm">
                  B
                </div>
                <div>
                  <h3 className="text-base font-bold text-slate-900">System B: Evidence Audit &amp; Response Packets</h3>
                  <p className="text-xs text-slate-500">Document Audit &amp; Bank-Ready PDF Compilation</p>
                </div>
              </div>
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                Defense Assembly
              </span>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed">
              Processes evidence for high-value cases. Generates legal rebuttals referencing 29 payment network reason codes
              (Visa Core Rules, Mastercard MasterCom, and NPCI UPI Guidelines).
            </p>

            <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs space-y-2">
              <div className="font-bold text-slate-800 flex items-center gap-1">
                <Scale className="w-3.5 h-3.5 text-[#0C66E4]" />
                Evidence Contradiction Filter
              </div>
              <p className="text-[11px] text-slate-600 leading-relaxed">
                Scans internal ERP records and customer chat strings. If conflicting statements (e.g. admitted fulfillment delays or unissued refunds)
                are detected, they are safely excluded from the bank packet.
              </p>
            </div>

            <div className="text-xs text-slate-700 space-y-1 pt-1">
              <div className="flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span><strong>3-Page Formal Dossier</strong>: Cover Letter + Commercial Invoice + Category Proof</span>
              </div>
              <div className="flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span><strong>100% Decoupled</strong>: Internal AI metrics and EV numbers omitted from bank packets</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Empirical Benchmark Results */}
      <section className="bg-white rounded-2xl border border-slate-200 p-8 shadow-xs space-y-6">
        <h2 className="text-lg font-bold text-slate-900">Verified Results on Held-Out Test Data</h2>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-100">
            <div className="text-2xl font-black text-slate-900">0.8147</div>
            <div className="text-[11px] text-slate-500 font-medium mt-1">PR-AUC (+0.56 vs base)</div>
          </div>
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-100">
            <div className="text-2xl font-black text-slate-900">0.3732</div>
            <div className="text-[11px] text-slate-500 font-medium mt-1">Brier Skill Score</div>
          </div>
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-100">
            <div className="text-2xl font-black text-slate-900">72.93%</div>
            <div className="text-[11px] text-slate-500 font-medium mt-1">Decision Precision</div>
          </div>
          <div className="p-4 rounded-xl bg-emerald-50/70 border border-emerald-200">
            <div className="text-2xl font-black text-emerald-700">+₹381,448</div>
            <div className="text-[11px] text-emerald-700 font-bold mt-1">Margin Preserved vs Fight All</div>
          </div>
        </div>
      </section>

      {/* Call to Action */}
      <div className="text-center pt-4">
        <button
          onClick={onNavigateToFlow}
          className="px-6 py-3 rounded-xl bg-[#0C66E4] hover:bg-blue-700 text-white font-semibold text-sm shadow-md shadow-blue-500/20 transition-all inline-flex items-center gap-2 cursor-pointer"
        >
          <span>Test the System Flow Step-by-Step</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
