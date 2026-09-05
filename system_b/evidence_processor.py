"""
SYSTEM B — EVIDENCE PROCESSOR & FILTERING ENGINE

Responsibilities:
  1. Load System A calibrated model and run inference on chargeback cases.
  2. Filter cases where Expected Value (EV) > 0 (profitable to fight).
  3. Join high-EV cases with evidence_items.csv.
  4. Filter out contradictory evidence (is_contradictory == False).
  5. Rank evidence items by ground_truth_rank (1=Required, 2=Relevant)
     and evidence_quality_score (descending).
  6. Return structured case payloads ready for LLM prompt formatting.
"""

from pathlib import Path
import joblib
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "system_a" / "model" / "xgb_calibrated_model.pkl"
FEATURE_COLS_PATH = ROOT / "system_a" / "model" / "feature_cols.pkl"
CASES_PATH = (
    ROOT / "data" / "chargeback_cases_v6.csv"
    if (ROOT / "data" / "chargeback_cases_v6.csv").exists()
    else ROOT / "data" / "chargeback_cases.csv"
)
EVIDENCE_PATH = ROOT / "data" / "evidence_items.csv"


def load_and_score_cases():
    """Run System A inference and compute Expected Value (EV)."""
    model = joblib.load(MODEL_PATH)
    feature_cols = joblib.load(FEATURE_COLS_PATH)
    cases_df = pd.read_csv(CASES_PATH)

    # Encode features matching System A training pipeline
    categorical_cols = ["network", "payment_rail", "normalized_category"]
    boolean_cols = [
        "is_tokenized", "bank_rrn_match", "delivery_otp_verified", "ip_geo_match",
        "sim_swap_flag_48h", "transaction_record_match", "post_dispute_activity",
    ]
    df_temp = cases_df.copy()
    for col in boolean_cols:
        df_temp[col] = df_temp[col].astype(int)

    df_encoded = pd.get_dummies(df_temp, columns=categorical_cols, drop_first=True)
    df_encoded = df_encoded.reindex(columns=list(feature_cols), fill_value=0)

    # Predict win probability and expected value
    cases_df["predicted_win_prob"] = model.predict_proba(df_encoded[feature_cols])[:, 1]
    cases_df["expected_value"] = (
        cases_df["predicted_win_prob"] * cases_df["dispute_amount_inr"]
        - (1 - cases_df["predicted_win_prob"]) * cases_df["false_positive_cost_inr"]
    )
    cases_df["model_decision_to_fight"] = (cases_df["expected_value"] > 0).astype(int)

    return cases_df


def get_high_ev_cases(split="test"):
    """Filter cases from the dataset where EV > 0."""
    cases_df = load_and_score_cases()
    if split:
        cases_df = cases_df[cases_df["dataset_split"] == split]

    high_ev_df = cases_df[cases_df["model_decision_to_fight"] == 1].copy()
    return high_ev_df.sort_values("expected_value", ascending=False)


_CACHED_EVIDENCE_DF = None

def get_cached_evidence_df():
    global _CACHED_EVIDENCE_DF
    if _CACHED_EVIDENCE_DF is None:
        _CACHED_EVIDENCE_DF = pd.read_csv(EVIDENCE_PATH)
    return _CACHED_EVIDENCE_DF


def get_case_evidence_payload(case_id, cases_df=None):
    """
    Retrieves case metadata and filtered/ranked evidence items for a given case_id.
    Filters out contradictory items (is_contradictory == True).
    """
    if cases_df is None:
        cases_df = load_and_score_cases()

    case_row = cases_df[cases_df["case_id"] == case_id]
    if case_row.empty:
        raise ValueError(f"Case ID {case_id} not found.")

    case_meta = case_row.iloc[0].to_dict()

    # Load evidence items (cached)
    evidence_df = get_cached_evidence_df()
    case_evidence = evidence_df[evidence_df["case_id"] == case_id].copy()

    # OPTION B: Pass ALL evidence items to LLM for dynamic text auditing
    # (Do NOT filter by is_contradictory in Python; let LLM audit raw text snippets)
    all_evidence = case_evidence.copy()
    all_evidence["is_required_int"] = all_evidence["is_required"].astype(int)
    ranked_evidence = all_evidence.sort_values(
        by=["is_required_int", "evidence_quality_score"], ascending=[False, False]
    )

    # Omit is_contradictory from payload so LLM gets no pre-labeled boolean flags
    evidence_list = ranked_evidence[
        ["evidence_id", "evidence_type", "document_text", "is_required", "evidence_quality_score"]
    ].to_dict(orient="records")

    return {
        "case_metadata": case_meta,
        "evidence_items": evidence_list,
        "total_evidence_found": len(case_evidence),
        "clean_evidence_count": len(evidence_list),
        "filtered_contradictory_count": 0,  # Handled dynamically by LLM
    }


def get_sample_cases_to_fight(sample_per_category=1, split="test"):
    """
    Returns representative high-EV cases (default: 1 top-EV case per dispute category)
    ready for System B LLM processing.
    """
    high_ev_df = get_high_ev_cases(split=split)
    sampled_ids = []

    for cat in high_ev_df["normalized_category"].unique():
        cat_cases = high_ev_df[high_ev_df["normalized_category"] == cat]
        top_cases = cat_cases.head(sample_per_category)["case_id"].tolist()
        sampled_ids.extend(top_cases)

    payloads = [get_case_evidence_payload(cid, cases_df=high_ev_df) for cid in sampled_ids]
    return payloads


if __name__ == "__main__":
    cases = get_high_ev_cases(split="test")
    print(f"Total test cases where EV > 0 (System A fight decision): {len(cases)} / 1,500")

    sample_payloads = get_sample_cases_to_fight(sample_per_category=1)
    print(f"Sampled {len(sample_payloads)} representative cases across categories:")
    for p in sample_payloads:
        meta = p["case_metadata"]
        print(f"  [{meta['case_id']}] Category: {meta['normalized_category']:<24} | "
              f"Network: {meta['network']:<16} | Reason Code: {meta.get('reason_code', 'N/A')} | "
              f"EV: Rs {meta['expected_value']:.2f} | Evidence Items: {p['clean_evidence_count']}")
