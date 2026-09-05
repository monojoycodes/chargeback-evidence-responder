import React from 'react';
import { Search, Filter, CheckCircle2, XCircle, SlidersHorizontal } from 'lucide-react';

const NETWORKS = [
  { id: 'all', label: 'All Networks' },
  { id: 'UPI_NPCI', label: 'UPI NPCI' },
  { id: 'VISA', label: 'Visa' },
  { id: 'MASTERCARD', label: 'Mastercard' },
  { id: 'RUPAY', label: 'RuPay' },
  { id: 'AMERICAN_EXPRESS', label: 'Amex' },
];

const CATEGORIES = [
  { id: 'all', label: 'All Categories' },
  { id: 'FRAUD_UNAUTHORIZED', label: 'Unauthorized Fraud' },
  { id: 'ITEM_NOT_RECEIVED', label: 'Goods Not Received' },
  { id: 'NOT_AS_DESCRIBED', label: 'Not As Described' },
  { id: 'DUPLICATE_TRANSACTION', label: 'Duplicate Billing' },
  { id: 'SERVICE_NOT_PROVIDED', label: 'Service Not Provided' },
  { id: 'RECON_SETTLEMENT_ERROR', label: 'Recon Settlement' },
];

export default function FilterBar({
  search,
  setSearch,
  selectedNetwork,
  setSelectedNetwork,
  selectedCategory,
  setSelectedCategory,
  selectedDecision,
  setSelectedDecision,
  stats,
}) {
  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm mb-6 space-y-4">
      {/* Top Search & Decision Row */}
      <div className="flex flex-col sm:flex-row gap-3 items-center justify-between">
        {/* Search Input */}
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search Case ID, Order, Code (e.g. 10.4, 1064)..."
            className="w-full pl-9 pr-4 py-2 rounded-xl text-xs bg-slate-50 border border-slate-200 focus:outline-none focus:border-[#0C66E4] focus:bg-white text-slate-800 placeholder-slate-400 transition-all"
          />
        </div>

        {/* Decision Toggle Pills */}
        <div className="flex items-center gap-1.5 p-1 rounded-xl bg-slate-100 border border-slate-200 w-full sm:w-auto justify-center">
          <button
            onClick={() => setSelectedDecision('all')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              selectedDecision === 'all'
                ? 'bg-white text-[#0C2340] shadow-sm'
                : 'text-slate-500 hover:text-slate-900'
            }`}
          >
            All Decisions ({stats.total || 0})
          </button>
          <button
            onClick={() => setSelectedDecision('fight')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1 cursor-pointer ${
              selectedDecision === 'fight'
                ? 'bg-emerald-600 text-white shadow-sm'
                : 'text-emerald-700 hover:bg-emerald-50'
            }`}
          >
            <CheckCircle2 className="w-3.5 h-3.5" />
            Fight ({stats.fight_count || 0})
          </button>
          <button
            onClick={() => setSelectedDecision('concede')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1 cursor-pointer ${
              selectedDecision === 'concede'
                ? 'bg-slate-700 text-white shadow-sm'
                : 'text-slate-600 hover:bg-slate-200'
            }`}
          >
            <XCircle className="w-3.5 h-3.5" />
            Concede ({stats.concede_count || 0})
          </button>
        </div>
      </div>

      {/* Network Filter Pills (Mirrors Image 2 top category bar) */}
      <div className="flex flex-wrap items-center gap-1.5 pt-2 border-t border-slate-100">
        <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mr-2 flex items-center gap-1">
          <Filter className="w-3 h-3" />
          Network:
        </span>
        {NETWORKS.map((net) => (
          <button
            key={net.id}
            onClick={() => setSelectedNetwork(net.id)}
            className={`px-3 py-1 rounded-lg text-xs font-medium transition-all cursor-pointer ${
              selectedNetwork === net.id
                ? 'bg-[#0C2340] text-white font-semibold'
                : 'bg-slate-50 text-slate-600 border border-slate-200/80 hover:bg-slate-100'
            }`}
          >
            {net.label}
          </button>
        ))}
      </div>

      {/* Category Filter Tabs */}
      <div className="flex flex-wrap items-center gap-1.5">
        <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mr-2 flex items-center gap-1">
          <SlidersHorizontal className="w-3 h-3" />
          Category:
        </span>
        {CATEGORIES.map((cat) => (
          <button
            key={cat.id}
            onClick={() => setSelectedCategory(cat.id)}
            className={`px-2.5 py-1 rounded-lg text-[11px] font-medium transition-all cursor-pointer ${
              selectedCategory === cat.id
                ? 'bg-[#0C66E4] text-white font-semibold shadow-sm'
                : 'bg-slate-50 text-slate-600 border border-slate-200/80 hover:bg-slate-100'
            }`}
          >
            {cat.label}
          </button>
        ))}
      </div>
    </div>
  );
}
