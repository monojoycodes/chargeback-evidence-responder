import React, { useState, useEffect } from 'react';
import { Sliders, CheckCircle2, XCircle, TrendingUp, AlertTriangle, RefreshCw } from 'lucide-react';

export default function WhatIfSimulator() {
  const [amount, setAmount] = useState(4500);
  const [winProb, setWinProb] = useState(0.65);
  const [fee, setFee] = useState(1200);
  const [simResult, setSimResult] = useState(null);

  const calculateEV = () => {
    fetch('/api/simulate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        dispute_amount_inr: amount,
        predicted_win_prob: winProb,
        false_positive_cost_inr: fee,
      }),
    })
      .then((r) => r.json())
      .then((data) => setSimResult(data))
      .catch((err) => console.error('Simulation error:', err));
  };

  useEffect(() => {
    calculateEV();
  }, [amount, winProb, fee]);

  const isFight = simResult && simResult.expected_value > 0;

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 rounded-xl bg-blue-50 text-[#0C66E4]">
            <Sliders className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-900">Interactive Expected Value (EV) Simulator</h2>
            <p className="text-xs text-slate-500">
              Test how changes in Dispute Amount, Win Probability, and Network Representment Fees alter the AI decision threshold:
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mt-6">
          {/* SLIDERS COLUMN */}
          <div className="lg:col-span-2 space-y-6">
            {/* Slider 1: Dispute Amount */}
            <div className="space-y-2">
              <div className="flex justify-between items-center text-xs">
                <label className="font-bold text-slate-700">Dispute Amount (INR)</label>
                <span className="font-mono font-bold text-[#0C66E4] text-sm">₹{amount.toLocaleString('en-IN')}</span>
              </div>
              <input
                type="range"
                min="200"
                max="50000"
                step="100"
                value={amount}
                onChange={(e) => setAmount(Number(e.target.value))}
                className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-[#0C66E4]"
              />
              <div className="flex justify-between text-[10px] text-slate-400 font-mono">
                <span>₹200 (Micro-txn)</span>
                <span>₹10,000 (Average Retail)</span>
                <span>₹50,000 (High-Ticket)</span>
              </div>
            </div>

            {/* Slider 2: Win Probability */}
            <div className="space-y-2">
              <div className="flex justify-between items-center text-xs">
                <label className="font-bold text-slate-700">Predicted Win Probability P(win)</label>
                <span className="font-mono font-bold text-emerald-600 text-sm">{(winProb * 100).toFixed(0)}%</span>
              </div>
              <input
                type="range"
                min="0.05"
                max="0.95"
                step="0.01"
                value={winProb}
                onChange={(e) => setWinProb(Number(e.target.value))}
                className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-emerald-600"
              />
              <div className="flex justify-between text-[10px] text-slate-400 font-mono">
                <span>5% (Missing Proof)</span>
                <span>50% (Equivocal)</span>
                <span>95% (3DS ECI 05 + POD OTP)</span>
              </div>
            </div>

            {/* Slider 3: Network Representment Fee */}
            <div className="space-y-2">
              <div className="flex justify-between items-center text-xs">
                <label className="font-bold text-slate-700">Network False Positive Fee (Cost of Losing)</label>
                <span className="font-mono font-bold text-amber-600 text-sm">₹{fee.toLocaleString('en-IN')}</span>
              </div>
              <input
                type="range"
                min="300"
                max="2500"
                step="50"
                value={fee}
                onChange={(e) => setFee(Number(e.target.value))}
                className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-amber-600"
              />
              <div className="flex justify-between text-[10px] text-slate-400 font-mono">
                <span>₹300 (UPI / RuPay)</span>
                <span>₹1,200 (Visa Standard)</span>
                <span>₹1,700 (Mastercard / Amex)</span>
              </div>
            </div>

            {/* Preset Fee Quick Select Buttons */}
            <div className="flex items-center gap-2 pt-2 border-t border-slate-100">
              <span className="text-[11px] font-bold text-slate-400">Quick Fee Rails:</span>
              <button
                onClick={() => setFee(300)}
                className={`px-2.5 py-1 rounded text-xs font-semibold border cursor-pointer ${
                  fee === 300 ? 'bg-emerald-50 text-emerald-700 border-emerald-300' : 'bg-slate-50 text-slate-600 border-slate-200'
                }`}
              >
                UPI / RuPay (₹300)
              </button>
              <button
                onClick={() => setFee(1200)}
                className={`px-2.5 py-1 rounded text-xs font-semibold border cursor-pointer ${
                  fee === 1200 ? 'bg-blue-50 text-blue-700 border-blue-300' : 'bg-slate-50 text-slate-600 border-slate-200'
                }`}
              >
                Cards Mid (₹1,200)
              </button>
              <button
                onClick={() => setFee(1700)}
                className={`px-2.5 py-1 rounded text-xs font-semibold border cursor-pointer ${
                  fee === 1700 ? 'bg-amber-50 text-amber-700 border-amber-300' : 'bg-slate-50 text-slate-600 border-slate-200'
                }`}
              >
                Cards Premium (₹1,700)
              </button>
            </div>
          </div>

          {/* DYNAMIC DECISION & EV CARD */}
          <div className="flex flex-col justify-between p-5 rounded-2xl bg-slate-50 border border-slate-200/90 shadow-sm">
            <div>
              <div className="text-[10px] uppercase font-bold text-slate-400 tracking-wider mb-1">
                Mathematical Decision Threshold
              </div>
              
              <div className="mb-4">
                {isFight ? (
                  <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-600 text-white font-extrabold text-sm shadow-sm">
                    <CheckCircle2 className="w-4 h-4" />
                    FIGHT DISPUTE
                  </div>
                ) : (
                  <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-700 text-white font-extrabold text-sm shadow-sm">
                    <XCircle className="w-4 h-4" />
                    CONCEDE DISPUTE
                  </div>
                )}
              </div>

              <div className="space-y-3">
                <div className="p-3 rounded-xl bg-white border border-slate-200/80">
                  <div className="text-[10px] uppercase font-bold text-slate-400">Expected Value (EV)</div>
                  <div className={`text-2xl font-black mt-0.5 ${isFight ? 'text-emerald-700' : 'text-slate-500'}`}>
                    {simResult ? (simResult.expected_value > 0 ? '+' : '') + `₹${simResult.expected_value.toLocaleString('en-IN')}` : '...'}
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-white border border-slate-200/80">
                  <div className="text-[10px] uppercase font-bold text-slate-400">Break-Even Win Probability</div>
                  <div className="text-sm font-black text-slate-900 mt-0.5">
                    {simResult ? `${simResult.break_even_prob_pct}%` : '...'}
                  </div>
                  <p className="text-[10px] text-slate-500 mt-0.5">Below this probability, fighting loses money.</p>
                </div>
              </div>
            </div>

            <div className="pt-4 border-t border-slate-200 text-xs text-slate-600 space-y-1">
              <div className="flex justify-between">
                <span>Gross Recovery Expectation:</span>
                <span className="font-bold text-emerald-700 font-mono">
                  +₹{simResult ? simResult.potential_recovery.toLocaleString('en-IN') : '0'}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Fee Loss Exposure:</span>
                <span className="font-bold text-amber-700 font-mono">
                  −₹{simResult ? simResult.risk_loss_exposure.toLocaleString('en-IN') : '0'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
