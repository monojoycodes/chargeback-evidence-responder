"""
SYSTEM A — EVALUATION

Loads the model train.py saved (does not retrain), rebuilds the
held-out test set the same way train.py built the training set, and
reports every metric the project needs:

  Part 1: Raw classifier quality (PR-AUC, Brier, Brier Skill Score)
  Part 2: Calibration-by-decile table + saved plot
  Part 3: Decision precision/recall with EV threshold
  Part 4: Three-way ROI baseline (concede-all / fight-all / AI strategy)
  Part 5: Oracle ceiling (% of theoretical max captured)
  Part 6: Error concentration by category

Run this after train.py, from the project root:
    python system_a/evaluate.py
"""

from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")  # non-interactive backend for saving plots
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    precision_score,
    recall_score,
)

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "system_a" / "model" / "xgb_calibrated_model.pkl"
FEATURE_COLS_PATH = ROOT / "system_a" / "model" / "feature_cols.pkl"
DATA_PATH = ROOT / "data" / "chargeback_cases_v6.csv" if (ROOT / "data" / "chargeback_cases_v6.csv").exists() else ROOT / "data" / "chargeback_cases.csv"
OUTPUT_DIR = ROOT / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------------
# 1. LOAD MODEL + FEATURE LIST
# ------------------------------------------------------------------

model = joblib.load(MODEL_PATH)
feature_cols = joblib.load(FEATURE_COLS_PATH)
print(f"Loaded model from {MODEL_PATH.name}")
print(f"Feature count: {len(feature_cols)}")

# ------------------------------------------------------------------
# 2. REBUILD THE TEST SET — must match train.py's preprocessing
# ------------------------------------------------------------------

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

# Guard against column mismatches between train and eval data
extra_cols_needed = [
    c for c in ["case_id", "dataset_split", "merchant_representment_won",
                "dispute_amount_inr", "false_positive_cost_inr"]
    if c not in feature_cols
]
df_encoded = df_encoded.reindex(columns=list(feature_cols) + extra_cols_needed, fill_value=0)
df_encoded = df_encoded.merge(original_categories, on="case_id", how="left")

test_df = df_encoded[df_encoded["dataset_split"] == "test"].copy()
X_test = test_df[feature_cols]
y_test = test_df["merchant_representment_won"]

# ------------------------------------------------------------------
# 3. INFERENCE + EV DECISION
# ------------------------------------------------------------------

test_df["predicted_win_prob"] = model.predict_proba(X_test)[:, 1]
test_df["expected_value"] = (
    test_df["predicted_win_prob"] * test_df["dispute_amount_inr"]
    - (1 - test_df["predicted_win_prob"]) * test_df["false_positive_cost_inr"]
)
test_df["model_decision_to_fight"] = (test_df["expected_value"] > 0).astype(int)

# ------------------------------------------------------------------
# PART 1: RAW CLASSIFIER QUALITY
# ------------------------------------------------------------------

pr_auc = average_precision_score(y_test, test_df["predicted_win_prob"])
brier = brier_score_loss(y_test, test_df["predicted_win_prob"])
no_skill_brier = y_test.mean() * (1 - y_test.mean())
brier_skill_score = 1 - (brier / no_skill_brier)

print("\n" + "=" * 60)
print("PART 1: RAW CLASSIFIER QUALITY")
print("=" * 60)
print(f"PR-AUC:              {pr_auc:.4f}  (0.5 = random, 1.0 = perfect)")
print(f"Brier score:         {brier:.4f}  (lower is better)")
print(f"No-skill baseline:   {no_skill_brier:.4f}  (always predicting the base rate)")
print(f"Brier Skill Score:   {brier_skill_score:.4f}  (>0 = better than base rate, 1.0 = perfect)")

# ------------------------------------------------------------------
# PART 2: CALIBRATION
# ------------------------------------------------------------------

test_df["prob_bin"] = pd.qcut(test_df["predicted_win_prob"], 10, duplicates="drop")
calibration = test_df.groupby("prob_bin", observed=True).agg(
    n_cases=("predicted_win_prob", "count"),
    mean_predicted=("predicted_win_prob", "mean"),
    actual_win_rate=("merchant_representment_won", "mean"),
).round(3)

print("\n" + "=" * 60)
print("PART 2: CALIBRATION BY PREDICTED-PROBABILITY DECILE")
print("=" * 60)
print(calibration)

# Save calibration plot
fig, ax = plt.subplots(figsize=(7, 5))
ax.plot([0, 1], [0, 1], "k--", label="Perfectly calibrated")
ax.scatter(calibration["mean_predicted"], calibration["actual_win_rate"],
           s=calibration["n_cases"] * 2, alpha=0.7, zorder=5, label="Model deciles")
ax.set_xlabel("Mean predicted probability")
ax.set_ylabel("Actual win rate")
ax.set_title("Calibration Plot (size = case count)")
ax.legend()
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
fig.tight_layout()
fig.savefig(OUTPUT_DIR / "calibration_plot.png", dpi=150)
plt.close(fig)
print(f"\nCalibration plot saved to {OUTPUT_DIR / 'calibration_plot.png'}")

# ------------------------------------------------------------------
# PART 3: DECISION QUALITY
# ------------------------------------------------------------------

