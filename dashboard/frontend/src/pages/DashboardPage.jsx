import React, { useState, useEffect } from 'react';
import { Search, Filter, CheckCircle2, XCircle, ArrowRight, ExternalLink } from 'lucide-react';

const NETWORKS = [
  { id: 'all', label: 'All Networks' },
  { id: 'VISA', label: 'Visa' },
  { id: 'MASTERCARD', label: 'Mastercard' },
  { id: 'UPI_NPCI', label: 'UPI' },
  { id: 'RUPAY', label: 'RuPay' },
  { id: 'AMERICAN_EXPRESS', label: 'Amex' },
];

export default function DashboardPage({ onSelectCaseForFlow }) {
  const [cases, setCases] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);

  const [search, setSearch] = useState('');
  const [selectedNetwork, setSelectedNetwork] = useState('all');
  const [selectedDecision, setSelectedDecision] = useState('all');
  const [limit, setLimit] = useState(25);

  useEffect(() => {
    setLoading(true);
    const params = new URLSearchParams({
      network: selectedNetwork,
      decision: selectedDecision,
      search: search,
      limit: limit.toString(),
      offset: '0',
    });

    fetch(`/api/cases?${params.toString()}`)
      .then((r) => r.json())
      .then((data) => {
        setCases(data.cases || []);
        setStats({
          total: data.total,
          fight_count: data.fight_count,
          concede_count: data.concede_count,
          total_disputed_val: data.total_disputed_val,
          total_expected_value: data.total_expected_value,
        });
        setLoading(false);
      })
      .catch((err) => {
        console.error('Error fetching dashboard cases:', err);
        setLoading(false);
      });
  }, [selectedNetwork, selectedDecision, search, limit]);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6 pb-16">
      {/* Top Header */}
      <div>
        <h1 className="text-2xl font-black text-slate-900 tracking-tight">Merchant Dispute Queue</h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Real-time chargeback stream scored by System A Expected Value engine:
        </p>
      </div>

      {/* 3 Clean KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
          <div className="text-[11px] uppercase font-bold text-slate-400">Total Disputes Screened</div>
          <div className="text-2xl font-black text-slate-900 mt-1">1,500</div>
          <div className="text-[11px] text-slate-500 mt-0.5">Held-out test set cases</div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
          <div className="text-[11px] uppercase font-bold text-slate-400">AI Decision Strategy</div>
          <div className="text-2xl font-black text-slate-900 mt-1">
            <span className="text-emerald-600">71% Fight</span> <span className="text-slate-300 font-normal">/</span> <span className="text-slate-500 font-normal text-lg">29% Concede</span>
          </div>
          <div className="text-[11px] text-slate-500 mt-0.5">Selective defense avoids lost fees</div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-emerald-200 bg-emerald-50/20 shadow-xs">
          <div className="text-[11px] uppercase font-bold text-emerald-700">Net Value Added (Held-Out)</div>
          <div className="text-2xl font-black text-emerald-700 mt-1">+₹381,448</div>
          <div className="text-[11px] text-emerald-600 mt-0.5">+71.1% of theoretical Oracle recovery</div>
        </div>
      </div>

      {/* Clean Filter Row */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs flex flex-col md:flex-row items-center justify-between gap-3">
        {/* Search */}
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search Case ID, Order ID, Reason Code..."
            className="w-full pl-9 pr-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-[#0C66E4] focus:bg-white text-slate-800"
          />
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-2 w-full md:w-auto justify-end">
          {/* Network Filter */}
          <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-xl border border-slate-200 text-xs">
            {NETWORKS.map((n) => (
              <button
                key={n.id}
                onClick={() => setSelectedNetwork(n.id)}
                className={`px-2.5 py-1 rounded-lg font-medium transition-all cursor-pointer ${
                  selectedNetwork === n.id
                    ? 'bg-white text-slate-900 font-bold shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                {n.label}
              </button>
            ))}
          </div>

          {/* Decision Filter */}
          <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-xl border border-slate-200 text-xs">
            <button
              onClick={() => setSelectedDecision('all')}
              className={`px-2.5 py-1 rounded-lg font-medium transition-all cursor-pointer ${
                selectedDecision === 'all'
                  ? 'bg-white text-slate-900 font-bold shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              All
            </button>
            <button
              onClick={() => setSelectedDecision('fight')}
              className={`px-2.5 py-1 rounded-lg font-medium transition-all cursor-pointer ${
                selectedDecision === 'fight'
                  ? 'bg-emerald-600 text-white font-bold shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Fight Only
            </button>
            <button
              onClick={() => setSelectedDecision('concede')}
              className={`px-2.5 py-1 rounded-lg font-medium transition-all cursor-pointer ${
                selectedDecision === 'concede'
                  ? 'bg-slate-700 text-white font-bold shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Concede Only
            </button>
          </div>
        </div>
      </div>

      {/* Streamlined Clean Table */}
      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-xs">
        {loading ? (
          <div className="p-12 text-center text-slate-400 text-xs">Loading disputes...</div>
        ) : cases.length === 0 ? (
          <div className="p-12 text-center text-slate-400 text-xs">No disputes match your filter.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-slate-400 uppercase text-[10px] font-bold">
                  <th className="py-3 px-4">Case Reference</th>
                  <th className="py-3 px-4">Dispute Reason</th>
                  <th className="py-3 px-4">Network Rail</th>
                  <th className="py-3 px-4 text-right">Disputed Amount</th>
                  <th className="py-3 px-4 text-right">Win Confidence</th>
                  <th className="py-3 px-4 text-center">AI Decision (EV)</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {cases.map((c) => {
                  const isFight = c.model_decision_to_fight === 1;
                  return (
                    <tr key={c.case_id} className="hover:bg-slate-50/70 transition-colors">
                      <td className="py-3 px-4 font-mono font-bold text-slate-900">
                        {c.case_id}
                        <div className="text-[10px] text-slate-400 font-normal">{c.order_id}</div>
                      </td>

                      <td className="py-3 px-4">
                        <div className="font-semibold text-slate-800 line-clamp-1">{c.reason_code_title}</div>
                        <div className="text-[10px] text-slate-400">Code {c.reason_code}</div>
                      </td>

                      <td className="py-3 px-4">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-700">
                          {c.network}
                        </span>
                      </td>

                      <td className="py-3 px-4 text-right font-mono font-bold text-slate-900">
                        ₹{c.dispute_amount_inr.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </td>

                      <td className="py-3 px-4 text-right font-mono">
                        <span className={`font-bold ${c.predicted_win_prob >= 0.6 ? 'text-emerald-700' : 'text-slate-600'}`}>
                          {(c.predicted_win_prob * 100).toFixed(1)}%
                        </span>
                      </td>

                      <td className="py-3 px-4 text-center">
                        {isFight ? (
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                            <CheckCircle2 className="w-3 h-3" />
                            FIGHT (+₹{c.expected_value.toFixed(0)})
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-slate-100 text-slate-600 border border-slate-200">
                            <XCircle className="w-3 h-3" />
                            CONCEDE
                          </span>
                        )}
                      </td>

                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={() => onSelectCaseForFlow(c.case_id)}
                          className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-[#0C66E4] hover:bg-blue-700 text-white font-semibold text-[11px] transition-colors cursor-pointer"
                        >
                          <span>Inspect Flow</span>
                          <ArrowRight className="w-3 h-3" />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Load More */}
        {cases.length < stats.total && (
          <div className="p-4 border-t border-slate-100 text-center">
            <button
              onClick={() => setLimit((prev) => prev + 25)}
              className="text-xs font-semibold text-[#0C66E4] hover:underline cursor-pointer"
            >
              Load More Disputes ({cases.length} of {stats.total})
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
