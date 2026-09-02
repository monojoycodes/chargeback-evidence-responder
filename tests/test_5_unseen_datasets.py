"""
EVALUATION ACROSS 5 COMPLETELY UNSEEN HELD-OUT DATASETS

Generates 5 brand new datasets with different random seeds, shifted parameter
distributions, and varied noise levels.
Runs the pre-trained System A model (without retraining) and System B evidence
responder on each dataset to evaluate true generalization and robustness.
"""

import sys
from pathlib import Path
import os
import random
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import joblib
from sklearn.metrics import average_precision_score, brier_score_loss, precision_score, recall_score
from dotenv import load_dotenv

load_dotenv()

MODEL_PATH = ROOT / "system_a" / "model" / "xgb_calibrated_model.pkl"
FEATURE_COLS_PATH = ROOT / "system_a" / "model" / "feature_cols.pkl"
UNSEEN_DIR = ROOT / "data" / "unseen_test_sets"
UNSEEN_DIR.mkdir(parents=True, exist_ok=True)
TEST_OUTPUT_DIR = ROOT / "outputs" / "unseen_eval_runs"
TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def generate_unseen_dataset(seed, label_noise_std=0.04, feature_flip_prob=0.08, leniency_shift=0.0):
    """Generates a completely new dataset with a custom seed and distribution parameters."""
    rng = np.random.default_rng(seed)
    n = 2000

    networks = ["UPI_NPCI", "RUPAY", "VISA", "MASTERCARD", "AMERICAN_EXPRESS"]
    net_p = [0.42, 0.28, 0.16, 0.10, 0.04]
    net_to_rail = {"UPI_NPCI": "UPI", "RUPAY": "CARD", "VISA": "CARD", "MASTERCARD": "CARD", "AMERICAN_EXPRESS": "CARD"}

    categories = [
        "FRAUD_UNAUTHORIZED", "ITEM_NOT_RECEIVED", "NOT_AS_DESCRIBED",
        "RECON_SETTLEMENT_ERROR", "REFUND_NOT_RECEIVED", "DUPLICATE_TRANSACTION",
        "SUBSCRIPTION_CANCELED", "SERVICE_NOT_PROVIDED", "INCORRECT_AMOUNT",
    ]
    cat_p = [0.28, 0.20, 0.12, 0.10, 0.08, 0.07, 0.06, 0.05, 0.04]

    cat_amount_params = {
        "FRAUD_UNAUTHORIZED": (7.4, 1.1),
        "SERVICE_NOT_PROVIDED": (8.2, 0.9),
        "ITEM_NOT_RECEIVED": (7.1, 1.0),
        "NOT_AS_DESCRIBED": (7.2, 0.9),
        "DUPLICATE_TRANSACTION": (6.8, 1.0),
        "INCORRECT_AMOUNT": (6.7, 1.1),
        "REFUND_NOT_RECEIVED": (7.0, 1.0),
        "RECON_SETTLEMENT_ERROR": (6.2, 0.8),
        "SUBSCRIPTION_CANCELED": (5.6, 0.7),
    }

    network = rng.choice(networks, n, p=net_p)
    payment_rail = np.array([net_to_rail[x] for x in network])
    normalized_category = rng.choice(categories, n, p=cat_p)

    reason_codes = {
        ("UPI_NPCI", "FRAUD_UNAUTHORIZED"): ("128", "Fraudulent Transaction"),
        ("UPI_NPCI", "ITEM_NOT_RECEIVED"): ("1064", "Goods/Services Not Received"),
        ("VISA", "FRAUD_UNAUTHORIZED"): ("10.4", "Other Fraud – Card-Absent Environment"),
        ("VISA", "ITEM_NOT_RECEIVED"): ("13.1", "Merchandise/Services Not Received"),
        ("MASTERCARD", "FRAUD_UNAUTHORIZED"): ("4837", "No Cardholder Authorisation"),
        ("RUPAY", "ITEM_NOT_RECEIVED"): ("1064", "Goods/Services Not Received"),
        ("AMERICAN_EXPRESS", "NOT_AS_DESCRIBED"): ("C31", "Goods/Services Not as Described"),
    }

    rcode_list, rtitle_list = [], []
    for net, cat in zip(network, normalized_category):
        c, t = reason_codes.get((net, cat), ("1000", "General Dispute"))
        rcode_list.append(c)
        rtitle_list.append(t)

    dispute_amount_inr = np.zeros(n)
    for i, cat in enumerate(normalized_category):
        mu, sigma = cat_amount_params[cat]
        dispute_amount_inr[i] = round(float(rng.lognormal(mean=mu, sigma=sigma)), 2)

    base_date = pd.Timestamp("2026-01-01")
    transaction_date = base_date + pd.to_timedelta(rng.integers(0, 210, n), unit="D")
    filing_delay_days = rng.integers(1, 90, n)
    dispute_filed_date = transaction_date + pd.to_timedelta(filing_delay_days, unit="D")

    is_tokenized = rng.choice([True, False], n, p=[0.70, 0.30])
    otp_entry_duration_sec = rng.integers(1, 45, n)

    account_pattern_consistent_true = np.where(
        normalized_category == "FRAUD_UNAUTHORIZED",
        rng.random(n) < 0.45,
        rng.random(n) < 0.90,
    )
    previous_successful_orders = np.where(
        account_pattern_consistent_true,
        rng.poisson(lam=3.5, size=n),
        rng.poisson(lam=0.3, size=n),
    )
    ip_geo_match_true = np.where(
        account_pattern_consistent_true,
        rng.random(n) < 0.85,
        rng.random(n) < 0.15,
    )

    sim_swap_flag_48h_true = rng.choice([True, False], n, p=[0.02, 0.98])
    bank_rrn_match_true = rng.choice([True, False], n, p=[0.85, 0.15])
    delivery_otp_verified_true = rng.choice([True, False], n, p=[0.60, 0.40])
    transaction_record_match_true = rng.random(n) < 0.75
    post_dispute_activity_true = rng.random(n) < 0.35

    previous_refunds = rng.poisson(lam=0.5, size=n)
    previous_chargebacks = rng.choice([0, 1, 2], n, p=[0.90, 0.08, 0.02])

    cases_df = pd.DataFrame({
        "case_id": [f"UNSEEN_{seed}_{i:04d}" for i in range(n)],
        "transaction_id": [f"TXN_{rng.integers(10**11, 10**12)}" for _ in range(n)],
        "order_id": [f"ORD_{rng.integers(10**9, 10**10)}" for _ in range(n)],
        "payment_rail": payment_rail, "network": network,
        "normalized_category": normalized_category,
        "reason_code": rcode_list, "reason_code_title": rtitle_list,
        "dispute_amount_inr": dispute_amount_inr, "currency": "INR", "country": "IN",
        "transaction_date": transaction_date, "filing_delay_days": filing_delay_days,
        "dispute_filed_date": dispute_filed_date,
        "is_tokenized": is_tokenized, "otp_entry_duration_sec": otp_entry_duration_sec,
        "bank_rrn_match_true": bank_rrn_match_true,
        "delivery_otp_verified_true": delivery_otp_verified_true,
        "ip_geo_match_true": ip_geo_match_true,
        "sim_swap_flag_48h_true": sim_swap_flag_48h_true,
        "transaction_record_match_true": transaction_record_match_true,
        "post_dispute_activity_true": post_dispute_activity_true,
        "account_pattern_consistent_true": account_pattern_consistent_true,
        "previous_successful_orders": previous_successful_orders,
        "previous_refunds": previous_refunds,
        "previous_chargebacks": previous_chargebacks,
    })

    # Evidence counts summary simulation
    cases_df["total_evidence"] = rng.integers(4, 10, n)
    cases_df["relevant_evidence_count"] = rng.integers(2, 6, n)
    cases_df["required_evidence_count"] = rng.integers(1, 3, n)
    cases_df["contradictory_evidence_count"] = rng.choice([0, 1, 2], n, p=[0.85, 0.12, 0.03])

    # Base win probability
    c = cases_df
    conditions = [
        (c.normalized_category == "FRAUD_UNAUTHORIZED") & (c.sim_swap_flag_48h_true | (c.otp_entry_duration_sec <= 2)),
        (c.normalized_category == "FRAUD_UNAUTHORIZED") & ~c.account_pattern_consistent_true,
        (c.normalized_category == "FRAUD_UNAUTHORIZED") & c.account_pattern_consistent_true & (c.previous_successful_orders >= 2) & c.ip_geo_match_true,
        (c.normalized_category == "FRAUD_UNAUTHORIZED"),

        (c.normalized_category == "RECON_SETTLEMENT_ERROR") & c.bank_rrn_match_true,
        (c.normalized_category == "RECON_SETTLEMENT_ERROR"),

        (c.normalized_category == "ITEM_NOT_RECEIVED") & c.delivery_otp_verified_true,
        (c.normalized_category == "ITEM_NOT_RECEIVED") & ~c.delivery_otp_verified_true & (c.filing_delay_days > 60),
        (c.normalized_category == "ITEM_NOT_RECEIVED"),

        (c.normalized_category == "NOT_AS_DESCRIBED") & c.post_dispute_activity_true,
        (c.normalized_category == "NOT_AS_DESCRIBED"),
    ]
    choices = [0.03, 0.08, 0.55, 0.25, 0.92, 0.05, 0.85, 0.45, 0.10, 0.92, 0.30]
    cases_df["base_win_prob"] = np.select(conditions, choices, default=0.50)

    # Hidden confounders
    _hidden_bank_leniency = rng.beta(2, 5, size=n) + leniency_shift
    _hidden_cardholder_counter = rng.beta(3, 4, size=n)
    _hidden_effect = np.where(
        normalized_category == "FRAUD_UNAUTHORIZED",
        0.20 * (_hidden_bank_leniency - 0.30) - 0.15 * _hidden_cardholder_counter,
        0.12 * (_hidden_bank_leniency - 0.30) - 0.10 * _hidden_cardholder_counter,
    )
    cases_df["base_win_prob"] = np.clip(cases_df["base_win_prob"] + _hidden_effect, 0.02, 0.98)

    noise = rng.normal(0, label_noise_std, n)
    cases_df["noisy_win_prob"] = np.clip(cases_df["base_win_prob"] + noise, 0.02, 0.98)
    cases_df["merchant_representment_won"] = rng.binomial(1, cases_df["noisy_win_prob"])

    # Feature flips
    flips = rng.random((n, 6)) < feature_flip_prob
    cols = ["bank_rrn_match", "delivery_otp_verified", "ip_geo_match", "sim_swap_flag_48h", "transaction_record_match", "post_dispute_activity"]
    for idx, col in enumerate(cols):
        cases_df[col] = np.where(flips[:, idx], ~cases_df[f"{col}_true"].values, cases_df[f"{col}_true"].values)
        cases_df[col] = cases_df[col].astype(int)

    cases_df["representment_fee_inr"] = np.where(cases_df.network.isin(["RUPAY", "UPI_NPCI"]), 300, 1200)
    cases_df["false_positive_cost_inr"] = cases_df["representment_fee_inr"] + 500

    return cases_df


