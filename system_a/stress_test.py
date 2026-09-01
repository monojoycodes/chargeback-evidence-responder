"""
SYSTEM A — DISTRIBUTION-SHIFT STRESS TEST

Loads the model trained on the original synthetic data, generates new
synthetic datasets with deliberately shifted parameters, and measures
how much the model degrades WITHOUT retraining.

This answers the question: "Did the model learn meaningful feature
relationships, or did it just memorise the specific parameter values
used during data generation?"

Three scenarios:
  1. Optimistic shift  — fraud win rate higher, less noise
  2. Neutral shift     — different category mix, same difficulty
  3. Pessimistic shift — fraud win rate lower, more noise, heavier fraud share

Run from project root (after train.py):
    python system_a/stress_test.py
"""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, brier_score_loss, precision_score, recall_score

ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / "system_a" / "model"
OUTPUT_DIR = ROOT / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------------
# Load the production model + feature schema
# ------------------------------------------------------------------

model = joblib.load(MODEL_DIR / "xgb_calibrated_model.pkl")
feature_cols = joblib.load(MODEL_DIR / "feature_cols.pkl")


# ------------------------------------------------------------------
# Minimal case generator (no evidence — we only need case-level data)
# ------------------------------------------------------------------

NETWORKS = ["UPI_NPCI", "RUPAY", "VISA", "MASTERCARD", "AMERICAN_EXPRESS"]
NETWORK_TO_RAIL = {
    "UPI_NPCI": "UPI", "RUPAY": "CARD", "VISA": "CARD",
    "MASTERCARD": "CARD", "AMERICAN_EXPRESS": "CARD",
}
CATEGORIES = [
    "FRAUD_UNAUTHORIZED", "ITEM_NOT_RECEIVED", "NOT_AS_DESCRIBED",
    "RECON_SETTLEMENT_ERROR", "REFUND_NOT_RECEIVED", "DUPLICATE_TRANSACTION",
    "SUBSCRIPTION_CANCELED", "SERVICE_NOT_PROVIDED", "INCORRECT_AMOUNT",
]
CATEGORY_AMOUNT_LOGMEAN = {
    "FRAUD_UNAUTHORIZED": 7.5, "SERVICE_NOT_PROVIDED": 7.8,
    "ITEM_NOT_RECEIVED": 7.0, "NOT_AS_DESCRIBED": 7.0,
    "DUPLICATE_TRANSACTION": 7.0, "INCORRECT_AMOUNT": 7.0,
    "REFUND_NOT_RECEIVED": 7.0, "RECON_SETTLEMENT_ERROR": 6.3,
    "SUBSCRIPTION_CANCELED": 5.5,
}


