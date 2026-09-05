import React from 'react';
import { ArrowUpRight, CheckCircle2, XCircle, ShieldAlert, FileText } from 'lucide-react';

export default function DisputeCard({ item, onInspect }) {
  const isFight = item.model_decision_to_fight === 1;
  const winPct = Math.round(item.predicted_win_prob * 100);

  const getNetworkColor = (network) => {
    switch (network) {
      case 'VISA':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'MASTERCARD':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'UPI_NPCI':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'RUPAY':
        return 'bg-cyan-50 text-cyan-700 border-cyan-200';
      case 'AMERICAN_EXPRESS':
        return 'bg-indigo-50 text-indigo-700 border-indigo-200';
      default:
        return 'bg-slate-50 text-slate-700 border-slate-200';
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200/90 p-5 shadow-sm hover:shadow-md hover:border-slate-300 transition-all flex flex-col justify-between group">
      <div>
        {/* Top Header Row: Category Badge & Network Tag (Matches Reference Image 2) */}
        <div className="flex items-center justify-between gap-2 mb-3">
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-md border ${getNetworkColor(item.network)}`}>
              {item.network}
            </span>
            <span className="text-[10px] font-semibold text-slate-500 bg-slate-100 px-2 py-0.5 rounded-md">
              {item.normalized_category.replace(/_/g, ' ')}
            </span>
          </div>

          <div className="text-[11px] font-bold text-slate-700 bg-slate-50 border border-slate-200 px-2 py-0.5 rounded-md">
            Code {item.reason_code}
          </div>
        </div>

        {/* Reason Code Title & IDs */}
        <h3 className="font-bold text-sm text-slate-900 line-clamp-1 mb-1 group-hover:text-[#0C66E4] transition-colors">
          {item.reason_code_title}
        </h3>
        <div className="flex items-center gap-2 text-xs text-slate-500 mb-4">
          <span className="font-mono">{item.case_id}</span>
          <span>•</span>
          <span className="font-mono truncate max-w-[100px]">{item.order_id}</span>
        </div>

        {/* Financial Metrics Grid */}
        <div className="grid grid-cols-2 gap-2.5 p-3 rounded-xl bg-slate-50/80 border border-slate-100 mb-4">
          <div>
            <div className="text-[10px] uppercase font-bold text-slate-400">Disputed Amount</div>
            <div className="text-sm font-black text-slate-900 mt-0.5">
              ₹{item.dispute_amount_inr.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </div>
          </div>
          <div>
            <div className="text-[10px] uppercase font-bold text-slate-400">Expected Value</div>
            <div className={`text-sm font-black mt-0.5 ${isFight ? 'text-emerald-700' : 'text-slate-500'}`}>
              {item.expected_value > 0 ? '+' : ''}₹{item.expected_value.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </div>
          </div>
        </div>

        {/* System A Win Probability Meter */}
        <div className="space-y-1.5 mb-4">
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-500 font-medium">System A Win Confidence</span>
            <span className="font-bold text-slate-800">{winPct}%</span>
          </div>
          <div className="w-full h-2 rounded-full bg-slate-100 overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                winPct >= 65 ? 'bg-emerald-500' : winPct >= 40 ? 'bg-blue-500' : 'bg-slate-400'
              }`}
              style={{ width: `${winPct}%` }}
            />
          </div>
        </div>
      </div>

      {/* Decision Pill & Action Button */}
      <div className="pt-3 border-t border-slate-100 flex items-center justify-between gap-2">
        <div>
          {isFight ? (
            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
              <CheckCircle2 className="w-3.5 h-3.5" />
              FIGHT (+₹{item.expected_value.toFixed(0)})
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold bg-slate-100 text-slate-600 border border-slate-200">
              <XCircle className="w-3.5 h-3.5" />
              CONCEDE
            </span>
          )}
        </div>

        <button
          onClick={() => onInspect(item.case_id)}
          className="px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-[#0C66E4] text-white text-xs font-semibold flex items-center gap-1 transition-all cursor-pointer group/btn"
        >
          <span>Inspect</span>
          <ArrowUpRight className="w-3.5 h-3.5 group-hover/btn:translate-x-0.5 group-hover/btn:-translate-y-0.5 transition-transform" />
        </button>
      </div>
    </div>
  );
}
