"""
SYSTEM A — TRAINING

Trains a calibrated XGBoost classifier to predict chargeback representment
outcome. Uses early stopping on the validation split, then calibrates
probabilities with isotonic regression.

Saves:
  system_a/model/xgb_calibrated_model.pkl  — production model (calibrated)
  system_a/model/xgb_base_model.pkl        — uncalibrated, for SHAP analysis
  system_a/model/feature_cols.pkl           — ordered feature column list

Run from project root:
    python system_a/train.py
"""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.calibration import CalibratedClassifierCV

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "chargeback_cases_v6.csv" if (ROOT / "data" / "chargeback_cases_v6.csv").exists() else ROOT / "data" / "chargeback_cases.csv"
MODEL_DIR = ROOT / "system_a" / "model"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------------
# 1. LOAD DATA
# ------------------------------------------------------------------

df = pd.read_csv(DATA_PATH)
print(f"Loaded {len(df):,} cases from {DATA_PATH.name}")

# ------------------------------------------------------------------
# 2. FEATURE ENGINEERING & PREPROCESSING
# ------------------------------------------------------------------

categorical_cols = ["network", "payment_rail", "normalized_category"]
boolean_cols = [
    "is_tokenized", "bank_rrn_match", "delivery_otp_verified", "ip_geo_match",
    "sim_swap_flag_48h", "transaction_record_match", "post_dispute_activity",
]

for col in boolean_cols:
    df[col] = df[col].astype(int)

df_encoded = pd.get_dummies(df, columns=categorical_cols, drop_first=True)

# Exclude non-feature columns from the feature matrix
exclude_cols = {
    "case_id", "transaction_id", "order_id", "country", "currency",
    "transaction_date", "dispute_filed_date", "dataset_split",
    "reason_code", "reason_code_title",
    "merchant_representment_won", "representment_fee_inr",
    "false_positive_cost_inr", "false_negative_cost_inr",
}
feature_cols = [c for c in df_encoded.columns if c not in exclude_cols]

# ------------------------------------------------------------------
# 3. SPLIT DATA USING PRE-DEFINED TIME SPLITS
# ------------------------------------------------------------------

train_df = df_encoded[df_encoded["dataset_split"] == "train"]
val_df = df_encoded[df_encoded["dataset_split"] == "validation"]
test_df = df_encoded[df_encoded["dataset_split"] == "test"]

X_train, y_train = train_df[feature_cols], train_df["merchant_representment_won"]
X_val, y_val = val_df[feature_cols], val_df["merchant_representment_won"]

print(f"Train: {len(X_train):,}  Val: {len(X_val):,}  Test: {len(test_df):,}")
print(f"Features: {len(feature_cols)}")

# ------------------------------------------------------------------
# 4. TRAIN BASE XGBOOST WITH EARLY STOPPING ON VALIDATION SET
# ------------------------------------------------------------------

print("\nTraining base XGBoost with early stopping on validation set...")
pos_weight = (len(y_train) - y_train.sum()) / y_train.sum()

base_model = xgb.XGBClassifier(
    n_estimators=500,
    learning_rate=0.05,
    max_depth=5,
    scale_pos_weight=pos_weight,
    random_state=42,
    eval_metric="logloss",
    early_stopping_rounds=30,
)
base_model.fit(
    X_train, y_train,
    eval_set=[(X_val, y_val)],
    verbose=False,
)
best_n = base_model.best_iteration + 1
print(f"Early stopping selected {best_n} / 500 estimators")

# ------------------------------------------------------------------
# 5. CALIBRATE PROBABILITIES (isotonic, 5-fold CV on training data)
# ------------------------------------------------------------------

print("Calibrating probabilities with isotonic regression (5-fold CV)...")
# Build a fresh base model with the optimal tree count (no early_stopping
# params, which would confuse CalibratedClassifierCV's internal fit calls)
final_base = xgb.XGBClassifier(
    n_estimators=best_n,
    learning_rate=0.05,
    max_depth=5,
    scale_pos_weight=pos_weight,
    random_state=42,
    eval_metric="logloss",
)

calibrated_model = CalibratedClassifierCV(final_base, method="isotonic", cv=5)
calibrated_model.fit(X_train, y_train)

# ------------------------------------------------------------------
# 6. FIT A STANDALONE BASE MODEL ON ALL TRAINING DATA (for SHAP)
# ------------------------------------------------------------------

print("Fitting standalone base model on full training data (for SHAP)...")
base_for_shap = xgb.XGBClassifier(
    n_estimators=best_n,
    learning_rate=0.05,
    max_depth=5,
    scale_pos_weight=pos_weight,
    random_state=42,
    eval_metric="logloss",
)
base_for_shap.fit(X_train, y_train)

# ------------------------------------------------------------------
# 7. SAVE EVERYTHING
# ------------------------------------------------------------------

joblib.dump(calibrated_model, MODEL_DIR / "xgb_calibrated_model.pkl")
joblib.dump(base_for_shap, MODEL_DIR / "xgb_base_model.pkl")
joblib.dump(feature_cols, MODEL_DIR / "feature_cols.pkl")

# Clean up placeholder file if it exists
placeholder = MODEL_DIR / "xgb_model.json"
if placeholder.exists():
    placeholder.unlink()

print(f"\nSaved to {MODEL_DIR}/:")
print(f"  xgb_calibrated_model.pkl  (production)")
print(f"  xgb_base_model.pkl        (for SHAP)")
print(f"  feature_cols.pkl           ({len(feature_cols)} features)")
print("\nRun 'python system_a/evaluate.py' for full evaluation on held-out test set.")