def generate_shifted_cases(
    n: int,
    seed: int,
    network_probs: list[float],
    category_probs: list[float],
    feature_flip_prob: float,
    label_noise_std: float,
    fraud_base_wins: tuple[float, float, float, float],
    hidden_confounder_scale: float = 1.0,
) -> pd.DataFrame:
    """Generate a shifted synthetic dataset.

    Parameters
    ----------
    fraud_base_wins : 4-tuple
        (sim_swap_case, inconsistent_account, strong_evidence, thin_evidence)
        base win probabilities for FRAUD_UNAUTHORIZED sub-conditions.
    """
    rng_local = np.random.default_rng(seed)
    np.random.seed(seed)

    network = np.random.choice(NETWORKS, n, p=network_probs)
    payment_rail = np.array([NETWORK_TO_RAIL[x] for x in network])
    normalized_category = np.random.choice(CATEGORIES, n, p=category_probs)

    amount_logmean = np.array([CATEGORY_AMOUNT_LOGMEAN[c] for c in normalized_category])
    dispute_amount_inr = np.round(np.random.lognormal(mean=amount_logmean, sigma=1.2), 2)

    filing_delay_days = np.random.randint(1, 90, n)
    is_tokenized = np.random.choice([True, False], n, p=[0.7, 0.3])
    otp_entry_duration_sec = np.random.randint(1, 45, n)

    account_pattern_consistent_true = np.where(
        normalized_category == "FRAUD_UNAUTHORIZED",
        np.random.random(n) < 0.45,
        np.random.random(n) < 0.90,
    )
    previous_successful_orders = np.where(
        account_pattern_consistent_true,
        np.random.poisson(lam=3.5, size=n),
        np.random.poisson(lam=0.3, size=n),
    )
    ip_geo_match_true = np.where(
        account_pattern_consistent_true,
        np.random.random(n) < 0.88,
        np.random.random(n) < 0.15,
    )
    sim_swap_flag_48h_true = np.random.choice([True, False], n, p=[0.02, 0.98])
    bank_rrn_match_true = np.random.choice([True, False], n, p=[0.85, 0.15])
    delivery_otp_verified_true = np.random.choice([True, False], n, p=[0.6, 0.4])
    transaction_record_match_true = np.random.random(n) < 0.75
    post_dispute_activity_true = np.random.random(n) < 0.35
    previous_refunds = np.random.poisson(lam=0.5, size=n)
    previous_chargebacks = np.random.choice([0, 1, 2], n, p=[0.90, 0.08, 0.02])

    # Evidence summary (simplified — fixed counts since we skip evidence generation)
    total_evidence = np.random.randint(4, 10, n)
    relevant_evidence_count = np.random.randint(2, 7, n)
    required_evidence_count = np.random.randint(1, 3, n)
    contradictory_evidence_count = np.random.binomial(1, 0.03, n)

    df = pd.DataFrame({
        "payment_rail": payment_rail, "network": network,
        "normalized_category": normalized_category,
        "dispute_amount_inr": dispute_amount_inr,
        "filing_delay_days": filing_delay_days,
        "is_tokenized": is_tokenized,
        "otp_entry_duration_sec": otp_entry_duration_sec,
        "bank_rrn_match": bank_rrn_match_true,  # will be noised below
        "delivery_otp_verified": delivery_otp_verified_true,
        "ip_geo_match": ip_geo_match_true,
        "sim_swap_flag_48h": sim_swap_flag_48h_true,
        "transaction_record_match": transaction_record_match_true,
        "post_dispute_activity": post_dispute_activity_true,
        "account_pattern_consistent_true": account_pattern_consistent_true,
        "previous_successful_orders": previous_successful_orders,
        "previous_refunds": previous_refunds,
        "previous_chargebacks": previous_chargebacks,
        "total_evidence": total_evidence,
        "relevant_evidence_count": relevant_evidence_count,
        "required_evidence_count": required_evidence_count,
        "contradictory_evidence_count": contradictory_evidence_count,
    })

    # --- WIN PROBABILITY (same structure, shifted parameters for fraud) ---
    c = df
    fw = fraud_base_wins
    conditions = [
        (c.normalized_category == "FRAUD_UNAUTHORIZED") & (c.sim_swap_flag_48h | (c.otp_entry_duration_sec <= 2)),
        (c.normalized_category == "FRAUD_UNAUTHORIZED") & ~c.account_pattern_consistent_true,
        (c.normalized_category == "FRAUD_UNAUTHORIZED") & c.account_pattern_consistent_true & (c.previous_successful_orders >= 2) & c.ip_geo_match,
        (c.normalized_category == "FRAUD_UNAUTHORIZED"),
        (c.normalized_category == "RECON_SETTLEMENT_ERROR") & c.bank_rrn_match,
        (c.normalized_category == "RECON_SETTLEMENT_ERROR"),
        (c.normalized_category == "ITEM_NOT_RECEIVED") & c.delivery_otp_verified,
        (c.normalized_category == "ITEM_NOT_RECEIVED") & ~c.delivery_otp_verified & (c.filing_delay_days > 60),
        (c.normalized_category == "ITEM_NOT_RECEIVED"),
        (c.normalized_category == "NOT_AS_DESCRIBED") & c.post_dispute_activity,
        (c.normalized_category == "NOT_AS_DESCRIBED"),
        (c.normalized_category == "SERVICE_NOT_PROVIDED") & c.post_dispute_activity,
        (c.normalized_category == "SERVICE_NOT_PROVIDED"),
        (c.normalized_category == "DUPLICATE_TRANSACTION") & c.transaction_record_match,
        (c.normalized_category == "DUPLICATE_TRANSACTION"),
        (c.normalized_category == "INCORRECT_AMOUNT") & c.transaction_record_match,
        (c.normalized_category == "INCORRECT_AMOUNT"),
        (c.normalized_category == "REFUND_NOT_RECEIVED") & c.transaction_record_match,
        (c.normalized_category == "REFUND_NOT_RECEIVED"),
        (c.normalized_category == "SUBSCRIPTION_CANCELED") & (c.relevant_evidence_count >= 3),
        (c.normalized_category == "SUBSCRIPTION_CANCELED"),
    ]
    choices = [
        fw[0], fw[1], fw[2], fw[3],  # fraud (shifted)
        0.92, 0.05,
        0.85, 0.45, 0.10,
        0.92, 0.30,
        0.88, 0.18,
        0.90, 0.15,
        0.90, 0.12,
        0.90, 0.10,
        0.75, 0.20,
    ]
    df["base_win_prob"] = np.select(conditions, choices, default=0.50)

    # Hidden confounders (same structure, scaled intensity)
    hidden_bank = np.random.beta(2, 5, size=n)
    hidden_counter = np.random.beta(3, 4, size=n)
    hidden_effect = np.where(
        normalized_category == "FRAUD_UNAUTHORIZED",
        hidden_confounder_scale * (0.20 * (hidden_bank - 0.30) - 0.15 * hidden_counter),
        hidden_confounder_scale * (0.12 * (hidden_bank - 0.30) - 0.10 * hidden_counter),
    )
    df["base_win_prob"] = np.clip(df["base_win_prob"] + hidden_effect, 0.02, 0.98)

    noise = np.random.normal(0, label_noise_std, n)
    df["noisy_win_prob"] = np.clip(df["base_win_prob"] + noise, 0.02, 0.98)
    df["merchant_representment_won"] = np.random.binomial(1, df["noisy_win_prob"])

    # Noisy observed features
    def flip(arr, p=feature_flip_prob):
        return np.where(np.random.random(len(arr)) < p, ~arr, arr)

    for col in ["bank_rrn_match", "delivery_otp_verified", "ip_geo_match",
                "sim_swap_flag_48h", "transaction_record_match", "post_dispute_activity"]:
        df[col] = flip(df[col].values)

    # Economic fields
    df["representment_fee_inr"] = np.where(df.network.isin(["RUPAY", "UPI_NPCI"]), 300, 1200)
    df["false_positive_cost_inr"] = df["representment_fee_inr"] + 500

    return df