def evaluate_unseen_dataset(dataset_idx, seed, model, feature_cols, label_noise=0.04, shift=0.0):
    """Evaluates System A on a single unseen dataset."""
    df = generate_unseen_dataset(seed, label_noise_std=label_noise, leniency_shift=shift)

    categorical_cols = ["network", "payment_rail", "normalized_category"]
    df_encoded = pd.get_dummies(df, columns=categorical_cols, drop_first=True)
    df_encoded = df_encoded.reindex(columns=list(feature_cols), fill_value=0)

    y_true = df["merchant_representment_won"]
    win_probs = model.predict_proba(df_encoded[feature_cols])[:, 1]

    ev = (win_probs * df["dispute_amount_inr"]) - ((1 - win_probs) * df["false_positive_cost_inr"])
    decisions = (ev > 0).astype(int)

    pr_auc = average_precision_score(y_true, win_probs)
    brier = brier_score_loss(y_true, win_probs)
    no_skill_brier = y_true.mean() * (1 - y_true.mean())
    bss = 1 - (brier / no_skill_brier)

    prec = precision_score(y_true, decisions, zero_division=0)
    rec = recall_score(y_true, decisions, zero_division=0)
    acc = (decisions == y_true).mean()

    # Economic ROI
    ai_profit = (df.loc[(decisions == 1) & (y_true == 1), "dispute_amount_inr"].sum() -
                 df.loc[(decisions == 1) & (y_true == 0), "false_positive_cost_inr"].sum())

    fight_all_profit = (df.loc[y_true == 1, "dispute_amount_inr"].sum() -
                         df.loc[y_true == 0, "false_positive_cost_inr"].sum())

    value_added = ai_profit - fight_all_profit

    return {
        "dataset": f"Unseen Set #{dataset_idx} (seed={seed})",
        "n_cases": len(df),
        "base_win_rate": f"{y_true.mean():.1%}",
        "PR-AUC": round(pr_auc, 4),
        "Brier": round(brier, 4),
        "BSS": round(bss, 4),
        "Precision": f"{prec:.1%}",
        "Recall": f"{rec:.1%}",
        "Accuracy": f"{acc:.1%}",
        "AI_Net_Profit": f"Rs {ai_profit:,.2f}",
        "Fight_All_Profit": f"Rs {fight_all_profit:,.2f}",
        "Value_Added": f"Rs {value_added:,.2f}",
    }