precision = precision_score(y_test, test_df["model_decision_to_fight"])
recall = recall_score(y_test, test_df["model_decision_to_fight"])
cm = confusion_matrix(y_test, test_df["model_decision_to_fight"])

print("\n" + "=" * 60)
print("PART 3: DECISION QUALITY (held-out test set)")
print("=" * 60)
print(f"Decision Precision: {precision:.2%}  (when EV says fight, how often do we win?)")
print(f"Decision Recall:    {recall:.2%}  (of all actual wins, how many did EV capture?)")
print(f"\nConfusion Matrix:")
print(f"  TN (Ignored correctly): {cm[0][0]:>5}  |  FP (Fought & Lost): {cm[0][1]:>5}")
print(f"  FN (Missed winnable):   {cm[1][0]:>5}  |  TP (Fought & Won):  {cm[1][1]:>5}")

# Per-category decision quality
print("\nPer-category precision & recall:")
per_cat = test_df.groupby("normalized_category").apply(
    lambda g: pd.Series({
        "n": len(g),
        "base_win_rate": g["merchant_representment_won"].mean(),
        "precision": (
            precision_score(g["merchant_representment_won"], g["model_decision_to_fight"], zero_division=0)
        ),
        "recall": (
            recall_score(g["merchant_representment_won"], g["model_decision_to_fight"], zero_division=0)
        ),
        "pct_fought": g["model_decision_to_fight"].mean(),
    }),
    include_groups=False,
).round(3)
print(per_cat.to_string())

# ------------------------------------------------------------------
# PART 4: BUSINESS ROI
# ------------------------------------------------------------------

net_concede_all = 0.0

fight_all_fees = test_df.loc[test_df.merchant_representment_won == 0, "false_positive_cost_inr"].sum()
fight_all_funds = test_df.loc[test_df.merchant_representment_won == 1, "dispute_amount_inr"].sum()
net_fight_all = fight_all_funds - fight_all_fees

ai = test_df[test_df.model_decision_to_fight == 1]
ai_fees = ai.loc[ai.merchant_representment_won == 0, "false_positive_cost_inr"].sum()
ai_funds = ai.loc[ai.merchant_representment_won == 1, "dispute_amount_inr"].sum()
net_ai = ai_funds - ai_fees

print("\n" + "=" * 60)
print("PART 4: BUSINESS ROI")
print("=" * 60)
print(f"Total disputed amount:     Rs{test_df['dispute_amount_inr'].sum():>14,.2f}")
print(f"Net profit (concede all):  Rs{net_concede_all:>14,.2f}")
print(f"Net profit (fight all):    Rs{net_fight_all:>14,.2f}")
print(f"Net profit (AI strategy):  Rs{net_ai:>14,.2f}")
print(f"Cases fought: {len(ai)}/{len(test_df)} ({len(ai)/len(test_df):.1%})")
print(f"Value added vs fight-all:  Rs{net_ai - net_fight_all:>14,.2f}")

# ------------------------------------------------------------------
# PART 5: ORACLE CEILING
# ------------------------------------------------------------------

oracle_net = test_df.loc[test_df.merchant_representment_won == 1, "dispute_amount_inr"].sum()

print("\n" + "=" * 60)
print("PART 5: ORACLE CEILING")
print("=" * 60)
print(f"Oracle (perfect classifier) net: Rs{oracle_net:>14,.2f}")
print(f"AI strategy net:                 Rs{net_ai:>14,.2f}")
print(f"Fraction of theoretical max:      {net_ai / oracle_net:.1%}")

# ------------------------------------------------------------------
# PART 6: ERROR CONCENTRATION
# ------------------------------------------------------------------

fn = test_df[(test_df.model_decision_to_fight == 0) & (test_df.merchant_representment_won == 1)]
fp = test_df[(test_df.model_decision_to_fight == 1) & (test_df.merchant_representment_won == 0)]

print("\n" + "=" * 60)
print("PART 6: ERROR CONCENTRATION")
print("=" * 60)
print(f"False negatives: {len(fn)} cases, avg predicted_win_prob {fn['predicted_win_prob'].mean():.3f}")
print(f"False positives: {len(fp)} cases, avg predicted_win_prob {fp['predicted_win_prob'].mean():.3f}")
if "normalized_category" in fn.columns:
    print("\nFalse negatives by category:")
    print(fn["normalized_category"].value_counts().to_string())
    print("\nFalse positives by category:")
    print(fp["normalized_category"].value_counts().to_string())

# ------------------------------------------------------------------
# SAVE SUMMARY TO FILE
# ------------------------------------------------------------------

summary_lines = [
    f"PR-AUC: {pr_auc:.4f}",
    f"Brier Score: {brier:.4f}",
    f"Brier Skill Score: {brier_skill_score:.4f}",
    f"Decision Precision: {precision:.2%}",
    f"Decision Recall: {recall:.2%}",
    f"Net Profit (AI Strategy): Rs{net_ai:,.2f}",
    f"Net Profit (Fight All): Rs{net_fight_all:,.2f}",
    f"Value Added vs Fight All: Rs{net_ai - net_fight_all:,.2f}",
    f"Oracle Fraction: {net_ai / oracle_net:.1%}",
]
(OUTPUT_DIR / "model_op.txt").write_text("\n".join(summary_lines), encoding="utf-8")
print(f"\nSummary saved to {OUTPUT_DIR / 'model_op.txt'}")