def evaluate_on_shifted(df: pd.DataFrame, label: str) -> dict:
    """Run the saved model on a shifted dataframe and report metrics."""
    categorical_cols = ["network", "payment_rail", "normalized_category"]
    boolean_cols = [
        "is_tokenized", "bank_rrn_match", "delivery_otp_verified", "ip_geo_match",
        "sim_swap_flag_48h", "transaction_record_match", "post_dispute_activity",
    ]
    for col in boolean_cols:
        df[col] = df[col].astype(int)

    df_enc = pd.get_dummies(df, columns=categorical_cols, drop_first=True)
    df_enc = df_enc.reindex(columns=feature_cols, fill_value=0)

    y = df["merchant_representment_won"]
    probs = model.predict_proba(df_enc)[:, 1]

    ev = probs * df["dispute_amount_inr"].values - (1 - probs) * df["false_positive_cost_inr"].values
    decisions = (ev > 0).astype(int)

    pr_auc = average_precision_score(y, probs)
    brier = brier_score_loss(y, probs)
    prec = precision_score(y, decisions, zero_division=0)
    rec = recall_score(y, decisions, zero_division=0)

    return {"label": label, "PR-AUC": pr_auc, "Brier": brier,
            "Precision": prec, "Recall": rec, "N": len(df)}


