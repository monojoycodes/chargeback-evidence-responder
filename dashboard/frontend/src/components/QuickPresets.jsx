import React from 'react';
import { Sparkles, ArrowRight, ShieldCheck, Truck, RefreshCw, AlertOctagon } from 'lucide-react';

export default function QuickPresets({ presets, onSelectPreset }) {
  const getIcon = (id) => {
    switch (id) {
      case 'preset_visa_3ds':
        return <ShieldCheck className="w-4 h-4 text-[#0C66E4]" />;
      case 'preset_upi_delivery':
        return <Truck className="w-4 h-4 text-emerald-600" />;
      case 'preset_dup_rrn':
        return <RefreshCw className="w-4 h-4 text-blue-600" />;
      case 'preset_concede_low_ev':
        return <AlertOctagon className="w-4 h-4 text-amber-600" />;
      default:
        return <Sparkles className="w-4 h-4 text-[#0C66E4]" />;
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm mb-6">
      <div className="flex items-center gap-2 mb-3">
        <div className="p-1.5 rounded-lg bg-blue-50 text-[#0C66E4]">
          <Sparkles className="w-4 h-4" />
        </div>
        <div>
          <h2 className="text-sm font-bold text-slate-900">Quick Start & Curated Scenarios</h2>
          <p className="text-xs text-slate-500">Pick a pre-configured dispute case to inspect the live decision & 4-page PDF package:</p>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {presets.map((preset) => (
          <button
            key={preset.id}
            onClick={() => onSelectPreset(preset.case_id)}
            className="text-left p-3.5 rounded-xl border border-slate-200/80 bg-slate-50/50 hover:bg-white hover:border-[#0C66E4] hover:shadow-md transition-all group cursor-pointer"
          >
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                {getIcon(preset.id)}
                <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-white border border-slate-200 text-slate-700">
                  {preset.network} • {preset.reason_code}
                </span>
              </div>
              <ArrowRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-[#0C66E4] group-hover:translate-x-0.5 transition-all" />
            </div>

            <div className="font-semibold text-xs text-slate-900 group-hover:text-[#0C66E4] transition-colors line-clamp-1">
              {preset.title}
            </div>
            <div className="text-[11px] text-slate-500 mt-1 line-clamp-2">
              {preset.subtitle}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
