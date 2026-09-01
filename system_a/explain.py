"""
SYSTEM A — FEATURE IMPORTANCE ANALYSIS

Computes feature importance using XGBoost's built-in gain-based
importance and permutation importance on the held-out test set.

Produces:
  1. A global feature importance summary (gain + permutation)
  2. Per-category top-feature breakdowns (verifies the model learned
     domain-appropriate patterns, not spurious correlations)
  3. Saved importance bar plot

Run from project root (after train.py):
    python system_a/explain.py
"""

from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance

ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / "system_a" / "model"
DATA_PATH = ROOT / "data" / "chargeback_cases_v6.csv" if (ROOT / "data" / "chargeback_cases_v6.csv").exists() else ROOT / "data" / "chargeback_cases.csv"
OUTPUT_DIR = ROOT / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------------
# 1. LOAD MODEL + DATA
# ------------------------------------------------------------------

base_model = joblib.load(MODEL_DIR / "xgb_base_model.pkl")
feature_cols = joblib.load(MODEL_DIR / "feature_cols.pkl")
print(f"Loaded base model and {len(feature_cols)} features")

df = pd.read_csv(DATA_PATH)
original_categories = df[["case_id", "normalized_category"]].copy()

categorical_cols = ["network", "payment_rail", "normalized_category"]
boolean_cols = [
    "is_tokenized", "bank_rrn_match", "delivery_otp_verified", "ip_geo_match",
    "sim_swap_flag_48h", "transaction_record_match", "post_dispute_activity",
]
for col in boolean_cols:
    df[col] = df[col].astype(int)

df_encoded = pd.get_dummies(df, columns=categorical_cols, drop_first=True)
df_encoded = df_encoded.reindex(columns=list(feature_cols) + ["case_id", "dataset_split",
                                                               "merchant_representment_won"], fill_value=0)
df_encoded = df_encoded.merge(original_categories, on="case_id", how="left")

test_df = df_encoded[df_encoded["dataset_split"] == "test"].copy()
X_test = test_df[feature_cols]
y_test = test_df["merchant_representment_won"]

print(f"Test set: {len(X_test)} cases")

# ------------------------------------------------------------------
# 2. GAIN-BASED IMPORTANCE (XGBoost built-in)
# ------------------------------------------------------------------

print("\nComputing gain-based feature importance...")
gain_importance = base_model.get_booster().get_score(importance_type="gain")

# Map internal feature names (f0, f1, ...) back to actual names
booster_fnames = base_model.get_booster().feature_names
if booster_fnames is None:
    # XGBoost uses f0..fN internally if feature_names not set
    booster_fnames = [f"f{i}" for i in range(len(feature_cols))]
    fname_map = dict(zip(booster_fnames, feature_cols))
else:
    fname_map = dict(zip(booster_fnames, booster_fnames))

gain_df = pd.DataFrame([
    {"feature": fname_map.get(k, k), "gain": v}
    for k, v in gain_importance.items()
]).sort_values("gain", ascending=False)

print("\n" + "=" * 60)
print("GLOBAL FEATURE IMPORTANCE (XGBoost gain)")
print("=" * 60)
print(gain_df.head(15).to_string(index=False))

# ------------------------------------------------------------------
# 3. PERMUTATION IMPORTANCE (model-agnostic, on test set)
# ------------------------------------------------------------------

print("\nComputing permutation importance (this may take a moment)...")
perm_result = permutation_importance(
    base_model, X_test, y_test, n_repeats=10, random_state=42, scoring="average_precision",
)

perm_df = pd.DataFrame({
    "feature": feature_cols,
    "perm_importance_mean": perm_result.importances_mean,
    "perm_importance_std": perm_result.importances_std,
}).sort_values("perm_importance_mean", ascending=False)

print("\n" + "=" * 60)
print("PERMUTATION IMPORTANCE (mean drop in PR-AUC)")
print("=" * 60)
print(perm_df.head(15).to_string(index=False))

