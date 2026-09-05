import React, { useState, useEffect, useCallback } from "react";
import {
  CheckCircle2, XCircle, AlertTriangle, Download, Send,
  ArrowRight, ArrowLeft, Copy, Check, RefreshCw, ExternalLink,
  FileText, TrendingUp, TrendingDown,
} from "lucide-react";

const NETWORK_COLORS = {
  VISA: "bg-blue-50 text-blue-700 ring-1 ring-blue-200",
  MASTERCARD: "bg-orange-50 text-orange-700 ring-1 ring-orange-200",
  UPI_NPCI: "bg-violet-50 text-violet-700 ring-1 ring-violet-200",
  RUPAY: "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200",
  AMEX: "bg-teal-50 text-teal-700 ring-1 ring-teal-200",
};

const networkBadge = (network) => {
  const cls = NETWORK_COLORS[network] ?? "bg-slate-100 text-slate-600";
  return (
    <span className={`inline-flex px-2 py-0.5 rounded text-[10px] font-semibold tracking-wide ${cls}`}>
      {network?.replace("_", " ")}
    </span>
  );
};

const catLabel = (cat) =>
  (cat ?? "").replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

const evLabel = (ev) =>
  ev.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

function StepDot({ n, label, current, onClick }) {
  const done = current > n;
  const active = current === n;
  return (
    <button onClick={() => onClick(n)} className="flex items-center gap-2 cursor-pointer group">
      <div
        className={`w-6 h-6 rounded-full flex items-center justify-center text-[11px] font-bold transition-all
          ${done ? "bg-emerald-500 text-white" : active ? "bg-[#0C2340] text-white" : "bg-slate-200 text-slate-500 group-hover:bg-slate-300"}`}
      >
        {done ? "✓" : n}
      </div>
      <span className={`text-xs font-medium hidden sm:block ${active ? "text-slate-900" : "text-slate-400"}`}>
        {label}
      </span>
    </button>
  );
}

