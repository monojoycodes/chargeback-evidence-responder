"""
SYSTEM A — EVALUATION

Loads the model train.py already saved (does not retrain), rebuilds the
held-out test set the same way train.py built the training set, and
reports every metric the project needs:

  - PR-AUC and Brier score          (raw classifier quality)
  - calibration-by-decile table     (is the probability itself honest?)
  - decision precision/recall       (quality of the EV-threshold decision)
  - three-way ROI baseline          (concede-all / fight-all / AI strategy)
  - oracle ceiling                  (% of the theoretical max captured)

Run this after train.py, from the project root:
    python3 system_a/evaluate.py
"""

import joblib
import pandas as pd
from sklearn.metrics import (
    precision_score, recall_score, confusion_matrix,
    average_precision_score, brier_score_loss,
)

MODEL_PATH = "system_a/model/xgb_calibrated_model.pkl"
FEATURE_COLS_PATH = "system_a/model/feature_cols.pkl"
DATA_PATH = "chargeback_cases.csv"

# ------------------------------------------------------------------
# 1. LOAD MODEL + FEATURE LIST (not retraining - this is the point of
#    splitting evaluate.py out from train.py)
# ------------------------------------------------------------------

model = joblib.load(MODEL_PATH)
feature_cols = joblib.load(FEATURE_COLS_PATH)

# ------------------------------------------------------------------
# 2. REBUILD THE TEST SET - must match train.py's preprocessing
#    exactly, or the feature columns won't line up with what the
#    model was trained on.
# ------------------------------------------------------------------

df = pd.read_csv(DATA_PATH)
original_categories = df[["case_id", "normalized_category"]].copy()  # kept pre-encoding for the error breakdown

categorical_cols = ["network", "payment_rail", "normalized_category"]
boolean_cols = [
    "is_tokenized", "bank_rrn_match", "delivery_otp_verified", "ip_geo_match",
    "sim_swap_flag_48h", "transaction_record_match", "post_dispute_activity"
]
for col in boolean_cols:
    df[col] = df[col].astype(int)

df_encoded = pd.get_dummies(df, columns=categorical_cols, drop_first=True)

# Defensive: if the test split happens to be missing a category value
# that appeared in train (or vice versa), pd.get_dummies on the full
# df already avoids that mismatch since it's encoded before splitting -
# reindexing against the saved feature_cols is a second guard in case
# this script is ever pointed at a different data file.
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
# 4. PART 1 - RAW CLASSIFIER QUALITY
# ------------------------------------------------------------------

pr_auc = average_precision_score(y_test, test_df["predicted_win_prob"])
brier = brier_score_loss(y_test, test_df["predicted_win_prob"])
no_skill_brier = y_test.mean() * (1 - y_test.mean())  # floor: always predict the base rate

print("=" * 55)
print("PART 1: PURE MODEL QUALITY")
print("=" * 55)
print(f"PR-AUC:            {pr_auc:.4f}  (0.5 = random, 1.0 = perfect)")
print(f"Brier score:       {brier:.4f}  (lower is better)")
print(f"No-skill baseline: {no_skill_brier:.4f}  (always predicting the base rate)")

# Calibration-by-decile - the check that confirms the Brier score isn't
# hiding a model that's over/under-confident in specific bins.
test_df["prob_bin"] = pd.qcut(test_df["predicted_win_prob"], 10, duplicates="drop")
calibration = test_df.groupby("prob_bin", observed=True).agg(
    n_cases=("predicted_win_prob", "count"),
    mean_predicted=("predicted_win_prob", "mean"),
    actual_win_rate=("merchant_representment_won", "mean"),
).round(3)
print("\nCalibration by predicted-probability decile:")
print(calibration)

# ------------------------------------------------------------------
# 5. PART 2 - DECISION QUALITY
# ------------------------------------------------------------------

precision = precision_score(y_test, test_df["model_decision_to_fight"])
recall = recall_score(y_test, test_df["model_decision_to_fight"])
cm = confusion_matrix(y_test, test_df["model_decision_to_fight"])

print("\n" + "=" * 55)
print("PART 2: DECISION QUALITY (held-out test set)")
print("=" * 55)
print(f"Decision Precision: {precision:.2%}  (when EV says fight, how often do we win?)")
print(f"Decision Recall:    {recall:.2%}  (of all actual wins, how many did EV capture?)")
print(f"\nTN {cm[0][0]} | FP {cm[0][1]}\nFN {cm[1][0]} | TP {cm[1][1]}")

# ------------------------------------------------------------------
# 6. PART 3 - BUSINESS ROI, THREE-WAY BASELINE
# ------------------------------------------------------------------

net_concede_all = 0.0

fight_all_fees = test_df.loc[test_df.merchant_representment_won == 0, "false_positive_cost_inr"].sum()
fight_all_funds = test_df.loc[test_df.merchant_representment_won == 1, "dispute_amount_inr"].sum()
net_fight_all = fight_all_funds - fight_all_fees

ai = test_df[test_df.model_decision_to_fight == 1]
ai_fees = ai.loc[ai.merchant_representment_won == 0, "false_positive_cost_inr"].sum()
ai_funds = ai.loc[ai.merchant_representment_won == 1, "dispute_amount_inr"].sum()
net_ai = ai_funds - ai_fees

print("\n" + "=" * 55)
print("PART 3: BUSINESS ROI")
print("=" * 55)
print(f"Total disputed amount:     Rs {test_df['dispute_amount_inr'].sum():,.2f}")
print(f"Net profit (concede all):  Rs {net_concede_all:,.2f}")
print(f"Net profit (fight all):    Rs {net_fight_all:,.2f}")
print(f"Net profit (AI strategy):  Rs {net_ai:,.2f}")
print(f"Cases fought: {len(ai)}/{len(test_df)} ({len(ai)/len(test_df):.1%})")
print(f"Value added vs fight-all:  Rs {net_ai - net_fight_all:,.2f}")

# ------------------------------------------------------------------
# 7. ORACLE CEILING - what a perfect classifier would net on this
#    exact test set, and what fraction of that the model captured.
# ------------------------------------------------------------------

oracle_net = test_df.loc[test_df.merchant_representment_won == 1, "dispute_amount_inr"].sum()

print("\n" + "=" * 55)
print("PART 4: ORACLE CEILING")
print("=" * 55)
print(f"Oracle (perfect classifier) net: Rs {oracle_net:,.2f}")
print(f"AI strategy net:                 Rs {net_ai:,.2f}")
print(f"Fraction of theoretical max:      {net_ai / oracle_net:.1%}")

# ------------------------------------------------------------------
# 8. ERROR BREAKDOWN BY CATEGORY - where the model's mistakes live
# ------------------------------------------------------------------

fn = test_df[(test_df.model_decision_to_fight == 0) & (test_df.merchant_representment_won == 1)]
fp = test_df[(test_df.model_decision_to_fight == 1) & (test_df.merchant_representment_won == 0)]

print("\n" + "=" * 55)
print("PART 5: ERROR CONCENTRATION")
print("=" * 55)
print(f"False negatives: {len(fn)} cases, avg predicted_win_prob {fn['predicted_win_prob'].mean():.3f}")
print(f"False positives: {len(fp)} cases, avg predicted_win_prob {fp['predicted_win_prob'].mean():.3f}")
if "normalized_category" in fn.columns:
    print("\nFalse negatives by category:")
    print(fn["normalized_category"].value_counts())
    print("\nFalse positives by category:")
    print(fp["normalized_category"].value_counts())