# ------------------------------------------------------------------
# Define scenarios
# ------------------------------------------------------------------

SCENARIOS = {
    "Optimistic": dict(
        seed=100,
        network_probs=[0.35, 0.25, 0.20, 0.12, 0.08],
        category_probs=[0.22, 0.22, 0.14, 0.10, 0.08, 0.08, 0.07, 0.05, 0.04],
        feature_flip_prob=0.06,
        label_noise_std=0.03,
        fraud_base_wins=(0.05, 0.12, 0.60, 0.30),
        hidden_confounder_scale=0.8,
    ),
    "Neutral shift": dict(
        seed=200,
        network_probs=[0.30, 0.35, 0.18, 0.10, 0.07],
        category_probs=[0.30, 0.18, 0.14, 0.08, 0.08, 0.07, 0.06, 0.05, 0.04],
        feature_flip_prob=0.08,
        label_noise_std=0.04,
        fraud_base_wins=(0.03, 0.08, 0.50, 0.22),
        hidden_confounder_scale=1.0,
    ),
    "Pessimistic": dict(
        seed=300,
        network_probs=[0.45, 0.25, 0.15, 0.10, 0.05],
        category_probs=[0.38, 0.16, 0.10, 0.08, 0.07, 0.06, 0.06, 0.05, 0.04],
        feature_flip_prob=0.12,
        label_noise_std=0.06,
        fraud_base_wins=(0.02, 0.05, 0.45, 0.18),
        hidden_confounder_scale=1.3,
    ),
}

# ------------------------------------------------------------------
# Run stress test
# ------------------------------------------------------------------

if __name__ == "__main__":
    N_CASES = 3000
    results = []

    print("=" * 65)
    print("DISTRIBUTION-SHIFT STRESS TEST")
    print("=" * 65)
    print(f"Model trained on original data. Testing on {N_CASES} shifted cases each.\n")

    for name, params in SCENARIOS.items():
        print(f"  Generating '{name}' scenario (seed={params['seed']})...")
        shifted_df = generate_shifted_cases(n=N_CASES, **params)
        result = evaluate_on_shifted(shifted_df, label=name)
        results.append(result)

    print("\n" + "-" * 65)
    print(f"{'Scenario':<20} {'PR-AUC':>8} {'Brier':>8} {'Precision':>10} {'Recall':>8}")
    print("-" * 65)
    for r in results:
        print(f"{r['label']:<20} {r['PR-AUC']:>8.4f} {r['Brier']:>8.4f} {r['Precision']:>9.2%} {r['Recall']:>7.2%}")
    print("-" * 65)

    # Interpretation
    prauc_values = [r["PR-AUC"] for r in results]
    worst_drop = min(prauc_values)
    print(f"\nWorst-case PR-AUC: {worst_drop:.4f}")
    if worst_drop > 0.60:
        print("[PASS] Model shows GRACEFUL degradation -- learned generalizable patterns.")
    elif worst_drop > 0.45:
        print("[WARN] Model shows MODERATE degradation -- partially generalizable.")
    else:
        print("[FAIL] Model shows SEVERE degradation -- likely memorised generative rules.")

    # Save results
    results_df = pd.DataFrame(results)
    results_df.to_csv(OUTPUT_DIR / "stress_test_results.csv", index=False)
    print(f"\nResults saved to {OUTPUT_DIR / 'stress_test_results.csv'}")