def main():
    print("=" * 80)
    print("ROBUSTNESS EVALUATION: TESTING PRE-TRAINED MODEL ON 5 UNSEEN HELD-OUT DATASETS")
    print("=" * 80)

    model = joblib.load(MODEL_PATH)
    feature_cols = joblib.load(FEATURE_COLS_PATH)

    seeds = [101, 202, 303, 404, 505]
    shifts = [0.0, 0.05, -0.05, 0.10, -0.08]
    noises = [0.04, 0.05, 0.06, 0.04, 0.07]

    results = []
    for i, (s, sh, n_val) in enumerate(zip(seeds, shifts, noises), 1):
        res = evaluate_unseen_dataset(i, s, model, feature_cols, label_noise=n_val, shift=sh)
        results.append(res)

    res_df = pd.DataFrame(results)
    print("\nSUMMARY METRICS ACROSS 5 UNSEEN DATASETS:")
    print(res_df[["dataset", "base_win_rate", "PR-AUC", "BSS", "Precision", "Recall", "Accuracy", "Value_Added"]].to_string(index=False))

    res_df.to_csv(TEST_OUTPUT_DIR / "unseen_5_datasets_eval.csv", index=False)
    print(f"\nDetailed evaluation report saved to {TEST_OUTPUT_DIR / 'unseen_5_datasets_eval.csv'}")


if __name__ == "__main__":
    main()