# ------------------------------------------------------------------
# 4. PER-CATEGORY TOP FEATURES
# ------------------------------------------------------------------

# Expected top features per category (domain knowledge validation)
EXPECTED_TOP_FEATURES = {
    "FRAUD_UNAUTHORIZED": ["account_pattern_consistent_true", "ip_geo_match", "sim_swap_flag_48h",
                           "previous_successful_orders", "otp_entry_duration_sec"],
    "ITEM_NOT_RECEIVED": ["delivery_otp_verified", "filing_delay_days"],
    "NOT_AS_DESCRIBED": ["post_dispute_activity"],
    "RECON_SETTLEMENT_ERROR": ["bank_rrn_match"],
    "DUPLICATE_TRANSACTION": ["transaction_record_match"],
    "INCORRECT_AMOUNT": ["transaction_record_match"],
    "REFUND_NOT_RECEIVED": ["transaction_record_match"],
    "SERVICE_NOT_PROVIDED": ["post_dispute_activity"],
    "SUBSCRIPTION_CANCELED": ["relevant_evidence_count"],
}

print("\n" + "=" * 60)
print("PER-CATEGORY TOP FEATURES (domain validation)")
print("=" * 60)

categories_in_test = test_df["normalized_category"].unique()
domain_hits = 0
domain_total = 0

for cat in sorted(categories_in_test):
    mask = test_df["normalized_category"].values == cat
    n_cat = mask.sum()
    if n_cat < 10:
        continue

    # Per-category permutation importance
    cat_perm = permutation_importance(
        base_model, X_test[mask], y_test[mask],
        n_repeats=5, random_state=42, scoring="accuracy",
    )
    cat_df = pd.DataFrame({
        "feature": feature_cols,
        "importance": cat_perm.importances_mean,
    }).sort_values("importance", ascending=False)

    top_5 = cat_df.head(5)["feature"].tolist()
    expected = EXPECTED_TOP_FEATURES.get(cat, [])

    # Check how many expected features appear in top 5
    hits = [f for f in expected if any(f in t for t in top_5)]
    if expected:
        domain_total += 1
        if hits:
            domain_hits += 1

    print(f"\n  {cat} ({n_cat} cases):")
    print(f"    Top 5: {', '.join(top_5)}")
    if expected:
        status = "[OK]" if hits else "[MISS]"
        print(f"    Expected: {', '.join(expected[:3])}")
        print(f"    {status} Domain match: {len(hits)}/{min(len(expected), 5)} expected features in top 5")

if domain_total > 0:
    print(f"\n  Overall domain alignment: {domain_hits}/{domain_total} categories "
          f"({domain_hits/domain_total:.0%}) have expected features in top 5")

# ------------------------------------------------------------------
# 5. SAVE PLOTS
# ------------------------------------------------------------------

# Combined importance plot (gain + permutation)
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# Gain plot
top_gain = gain_df.head(15)
ax1.barh(range(len(top_gain)), top_gain["gain"].values, color="#2196F3")
ax1.set_yticks(range(len(top_gain)))
ax1.set_yticklabels(top_gain["feature"].values)
ax1.invert_yaxis()
ax1.set_xlabel("Mean gain")
ax1.set_title("XGBoost Gain Importance (top 15)")

# Permutation plot
top_perm = perm_df.head(15)
ax2.barh(range(len(top_perm)), top_perm["perm_importance_mean"].values, color="#FF9800",
         xerr=top_perm["perm_importance_std"].values)
ax2.set_yticks(range(len(top_perm)))
ax2.set_yticklabels(top_perm["feature"].values)
ax2.invert_yaxis()
ax2.set_xlabel("Mean drop in PR-AUC")
ax2.set_title("Permutation Importance (top 15)")

fig.suptitle("Feature Importance Analysis", fontsize=14)
fig.tight_layout()
fig.savefig(OUTPUT_DIR / "feature_importance.png", dpi=150)
plt.close(fig)
print(f"\nImportance plot saved to {OUTPUT_DIR / 'feature_importance.png'}")
