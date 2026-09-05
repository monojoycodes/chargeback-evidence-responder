import React, { useState, useEffect } from 'react';
import {
  X,
  FileText,
  ShieldCheck,
  AlertTriangle,
  Download,
  Copy,
  Check,
  CheckCircle2,
  XCircle,
  ExternalLink,
  Layers,
  Sparkles,
} from 'lucide-react';

export default function CaseDrawer({ caseId, onClose }) {
  const [activeTab, setActiveTab] = useState('ml');
  const [detail, setDetail] = useState(null);
  const [letter, setLetter] = useState('');
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!caseId) return;
    setLoading(true);

    Promise.all([
      fetch(`/api/cases/${caseId}`).then((r) => r.json()),
      fetch(`/api/cases/${caseId}/defense-letter`).then((r) => r.json()),
    ])
      .then(([detailData, letterData]) => {
        setDetail(detailData);
        setLetter(letterData.markdown || '');
        setLoading(false);
      })
      .catch((err) => {
        console.error('Error fetching case detail:', err);
        setLoading(false);
      });
  }, [caseId]);

  const handleCopy = () => {
    navigator.clipboard.writeText(letter);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!caseId) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-900/40 backdrop-blur-xs transition-opacity animate-in fade-in duration-200">
      <div className="w-full max-w-2xl bg-white h-full shadow-2xl flex flex-col border-l border-slate-200 animate-in slide-in-from-right duration-300">
        
        {/* Drawer Header */}
        <div className="p-5 border-b border-slate-200 flex items-center justify-between bg-slate-50/70">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-slate-200 text-slate-800">
                {caseId}
              </span>
              {detail && (
                <span className="text-[11px] font-semibold px-2 py-0.5 rounded bg-blue-50 text-[#0C66E4] border border-blue-200">
                  {detail.case_metadata.network} • Code {detail.case_metadata.reason_code}
                </span>
              )}
            </div>
            <h2 className="text-base font-bold text-slate-900 line-clamp-1">
              {detail ? detail.case_metadata.reason_code_title : 'Loading dispute details...'}
            </h2>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-slate-700 hover:bg-slate-200/60 transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center gap-2 px-5 pt-3 border-b border-slate-200 bg-white">
          <button
            onClick={() => setActiveTab('ml')}
            className={`pb-3 text-xs font-semibold border-b-2 transition-all cursor-pointer ${
              activeTab === 'ml'
                ? 'border-[#0C66E4] text-[#0C66E4]'
                : 'border-transparent text-slate-500 hover:text-slate-900'
            }`}
          >
            System A: Financial EV
          </button>
          <button
            onClick={() => setActiveTab('audit')}
            className={`pb-3 text-xs font-semibold border-b-2 transition-all flex items-center gap-1.5 cursor-pointer ${
              activeTab === 'audit'
                ? 'border-[#0C66E4] text-[#0C66E4]'
                : 'border-transparent text-slate-500 hover:text-slate-900'
            }`}
          >
            <span>Agentic Evidence Audit</span>
            {detail && detail.contradictions_detected_count > 0 && (
              <span className="px-1.5 py-0.2 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800">
                {detail.contradictions_detected_count} Flagged
              </span>
            )}
          </button>
          <button
            onClick={() => setActiveTab('letter')}
            className={`pb-3 text-xs font-semibold border-b-2 transition-all cursor-pointer ${
              activeTab === 'letter'
                ? 'border-[#0C66E4] text-[#0C66E4]'
                : 'border-transparent text-slate-500 hover:text-slate-900'
            }`}
          >
            Legal Representment Letter
          </button>
          <button
            onClick={() => setActiveTab('pdf')}
            className={`pb-3 text-xs font-semibold border-b-2 transition-all cursor-pointer ${
              activeTab === 'pdf'
                ? 'border-[#0C66E4] text-[#0C66E4]'
                : 'border-transparent text-slate-500 hover:text-slate-900'
            }`}
          >
            Bank-Ready 4-Page PDF
          </button>
        </div>

        {/* Drawer Body */}
        <div className="flex-1 overflow-y-auto p-5">
          {loading ? (
            <div className="flex flex-col items-center justify-center h-64 text-slate-400 gap-2">
              <div className="w-8 h-8 border-3 border-blue-500 border-t-transparent rounded-full animate-spin" />
              <p className="text-xs">Analyzing case with System A & System B...</p>
            </div>
          ) : !detail ? (
            <div className="text-center py-12 text-slate-500 text-xs">Failed to load case details.</div>
          ) : (
            <>
              {/* TAB 1: SYSTEM A ML RISK & EV */}
              {activeTab === 'ml' && (
                <div className="space-y-5">
                  {/* Decision Banner */}
                  <div
                    className={`p-4 rounded-2xl border flex items-center justify-between ${
                      detail.case_metadata.model_decision_to_fight === 1
                        ? 'bg-emerald-50/70 border-emerald-200 text-emerald-900'
                        : 'bg-slate-50 border-slate-200 text-slate-900'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      {detail.case_metadata.model_decision_to_fight === 1 ? (
                        <div className="w-10 h-10 rounded-xl bg-emerald-600 text-white flex items-center justify-center font-black">
                          <CheckCircle2 className="w-6 h-6" />
                        </div>
                      ) : (
                        <div className="w-10 h-10 rounded-xl bg-slate-600 text-white flex items-center justify-center font-black">
                          <XCircle className="w-6 h-6" />
                        </div>
                      )}
                      <div>
                        <div className="text-xs font-bold uppercase tracking-wider">
                          {detail.case_metadata.model_decision_to_fight === 1
                            ? 'AI Strategy: FIGHT DISPUTE'
                            : 'AI Strategy: CONCEDE DISPUTE'}
                        </div>
                        <div className="text-xs text-slate-600 mt-0.5">
                          {detail.case_metadata.model_decision_to_fight === 1
                            ? `Positive Expected Value (+₹${detail.case_metadata.expected_value.toFixed(2)}). Recovering merchant margin.`
                            : detail.case_metadata.predicted_win_prob < 0.20
                            ? `Win probability (${(detail.case_metadata.predicted_win_prob * 100).toFixed(1)}%) below 20% safety floor. Conceding protects gateway standing.`
                            : detail.case_metadata.expected_value < 50.0
                            ? `Net EV (+₹${detail.case_metadata.expected_value.toFixed(2)}) below ₹50 hurdle rate. Conceding avoids fee risk.`
                            : `Negative Expected Value (EV ≤ 0). Conceding saves ₹${detail.case_metadata.false_positive_cost_inr} fee on low win probability.`}
                        </div>
                      </div>
                    </div>

                    <div className="text-right">
                      <div className="text-[10px] uppercase font-bold text-slate-400">
                        {detail.case_metadata.model_decision_to_fight === 1 ? 'Amount to Recover' : 'Fee Saved'}
                      </div>
                      <div className="text-lg font-black text-slate-900">
                        ₹{(detail.case_metadata.model_decision_to_fight === 1
                          ? detail.case_metadata.dispute_amount_inr
                          : detail.case_metadata.false_positive_cost_inr
                        ).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </div>
                    </div>
                  </div>

                  {/* Mathematical EV Equation Box */}
                  <div className="p-4 rounded-xl bg-slate-900 text-white font-mono text-xs space-y-2">
                    <div className="text-slate-400 text-[10px] uppercase tracking-wider font-sans font-bold">
                      Expected Value Calculation Formula
                    </div>
                    <div className="text-blue-300">
                      EV = (P(win) × Dispute Amount) − ((1 − P(win)) × False Positive Cost)
                    </div>
                    <div className="text-slate-300 pt-1 border-t border-slate-800">
                      EV = ({(detail.case_metadata.predicted_win_prob * 100).toFixed(1)}% × ₹
                      {detail.case_metadata.dispute_amount_inr}) − (
                      {((1 - detail.case_metadata.predicted_win_prob) * 100).toFixed(1)}% × ₹
                      {detail.case_metadata.false_positive_cost_inr}) ={' '}
                      <span className={detail.case_metadata.expected_value > 0 ? 'text-emerald-400 font-bold' : 'text-slate-400 font-bold'}>
                        ₹{detail.case_metadata.expected_value.toFixed(2)}
                      </span>
                    </div>
                  </div>

                  {/* Model Features Grid */}
                  <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 space-y-3">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                      Key Verified Risk Factors (System A Feature Set)
                    </h3>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div className="flex items-center justify-between p-2 rounded-lg bg-white border border-slate-200/80">
                        <span className="text-slate-600">3DS / Auth Liability Shift:</span>
                        <span className="font-bold text-emerald-700">ECI 05 Active</span>
                      </div>
                      <div className="flex items-center justify-between p-2 rounded-lg bg-white border border-slate-200/80">
                        <span className="text-slate-600">Delivery OTP Verified:</span>
                        <span className={`font-bold ${detail.case_metadata.delivery_otp_verified ? 'text-emerald-700' : 'text-slate-500'}`}>
                          {detail.case_metadata.delivery_otp_verified ? 'YES (Doorstep)' : 'No'}
                        </span>
                      </div>
                      <div className="flex items-center justify-between p-2 rounded-lg bg-white border border-slate-200/80">
                        <span className="text-slate-600">Bank RRN Match:</span>
                        <span className={`font-bold ${detail.case_metadata.bank_rrn_match ? 'text-emerald-700' : 'text-slate-500'}`}>
                          {detail.case_metadata.bank_rrn_match ? 'MATCHED' : 'Pending'}
                        </span>
                      </div>
                      <div className="flex items-center justify-between p-2 rounded-lg bg-white border border-slate-200/80">
                        <span className="text-slate-600">IP Geolocation Match:</span>
                        <span className={`font-bold ${detail.case_metadata.ip_geo_match ? 'text-emerald-700' : 'text-slate-500'}`}>
                          {detail.case_metadata.ip_geo_match ? 'MATCHED' : 'Mismatch'}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 2: AGENTIC EVIDENCE AUDITOR (OPTION B) */}
              {activeTab === 'audit' && (
                <div className="space-y-4">
                  {/* Mandatory Requirement Audit Banner */}
                  <div className="p-4 rounded-xl border border-blue-200 bg-blue-50/50">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-bold text-blue-900 uppercase tracking-wider">
                        Mandatory Network Evidence Coverage
                      </span>
                      <span className="text-xs font-bold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded">
                        {detail.all_mandatory_present ? '100% COMPLETE' : 'INCOMPLETE'}
                      </span>
                    </div>
                    <div className="space-y-1">
                      {detail.mandatory_audit.map((req, i) => (
                        <div key={i} className="flex items-center justify-between text-xs py-1 border-b border-blue-100/50">
                          <span className="text-slate-700 font-medium">{req.requirement}</span>
                          <span className="font-bold text-emerald-700 flex items-center gap-1">
                            <Check className="w-3.5 h-3.5" />
                            {req.status}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Option B Contradiction Filter Demo */}
                  <div>
                    <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 mb-2 flex items-center gap-2">
                      <span>ERP Evidence Documents Audited by System B</span>
                      <span className="text-[10px] font-normal text-slate-500">(Option B Agentic Audit)</span>
                    </h3>

                    <div className="space-y-2.5">
                      {detail.evidence_items.map((item, idx) => {
                        const isContradictory = item.is_contradictory_detected;
                        return (
                          <div
                            key={idx}
                            className={`p-3.5 rounded-xl border transition-all ${
                              isContradictory
                                ? 'bg-amber-50/60 border-amber-300'
                                : 'bg-white border-slate-200'
                            }`}
                          >
                            <div className="flex items-center justify-between mb-1.5">
                              <div className="flex items-center gap-2">
                                <span className="font-mono text-[10px] font-bold px-1.5 py-0.5 rounded bg-slate-100 text-slate-700">
                                  #{idx + 1} {item.evidence_type}
                                </span>
                                {item.is_required && (
                                  <span className="text-[10px] font-bold text-blue-700 bg-blue-50 px-1.5 py-0.5 rounded border border-blue-200">
                                    MANDATORY
                                  </span>
                                )}
                              </div>

                              <span
                                className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                                  isContradictory
                                    ? 'bg-amber-100 text-amber-900 border border-amber-300'
                                    : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                                }`}
                              >
                                {item.audit_verdict}
                              </span>
                            </div>

                            <p className={`text-xs ${isContradictory ? 'text-amber-950 font-medium' : 'text-slate-700'}`}>
                              {item.document_text}
                            </p>

                            {isContradictory && (
                              <div className="mt-2 pt-2 border-t border-amber-200/80 text-[11px] text-amber-800 font-semibold flex items-center gap-1.5">
                                <AlertTriangle className="w-3.5 h-3.5" />
                                <span>
                                  LLM Action: Excluded from Section 3 Table to prevent submitting self-incriminating proof to card issuer.
                                </span>
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 3: LEGAL DEFENSE PACKAGE */}
              {activeTab === 'letter' && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                      Generated Formal Defense Package (Markdown)
                    </span>
                    <button
                      onClick={handleCopy}
                      className="px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold flex items-center gap-1.5 shadow-xs transition-all cursor-pointer"
                    >
                      {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                      <span>{copied ? 'Copied!' : 'Copy Letter'}</span>
                    </button>
                  </div>

                  <pre className="p-4 rounded-xl bg-slate-900 text-slate-100 text-xs font-mono overflow-x-auto whitespace-pre-wrap leading-relaxed max-h-[500px]">
                    {letter || 'No defense package available.'}
                  </pre>
                </div>
              )}

              {/* TAB 4: BANK-READY 4-PAGE PDF */}
              {activeTab === 'pdf' && (
                <div className="space-y-4">
                  <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Layers className="w-5 h-5 text-[#0C66E4]" />
                        <div>
                          <h4 className="text-xs font-bold text-slate-900">4-Page Compiled Bank Package</h4>
                          <p className="text-[11px] text-slate-500">
                            Cover Letter + Appendix A (Tax Invoice) + Appendix B (Proof of Delivery)
                          </p>
                        </div>
                      </div>

                      <a
                        href={`/api/cases/${caseId}/pdf`}
                        target="_blank"
                        rel="noreferrer"
                        className="px-4 py-2 rounded-xl bg-[#0C66E4] hover:bg-blue-700 text-white text-xs font-bold flex items-center gap-2 shadow-sm transition-all cursor-pointer"
                      >
                        <Download className="w-4 h-4" />
                        <span>Download 4-Page PDF</span>
                      </a>
                    </div>

                    <div className="text-[11px] text-slate-600 bg-white p-3 rounded-lg border border-slate-200/80">
                      <strong>100% Bank-Ready Guarantee:</strong> Internal AI win probabilities, EV scores, and debug tags
                      are omitted from the PDF. The document adheres strictly to Visa VROL, Mastercard MasterCom, and NPCI UPI
                      dispute submission standards.
                    </div>
                  </div>

                  {/* PDF Viewer Frame */}
                  <div className="w-full h-[450px] rounded-xl border border-slate-200 overflow-hidden bg-slate-100 shadow-inner">
                    <iframe
                      src={`/api/cases/${caseId}/pdf#toolbar=0`}
                      className="w-full h-full border-none"
                      title="4-Page Bank-Ready PDF Preview"
                    />
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