function ScenarioCard({ sc, selected, onSelect }) {
  const isFight = sc.model_decision_to_fight === 1;
  return (
    <button
      onClick={() => onSelect(sc.case_id)}
      className={`w-full text-left p-5 rounded-xl border transition-all
        ${selected
          ? "border-[#0C2340] bg-white shadow-sm ring-2 ring-[#0C2340]/10"
          : "border-slate-200 bg-white hover:border-slate-300 hover:shadow-sm"
        }`}
    >
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex flex-wrap items-center gap-1.5">
          {networkBadge(sc.network)}
          <span className="text-[10px] font-medium text-slate-400 font-mono">Code {sc.reason_code}</span>
        </div>
        <span className="text-sm font-bold text-slate-900 font-mono tabular-nums shrink-0">
          ₹{sc.dispute_amount_inr?.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
        </span>
      </div>
      <div className="text-sm font-semibold text-slate-800 mb-1 leading-snug">{sc.reason_code_title}</div>
      <div className="text-xs text-slate-400 mb-3">{catLabel(sc.category)}</div>
      {sc.available_evidence?.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-3">
          {sc.available_evidence.slice(0, 4).map((ev, i) => (
            <span key={i} className="text-[10px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-500 font-mono">
              {evLabel(ev)}
            </span>
          ))}
          {sc.available_evidence.length > 4 && (
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-400">
              +{sc.available_evidence.length - 4} more
            </span>
          )}
        </div>
      )}
      <div className="flex items-center justify-between pt-3 border-t border-slate-100">
        <span className="font-mono text-[10px] text-slate-300">{sc.case_id}</span>
        <span
          className={`inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full
            ${isFight ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-500"}`}
        >
          {isFight ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
          {isFight ? "Fight" : "Concede"}
        </span>
      </div>
    </button>
  );
}

export default function SystemFlowPage({ initialCaseId }) {
  const [step, setStep] = useState(1);
  const [scenarios, setScenarios] = useState([]);
  const [loadingScenarios, setLoadingScenarios] = useState(true);
  const [selectedId, setSelectedId] = useState(initialCaseId || null);
  const [detail, setDetail] = useState(null);
  const [letter, setLetter] = useState("");
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [copied, setCopied] = useState(false);
  const [showPdf, setShowPdf] = useState(false);
  const [showSendModal, setShowSendModal] = useState(false);
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);
  const [ackId] = useState(() => "ACK" + Math.floor(100000 + Math.random() * 900000));

  const fetchPresets = useCallback(async () => {
    setLoadingScenarios(true);
    try {
      const res = await fetch("/api/presets");
      const data = await res.json();
      setScenarios(data);
      if (!initialCaseId && data.length > 0) setSelectedId(data[0].case_id);
    } catch (e) { console.error(e); }
    setLoadingScenarios(false);
  }, [initialCaseId]);

  const shuffleScenarios = useCallback(async () => {
    setLoadingScenarios(true);
    setSelectedId(null);
    try {
      const res = await fetch("/api/presets/shuffle");
      const data = await res.json();
      setScenarios(data);
      if (data.length > 0) setSelectedId(data[0].case_id);
    } catch (e) { console.error(e); }
    setLoadingScenarios(false);
  }, []);

  useEffect(() => { fetchPresets(); }, [fetchPresets]);

  useEffect(() => {
    if (!selectedId) return;
    setLoadingDetail(true);
    setDetail(null);
    setLetter("");
    Promise.all([
      fetch(`/api/cases/${selectedId}`).then((r) => r.json()),
      fetch(`/api/cases/${selectedId}/defense-letter`).then((r) => r.json()),
    ])
      .then(([d, l]) => { setDetail(d); setLetter(l.markdown || ""); setLoadingDetail(false); })
      .catch(() => setLoadingDetail(false));
  }, [selectedId]);

  const isFight = detail?.case_metadata?.model_decision_to_fight === 1;
  const selectedScenario = scenarios.find((s) => s.case_id === selectedId);
  const canAdvance = !!selectedId && !loadingDetail;

  const handleDownload = () => {
    const link = document.createElement("a");
    link.href = `/api/cases/${selectedId}/pdf`;
    link.download = `${selectedId}_Chargeback_Response.pdf`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleSendToBank = () => {
    setShowSendModal(true); setSending(true); setSent(false);
    setTimeout(() => { setSending(false); setSent(true); }, 1800);
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(letter);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // ── Sticky bar ──────────────────────────────────────────────────────────────
  function StickyBar() {
    return (
      <div className="sticky top-16 z-30 bg-white/90 backdrop-blur border-b border-slate-200 px-4 sm:px-6 lg:px-8 py-3">
        <div className="max-w-5xl mx-auto flex items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <StepDot n={1} label="Scenario" current={step} onClick={setStep} />
            <div className="w-8 h-px bg-slate-200" />
            <StepDot n={2} label="System A" current={step} onClick={setStep} />
            <div className="w-8 h-px bg-slate-200" />
            <StepDot n={3} label="Bank Packet" current={step} onClick={setStep} />
          </div>
          <div className="flex items-center gap-3 shrink-0">
            {selectedId ? (
              <div className="hidden md:flex items-center gap-2 text-xs text-slate-500">
                <span className="font-mono font-semibold text-slate-700">{selectedId}</span>
                {selectedScenario && networkBadge(selectedScenario.network)}
              </div>
            ) : (
              <span className="text-xs text-slate-400 hidden md:block">No scenario selected</span>
            )}
            {step === 1 && (
              <button
                disabled={!canAdvance}
                onClick={() => setStep(2)}
                className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold transition-all
                  ${canAdvance
                    ? "bg-[#0C2340] text-white hover:bg-[#0C66E4] cursor-pointer shadow-sm"
                    : "bg-slate-100 text-slate-400 cursor-not-allowed"}`}
              >
                Analyse with System A <ArrowRight className="w-3.5 h-3.5" />
              </button>
            )}
            {step === 2 && (
              <button
                disabled={!detail}
                onClick={() => setStep(3)}
                className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold transition-all
                  ${detail
                    ? "bg-[#0C2340] text-white hover:bg-[#0C66E4] cursor-pointer shadow-sm"
                    : "bg-slate-100 text-slate-400 cursor-not-allowed"}`}
              >
                View bank packet <ArrowRight className="w-3.5 h-3.5" />
              </button>
            )}
            {step === 3 && (
              <button onClick={() => setStep(1)} className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold text-slate-600 bg-slate-100 hover:bg-slate-200 transition-all cursor-pointer">
                <RefreshCw className="w-3.5 h-3.5" /> New Scenario
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  // ── Step 1 ──────────────────────────────────────────────────────────────────
  function Step1() {
    return (
      <div className="space-y-6">
        <div className="flex items-end justify-between">
          <div>
            <p className="text-[11px] uppercase tracking-widest text-slate-400 font-semibold mb-1">Step 1 of 3</p>
            <h2 className="text-xl font-bold text-slate-900">Choose a dispute scenario</h2>
            <p className="text-sm text-slate-400 mt-0.5">Sampled from the held-out test set. Select any to trace the full AI decision flow.</p>
          </div>
          <button
            onClick={shuffleScenarios}
            disabled={loadingScenarios}
            className={`flex items-center gap-2 px-3.5 py-2 rounded-lg border text-xs font-semibold text-slate-600 hover:text-slate-900 hover:border-slate-300 transition-all
              ${loadingScenarios ? "opacity-50 cursor-not-allowed" : "cursor-pointer bg-white border-slate-200"}`}
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loadingScenarios ? "animate-spin" : ""}`} />
            Regenerate suggestions
          </button>
        </div>

        {loadingScenarios ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[...Array(5)].map((_, i) => <div key={i} className="h-44 rounded-xl bg-slate-100 animate-pulse" />)}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {scenarios.map((sc) => (
              <ScenarioCard key={sc.id || sc.case_id} sc={sc} selected={selectedId === sc.case_id} onSelect={setSelectedId} />
            ))}
          </div>
        )}
      </div>
    );
  }

  // ── Step 2 ──────────────────────────────────────────────────────────────────
  function Step2() {
    if (loadingDetail) {
      return (
        <div className="flex flex-col items-center justify-center py-24 gap-3 text-slate-400">
          <RefreshCw className="w-6 h-6 animate-spin" />
          <p className="text-sm">Loading System A evaluation...</p>
        </div>
      );
    }
    if (!detail) return null;
    const m = detail.case_metadata;
    const winPct = (m.predicted_win_prob * 100).toFixed(1);
    const lossPct = ((1 - m.predicted_win_prob) * 100).toFixed(1);
    const expectedRecovery = (m.predicted_win_prob * m.dispute_amount_inr).toFixed(2);
    const riskLoss = ((1 - m.predicted_win_prob) * m.false_positive_cost_inr).toFixed(2);

    return (
      <div className="space-y-6">
        <div>
          <p className="text-[11px] uppercase tracking-widest text-slate-400 font-semibold mb-1">Step 2 of 3</p>
          <h2 className="text-xl font-bold text-slate-900">System A &#8212; Financial risk evaluation</h2>
          <p className="text-sm text-slate-400 mt-0.5">Calibrated ML model computes win probability and expected value before any legal action.</p>
        </div>

        <div className={`rounded-xl p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-5
          ${isFight ? "bg-emerald-50 border border-emerald-200" : "bg-slate-50 border border-slate-200"}`}>
          <div className="flex items-center gap-4">
            <div className={`w-11 h-11 rounded-lg flex items-center justify-center ${isFight ? "bg-emerald-600 text-white" : "bg-slate-700 text-white"}`}>
              {isFight ? <CheckCircle2 className="w-6 h-6" /> : <XCircle className="w-6 h-6" />}
            </div>
            <div>
              <div className="text-[10px] uppercase tracking-widest font-bold text-slate-400 mb-0.5">System A verdict</div>
              <div className="text-lg font-black text-slate-900">{isFight ? "Fight this dispute" : "Concede this dispute"}</div>
              <div className="text-xs text-slate-500 mt-0.5">
                Full amount at stake: <span className="font-semibold text-slate-800">₹{m.dispute_amount_inr.toLocaleString("en-IN")}</span> (100% recovered on win)
              </div>
            </div>
          </div>
          <div className="text-right">
            <div className="text-[10px] uppercase tracking-widest text-slate-400 mb-0.5">Net Expected Value (EV)</div>
            <div className={`text-2xl font-black tabular-nums ${isFight ? "text-emerald-700" : "text-slate-500"}`}>
              {m.expected_value > 0 ? "+" : ""}₹{m.expected_value.toFixed(2)}
            </div>
            <div className="text-[11px] text-slate-400">Risk-weighted expectation</div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-white border border-slate-200 rounded-xl p-5 space-y-4">
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-widest">Win probability P(win)</div>
            <div className="text-4xl font-black text-slate-900 tabular-nums">{winPct}%</div>
            <div className="relative h-2 bg-slate-100 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full ${isFight ? "bg-emerald-500" : "bg-slate-400"}`}
                style={{ width: `${winPct}%` }}
              />
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Calibrated with 5-fold Isotonic Regression. {winPct}% of statistically equivalent disputes resulted in merchant recovery.
            </p>
          </div>

          <div className="bg-[#0C2340] rounded-xl p-5 space-y-3">
            <div className="text-[10px] uppercase tracking-widest text-slate-400 font-semibold">Expected value formula</div>
            <div className="font-mono text-sm text-blue-300 leading-relaxed">EV = (P(win) × Amount) − ((1 − P(win)) × Fee)</div>
            <div className="border-t border-slate-700 pt-2.5 font-mono text-xs text-slate-300 space-y-1">
              <div>= ({winPct}% × ₹{m.dispute_amount_inr.toLocaleString("en-IN")})</div>
              <div className="pl-2">− ({lossPct}% × ₹{m.false_positive_cost_inr.toLocaleString("en-IN")})</div>
            </div>
            <div className={`text-base font-black font-mono ${isFight ? "text-emerald-400" : "text-slate-400"}`}>
              = {m.expected_value > 0 ? "+" : ""}₹{m.expected_value.toFixed(2)}
            </div>
            <p className="text-[11px] text-slate-400 border-t border-slate-700/60 pt-2 leading-tight">
              Note: EV is the statistical return. If won, merchant recovers the full ₹{m.dispute_amount_inr.toLocaleString("en-IN")}.
            </p>
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-5">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-2">Rationale</div>
          <p className="text-sm text-slate-600 leading-relaxed">
            {isFight
              ? `If contested and won, the merchant recovers the full ₹${m.dispute_amount_inr.toLocaleString("en-IN")}. With a ${winPct}% win likelihood against an ₹${m.false_positive_cost_inr.toLocaleString("en-IN")} downside fee, expected gains (+₹${expectedRecovery}) exceed expected fee risk (-₹${riskLoss}), yielding a net positive EV of +₹${m.expected_value.toFixed(2)}.`
              : m.predicted_win_prob < 0.20 && m.expected_value > 0
                ? `Disputed amount is high (₹${m.dispute_amount_inr.toLocaleString("en-IN")}), producing a nominal statistical return (+₹${m.expected_value.toFixed(2)}). However, win confidence is critically low (${winPct}% < 20% safety floor). Card schemes monitor dispute loss rates; contesting high-probability losses triggers acquirer scrutiny and risks losing ₹${m.false_positive_cost_inr.toLocaleString("en-IN")} in fees on a ${(100 - parseFloat(winPct)).toFixed(1)}% likely loss. Conceding preserves merchant operational standing.`
              : m.expected_value > 0 && m.expected_value < 50.0
                ? `Nominal expected value (+₹${m.expected_value.toFixed(2)}) is below the ₹50 operational hurdle rate. Fighting for negligible margin exposes the merchant to ₹${m.false_positive_cost_inr.toLocaleString("en-IN")} in representment fee risk.`
              : `Disputed amount (₹${m.dispute_amount_inr.toLocaleString("en-IN")}) does not justify the representment fee risk (₹${m.false_positive_cost_inr.toLocaleString("en-IN")}). Conceding immediately protects merchant margin by ₹${Math.abs(m.expected_value).toFixed(2)}.`
            }
          </p>
        </div>

        <div className="flex items-center justify-between pt-2">
          <button onClick={() => setStep(1)} className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-900 transition-colors cursor-pointer">
            <ArrowLeft className="w-3.5 h-3.5" /> Choose different scenario
          </button>
          <button onClick={() => setStep(3)} className="flex items-center gap-1.5 px-5 py-2.5 bg-[#0C2340] hover:bg-[#0C66E4] text-white text-xs font-semibold rounded-lg transition-all cursor-pointer shadow-sm">
            View bank packet <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    );
  }

  // ── Step 3 ──────────────────────────────────────────────────────────────────
  function Step3() {
    if (!detail) return null;
    const m = detail.case_metadata;

    return (
      <div className="space-y-6">
        <div>
          <p className="text-[11px] uppercase tracking-widest text-slate-400 font-semibold mb-1">Step 3 of 3</p>
          <h2 className="text-xl font-bold text-slate-900">System B &#8212; Bank submission packet</h2>
          <p className="text-sm text-slate-400 mt-0.5">Agentic evidence audit, contradiction filter, and 4-page bank-ready PDF compiled.</p>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-4">
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="font-semibold text-slate-900 mb-0.5">Ready for submission</div>
              <p className="text-xs text-slate-400">Compiled for {m.network} dispute portal — Case {m.case_id}</p>
            </div>
            <span className="flex items-center gap-1 px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 text-[10px] font-semibold border border-emerald-200 shrink-0">
              <CheckCircle2 className="w-3 h-3" /> Compliance verified
            </span>
          </div>
          <div className="flex flex-wrap gap-3 pt-2 border-t border-slate-100">
            <button onClick={handleDownload} className="flex items-center gap-2 px-4 py-2.5 rounded-lg border border-slate-300 bg-white text-slate-800 text-xs font-semibold hover:border-slate-400 transition-all cursor-pointer">
              <Download className="w-3.5 h-3.5 text-[#0C66E4]" /> Download chargeback response
            </button>
            <button onClick={handleSendToBank} className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-[#0C2340] hover:bg-[#0C66E4] text-white text-xs font-semibold transition-all cursor-pointer shadow-sm">
              Send to bank <Send className="w-3.5 h-3.5" />
            </button>
          </div>
          <p className="text-[11px] text-slate-400">4-page bundle: Rebuttal Cover Letter (P.1) · Commercial Tax Invoice (Exhibit A) · Primary Proof (Exhibit B) · Telemetry &amp; Policy Audit (Exhibit C). Internal model scores are decoupled from this packet.</p>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
          <div className="px-5 py-4 border-b border-slate-100">
            <div className="text-sm font-semibold text-slate-900">Agentic evidence audit</div>
            <p className="text-xs text-slate-400 mt-0.5">{detail.total_evidence_found} ERP items scanned — {detail.contradictions_detected_count} contradiction{detail.contradictions_detected_count !== 1 ? "s" : ""} filtered</p>
          </div>
          <div className="divide-y divide-slate-100">
            {detail.evidence_items.map((item, idx) => {
              const bad = item.is_contradictory_detected;
              return (
                <div key={idx} className={`px-5 py-3.5 ${bad ? "bg-amber-50/50" : ""}`}>
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs font-semibold text-slate-800">{evLabel(item.evidence_type)}</span>
                        {item.is_required && <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-blue-50 text-blue-600 border border-blue-200 uppercase tracking-wide">Mandatory</span>}
                      </div>
                      <p className={`text-[11px] leading-relaxed line-clamp-2 ${bad ? "text-amber-800" : "text-slate-500"}`}>{item.document_text}</p>
                      {bad && (
                        <div className="flex items-center gap-1.5 mt-1.5 text-[10px] text-amber-700 font-medium">
                          <AlertTriangle className="w-3 h-3" /> Contradiction detected — excluded from bank submission
                        </div>
                      )}
                    </div>
                    <span className={`shrink-0 text-[10px] font-semibold px-2 py-0.5 rounded-full ${bad ? "bg-amber-100 text-amber-800 border border-amber-300" : "bg-emerald-50 text-emerald-700 border border-emerald-200"}`}>
                      {bad ? "Excluded" : "Included"}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
          <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
            <div className="text-sm font-semibold text-slate-900">Executive defense statement</div>
            <button onClick={handleCopy} className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 text-xs font-medium text-slate-600 hover:bg-slate-50 cursor-pointer transition-all">
              {copied ? <Check className="w-3 h-3 text-emerald-600" /> : <Copy className="w-3 h-3" />}
              {copied ? "Copied" : "Copy text"}
            </button>
          </div>
          <pre className="px-5 py-4 text-[11px] font-mono text-slate-600 whitespace-pre-wrap leading-relaxed max-h-52 overflow-y-auto bg-slate-50/50">
            {letter || "Generating statement..."}
          </pre>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
          <button onClick={() => setShowPdf(!showPdf)} className="w-full px-5 py-4 flex items-center justify-between text-left cursor-pointer hover:bg-slate-50 transition-colors">
            <div className="flex items-center gap-3">
              <FileText className="w-4 h-4 text-slate-400" />
              <div>
                <div className="text-sm font-semibold text-slate-900">4-page bank document preview</div>
                <p className="text-xs text-slate-400">Cover letter (P.1) · Commercial invoice (Ex. A) · Primary proof (Ex. B) · Telemetry &amp; policy (Ex. C)</p>
              </div>
            </div>
            <span className="text-xs text-[#0C66E4] font-medium flex items-center gap-1">
              {showPdf ? "Hide" : "Show"} preview <ExternalLink className="w-3 h-3" />
            </span>
          </button>
          {showPdf && (
            <div className="border-t border-slate-100 h-96 bg-slate-50">
              <iframe src={`/api/cases/${selectedId}/pdf#toolbar=0`} className="w-full h-full border-none" title="Bank document preview" />
            </div>
          )}
        </div>

        <div className="flex items-center justify-between pt-2">
          <button onClick={() => setStep(2)} className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-900 transition-colors cursor-pointer">
            <ArrowLeft className="w-3.5 h-3.5" /> Back to System A
          </button>
          <button onClick={() => { setStep(1); setDetail(null); setLetter(""); setShowPdf(false); }} className="flex items-center gap-1.5 text-xs text-[#0C66E4] hover:text-blue-700 cursor-pointer transition-colors">
            <RefreshCw className="w-3.5 h-3.5" /> Test another scenario
          </button>
        </div>
      </div>
    );
  }

  // ── Send modal ──────────────────────────────────────────────────────────────
  function SendModal() {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-sm p-4">
        <div className="bg-white rounded-2xl shadow-2xl max-w-sm w-full p-6 space-y-5">
          <div className="flex items-center justify-between">
            <div className="text-sm font-bold text-slate-900">Network gateway submission</div>
            {!sending && <button onClick={() => setShowSendModal(false)} className="text-slate-400 hover:text-slate-700 text-xl leading-none cursor-pointer">×</button>}
          </div>
          {sending ? (
            <div className="py-10 flex flex-col items-center gap-3 text-slate-500">
              <div className="w-8 h-8 border-2 border-[#0C66E4] border-t-transparent rounded-full animate-spin" />
              <p className="text-xs text-center">Transmitting representment bundle to {detail?.case_metadata?.network} dispute gateway...</p>
            </div>
          ) : sent ? (
            <div className="space-y-4">
              <div className="flex items-start gap-3 p-4 rounded-xl bg-emerald-50 border border-emerald-200">
                <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
                <div>
                  <div className="text-sm font-semibold text-emerald-900">Packet dispatched</div>
                  <p className="text-xs text-emerald-700 mt-0.5">The 4-page evidence bundle has been acknowledged by the acquiring bank.</p>
                </div>
              </div>
              <div className="p-3.5 rounded-xl border border-slate-200 font-mono text-[11px] text-slate-600 space-y-1 bg-slate-50">
                <div><span className="text-slate-400">Network </span>{detail?.case_metadata?.network}</div>
                <div><span className="text-slate-400">Reason  </span>{detail?.case_metadata?.reason_code}</div>
                <div><span className="text-slate-400">Ack ID  </span>{ackId}</div>
                <div><span className="text-slate-400">Status  </span>REPRESENTMENT_SUBMITTED</div>
                <div><span className="text-slate-400">Time    </span>{new Date().toISOString()}</div>
              </div>
              <button onClick={() => setShowSendModal(false)} className="w-full py-2.5 rounded-xl bg-[#0C2340] hover:bg-[#0C66E4] text-white text-xs font-semibold transition-all cursor-pointer">Close</button>
            </div>
          ) : null}
        </div>
      </div>
    );
  }

  return (
    <>
      <StickyBar />
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 pb-24">
        {step === 1 && <Step1 />}
        {step === 2 && <Step2 />}
        {step === 3 && <Step3 />}
      </div>
      {showSendModal && <SendModal />}
    </>
  );
}
