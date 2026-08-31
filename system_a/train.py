from pathlib import Path

import xgboost as xgb
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import brier_score_loss, average_precision_score
import pandas as pd
import numpy as np
from sklearn.metrics import precision_score, recall_score, confusion_matrix

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "chargeback_cases.csv"

# 1. LOAD DATA
df = pd.read_csv(DATA_PATH)

# 2. FEATURE ENGINEERING & PREPROCESSING
# Select the observable features the model is allowed to see
categorical_cols = ["network", "payment_rail", "normalized_category"]
numeric_cols = [
    "dispute_amount_inr", "otp_entry_duration_sec", "previous_successful_orders",
    "previous_refunds", "previous_chargebacks", "filing_delay_days"
]
boolean_cols = [
    "is_tokenized", "bank_rrn_match", "delivery_otp_verified", "ip_geo_match",
    "sim_swap_flag_48h", "transaction_record_match", "post_dispute_activity"
]

# Convert booleans to integers (1/0)
for col in boolean_cols:
    df[col] = df[col].astype(int)

# One-hot encode categorical features
df_encoded = pd.get_dummies(df, columns=categorical_cols, drop_first=True)

# 3. SPLIT DATA USING THE PRE-DEFINED TIME SPLITS
train_df = df_encoded[df_encoded["dataset_split"] == "train"]
test_df = df_encoded[df_encoded["dataset_split"] == "test"]

# Define feature matrix (X) and target (y)
feature_cols = [col for col in df_encoded.columns if col not in [
    "case_id", "transaction_id", "order_id", "country", "currency",
    "transaction_date", "dispute_filed_date", "dataset_split",
    "merchant_representment_won", "representment_fee_inr",
    "false_positive_cost_inr", "false_negative_cost_inr"
]]

X_train, y_train = train_df[feature_cols], train_df["merchant_representment_won"]
X_test, y_test = test_df[feature_cols], test_df["merchant_representment_won"]


# 4. TRAIN THE CALIBRATED XGBOOST VERIFIER
print("Training and Calibrating XGBoost Verifier Model...")
base_model = xgb.XGBClassifier(
    n_estimators=200,
    learning_rate=0.05,
    max_depth=5,
    scale_pos_weight=(len(y_train) - sum(y_train)) / sum(y_train),
    random_state=42,
    eval_metric="logloss"
)

# Wrap model to ensure probabilities reflect true real-world likelihoods
calibrated_model = CalibratedClassifierCV(base_model, method='isotonic', cv=5)
calibrated_model.fit(X_train, y_train)

# 5. INFERENCE & EXPECTED VALUE (EV) DECISION LOGIC
test_df = test_df.copy()
test_df["predicted_win_prob"] = calibrated_model.predict_proba(X_test)[:, 1]

# Hackathon "Honest Metric": Only fight if Expected Value > 0
test_df["expected_value"] = (
    (test_df["predicted_win_prob"] * test_df["dispute_amount_inr"]) -
    ((1 - test_df["predicted_win_prob"]) * test_df["false_positive_cost_inr"])
)

test_df["model_decision_to_fight"] = (test_df["expected_value"] > 0).astype(int)

# 6. EVALUATION & "HONEST METRICS" OUTPUT
print("\n" + "="*50)
print("PART 1: PURE MODEL QUALITY (Classifier Metrics)")
print("="*50)

# Raw model quality before any business logic is applied
pr_auc = average_precision_score(y_test, test_df["predicted_win_prob"])
brier = brier_score_loss(y_test, test_df["predicted_win_prob"])

print(f"PR-AUC:       {pr_auc:.4f} (Higher is better, 1.0 is perfect)")
print(f"Brier Score:  {brier:.4f} (Lower is better, 0.0 is perfectly calibrated)")

print("\n" + "="*50)
print("PART 2: DECISION QUALITY (Held-Out Test Set)")
print("="*50)

precision = precision_score(y_test, test_df["model_decision_to_fight"])
recall = recall_score(y_test, test_df["model_decision_to_fight"])
cm = confusion_matrix(y_test, test_df["model_decision_to_fight"])

print(f"Decision Precision: {precision:.2%} (When EV says fight, how often do we win?)")
print(f"Decision Recall:    {recall:.2%} (Of all actual wins, how many did EV capture?)")
print(f"\nConfusion Matrix: \nTN (Ignored correctly): {cm[0][0]} | FP (Fought & Lost): {cm[0][1]}")
print(f"FN (Ignored & Lost):    {cm[1][0]} | TP (Fought & Won):  {cm[1][1]}")

print("\n" + "="*50)
print("PART 3: BUSINESS ROI & NET SAVINGS")
print("="*50)

# Baseline 1: Concede everything (Zero effort, zero fees, zero wins)
net_concede_all = 0.0

# Baseline 2: Fight everything blindly
fight_all_fees_lost = test_df[test_df["merchant_representment_won"] == 0]["false_positive_cost_inr"].sum()
fight_all_funds_won = test_df[test_df["merchant_representment_won"] == 1]["dispute_amount_inr"].sum()
net_fight_all = fight_all_funds_won - fight_all_fees_lost

# AI Verifier Pipeline Strategy
ai_fought = test_df[test_df["model_decision_to_fight"] == 1]
ai_fees_lost = ai_fought[ai_fought["merchant_representment_won"] == 0]["false_positive_cost_inr"].sum()
ai_funds_won = ai_fought[ai_fought["merchant_representment_won"] == 1]["dispute_amount_inr"].sum()
net_ai_strategy = ai_funds_won - ai_fees_lost

print(f"Total Disputed Amount:      ₹{test_df['dispute_amount_inr'].sum():,.2f}")
print(f"Net Profit (Concede All):   ₹{net_concede_all:,.2f}")
print(f"Net Profit (Fight All):     ₹{net_fight_all:,.2f}")
print(f"Net Profit (AI Strategy):   ₹{net_ai_strategy:,.2f}")
print(f"\nValue Added by AI vs Fight All: ₹{(net_ai_strategy - net_fight_all):,.2f}")