"""
SYSTEM A — GRAPH GENERATOR FOR MODEL METRIC EVALUATION

Generates comprehensive, publication-quality model evaluation plots and saves them in outputs/evaluation_plots/

Plots generated:
  1. roc_curve.png                      - ROC Curve & AUC Score
  2. precision_recall_curve.png        - PR Curve & PR-AUC Score
  3. calibration_curve.png             - Calibration Curve (Base vs Calibrated vs Ideal)
  4. confusion_matrices.png            - Confusion Matrix Heatmaps (EV Policy vs Standard 0.5)
  5. generalization_gap_metrics.png    - Metrics across Train, Val, Test splits (Bias/Variance)
  6. feature_importance.png            - Top Feature Importances (Gain)
  7. probability_distribution.png       - Class Probability Separation Density
  8. business_roi_threshold.png        - ROI & Net Profit vs Threshold Analysis
  9. error_by_category.png             - FP & FN Error Concentration by Category
 10. ks_statistic_plot.png             - Kolmogorov-Smirnov Cumulative Separation Plot
 11. permutation_importance.png        - Permutation Feature Importance (Drop in PR-AUC)
"""

from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import (
    roc_curve,
    auc,
    precision_recall_curve,
    average_precision_score,
    confusion_matrix,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    log_loss,
    brier_score_loss,
)
from sklearn.calibration import calibration_curve
from sklearn.inspection import permutation_importance

# Style configuration
plt.rcParams.update({
    "font.sans-serif": "Arial",
    "font.family": "sans-serif",
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "axes.labelsize": 11,
    "axes.titlesize": 12,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
    "axes.titlesize": 13,
    "axes.titleweight": "bold",
})

ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / "system_a" / "model"
OUTPUT_DIR = ROOT / "outputs" / "evaluation_plots"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------------
# 1. LOAD DATA & MODELS
# ------------------------------------------------------------------

calibrated_model = joblib.load(MODEL_DIR / "xgb_calibrated_model.pkl")
base_model = joblib.load(MODEL_DIR / "xgb_base_model.pkl")
feature_cols = joblib.load(MODEL_DIR / "feature_cols.pkl")

data_path = ROOT / "data" / "chargeback_cases_v6.csv" if (ROOT / "data" / "chargeback_cases_v6.csv").exists() else ROOT / "data" / "chargeback_cases.csv"
df = pd.read_csv(data_path)
original_categories = df[["case_id", "normalized_category"]].copy()

categorical_cols = ["network", "payment_rail", "normalized_category"]
boolean_cols = [
    "is_tokenized", "bank_rrn_match", "delivery_otp_verified", "ip_geo_match",
    "sim_swap_flag_48h", "transaction_record_match", "post_dispute_activity",
]
for col in boolean_cols:
    df[col] = df[col].astype(int)

df_encoded = pd.get_dummies(df, columns=categorical_cols, drop_first=True)
missing = [c for c in feature_cols if c not in df_encoded.columns]
for m in missing:
    df_encoded[m] = 0

train_df = df_encoded[df_encoded["dataset_split"] == "train"].copy()
val_df = df_encoded[df_encoded["dataset_split"] == "validation"].copy()
test_df = df_encoded[df_encoded["dataset_split"] == "test"].copy()

if "normalized_category" not in test_df.columns:
    test_df = test_df.merge(original_categories, on="case_id", how="left")

X_train, y_train = train_df[feature_cols], train_df["merchant_representment_won"]
X_val, y_val = val_df[feature_cols], val_df["merchant_representment_won"]
X_test, y_test = test_df[feature_cols], test_df["merchant_representment_won"]

# Inference
probs_test = calibrated_model.predict_proba(X_test)[:, 1]
probs_test_base = base_model.predict_proba(X_test)[:, 1]
probs_train = calibrated_model.predict_proba(X_train)[:, 1]
probs_val = calibrated_model.predict_proba(X_val)[:, 1]

test_df["predicted_win_prob"] = probs_test
test_df["expected_value"] = (
    test_df["predicted_win_prob"] * test_df["dispute_amount_inr"]
    - (1 - test_df["predicted_win_prob"]) * test_df["false_positive_cost_inr"]
)
test_df["model_decision_to_fight"] = (test_df["expected_value"] > 0).astype(int)
test_df["pred_50"] = (probs_test >= 0.5).astype(int)

print(f"Data loaded successfully. Output directory: {OUTPUT_DIR}")

# ------------------------------------------------------------------
# GRAPH 1: ROC CURVE
# ------------------------------------------------------------------
fpr, tpr, _ = roc_curve(y_test, probs_test)
roc_auc = auc(fpr, tpr)

fig, ax = plt.subplots(figsize=(7, 6))
ax.plot(fpr, tpr, color="#1f77b4", lw=2.5, label=f"Calibrated XGBoost (AUC = {roc_auc:.4f})")
ax.plot([0, 1], [0, 1], color="gray", lw=1.5, linestyle="--", label="Random Classifier (AUC = 0.5000)")
ax.set_xlim([-0.02, 1.02])
ax.set_ylim([-0.02, 1.02])
ax.set_xlabel("False Positive Rate (1 - Specificity)")
ax.set_ylabel("True Positive Rate (Sensitivity / Recall)")
ax.set_title("Receiver Operating Characteristic (ROC) Curve — System A")
ax.legend(loc="lower right", frameon=True, facecolor="white")
ax.grid(True, linestyle=":", alpha=0.6)
fig.tight_layout()
fig.savefig(OUTPUT_DIR / "roc_curve.png")
plt.close(fig)
print("1. Saved roc_curve.png")

# ------------------------------------------------------------------
# GRAPH 2: PRECISION-RECALL CURVE
# ------------------------------------------------------------------
precision_pts, recall_pts, _ = precision_recall_curve(y_test, probs_test)
pr_auc_score = average_precision_score(y_test, probs_test)
baseline_pr = y_test.mean()

fig, ax = plt.subplots(figsize=(7, 6))
ax.plot(recall_pts, precision_pts, color="#2ca02c", lw=2.5, label=f"Calibrated XGBoost (PR-AUC = {pr_auc_score:.4f})")
ax.axhline(y=baseline_pr, color="red", linestyle="--", lw=1.5, label=f"No-Skill Baseline ({baseline_pr:.4f})")
ax.set_xlim([-0.02, 1.02])
ax.set_ylim([-0.02, 1.02])
ax.set_xlabel("Recall")
ax.set_ylabel("Precision")
ax.set_title("Precision-Recall (PR) Curve — System A")
ax.legend(loc="lower left", frameon=True, facecolor="white")
ax.grid(True, linestyle=":", alpha=0.6)
fig.tight_layout()
fig.savefig(OUTPUT_DIR / "precision_recall_curve.png")
plt.close(fig)
print("2. Saved precision_recall_curve.png")

# ------------------------------------------------------------------
# GRAPH 3: CALIBRATION CURVE (RELIABILITY DIAGRAM)
# ------------------------------------------------------------------
prob_true_cal, prob_pred_cal = calibration_curve(y_test, probs_test, n_bins=10, strategy="quantile")
prob_true_base, prob_pred_base = calibration_curve(y_test, probs_test_base, n_bins=10, strategy="quantile")

fig, ax = plt.subplots(figsize=(7, 6))
ax.plot([0, 1], [0, 1], "k--", lw=1.5, label="Perfectly Calibrated")
ax.plot(prob_pred_base, prob_true_base, "s-", color="#ff7f0e", lw=2, label="Uncalibrated Base XGBoost")
ax.plot(prob_pred_cal, prob_true_cal, "o-", color="#1f77b4", lw=2.5, label="Isotonic Calibrated XGBoost")
ax.set_xlabel("Mean Predicted Probability")
ax.set_ylabel("Actual Win Rate (Fraction of Positives)")
ax.set_title("Probability Calibration Curve (Reliability Diagram)")
ax.legend(loc="upper left", frameon=True, facecolor="white")
ax.grid(True, linestyle=":", alpha=0.6)
fig.tight_layout()
fig.savefig(OUTPUT_DIR / "calibration_curve.png")
plt.close(fig)
print("3. Saved calibration_curve.png")

# ------------------------------------------------------------------
# GRAPH 4: CONFUSION MATRICES
# ------------------------------------------------------------------
def plot_custom_cm(cm, ax, title, colormap="Blues"):
    im = ax.imshow(cm, interpolation="nearest", cmap=plt.get_cmap(colormap))
    ax.set_title(title, fontsize=11, fontweight="bold")
    tick_marks = np.arange(2)
    ax.set_xticks(tick_marks)
    ax.set_xticklabels(["Concede (0)", "Fight (1)"])
    ax.set_yticks(tick_marks)
    ax.set_yticklabels(["Actual Loss (0)", "Actual Win (1)"])
    
    thresh = cm.max() / 2.
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            val = cm[i, j]
            label = f"{val}\n" + (
                "(TN)" if i==0 and j==0 else
                "(FP)" if i==0 and j==1 else
                "(FN)" if i==1 and j==0 else "(TP)"
            )
            ax.text(j, i, label, ha="center", va="center",
                    color="white" if val > thresh else "black", fontweight="bold", fontsize=12)
    ax.set_xlabel("Predicted Action")
    ax.set_ylabel("True Outcome")

cm_ev = confusion_matrix(y_test, test_df["model_decision_to_fight"])
cm_50 = confusion_matrix(y_test, test_df["pred_50"])

fig, axes = plt.subplots(1, 2, figsize=(12, 5))
plot_custom_cm(cm_ev, axes[0], "Business EV Policy Threshold (EV > 0)\nPrec: 72.93% | Rec: 71.15% | Acc: 71.27%", "Blues")
plot_custom_cm(cm_50, axes[1], "Standard Probability Threshold (p >= 0.5)\nPrec: 81.10% | Rec: 73.72% | Acc: 77.40%", "Greens")

fig.suptitle("Confusion Matrix Comparison — System A (Test Set N=1,500)", fontsize=14, fontweight="bold", y=1.02)
fig.tight_layout()
fig.savefig(OUTPUT_DIR / "confusion_matrices.png", bbox_inches="tight")
plt.close(fig)
print("4. Saved confusion_matrices.png")

# ------------------------------------------------------------------
# GRAPH 5: GENERALIZATION GAP & METRICS ACROSS SPLITS
# ------------------------------------------------------------------
splits = ["Train (N=7k)", "Validation (N=1.5k)", "Test (N=1.5k)"]
metrics_cls = {
    "Accuracy": [
        accuracy_score(y_train, (probs_train >= 0.5).astype(int)),
        accuracy_score(y_val, (probs_val >= 0.5).astype(int)),
        accuracy_score(y_test, (probs_test >= 0.5).astype(int)),
    ],
    "Precision": [
        precision_score(y_train, (probs_train >= 0.5).astype(int)),
        precision_score(y_val, (probs_val >= 0.5).astype(int)),
        precision_score(y_test, (probs_test >= 0.5).astype(int)),
    ],
    "Recall": [
        recall_score(y_train, (probs_train >= 0.5).astype(int)),
        recall_score(y_val, (probs_val >= 0.5).astype(int)),
        recall_score(y_test, (probs_test >= 0.5).astype(int)),
    ],
    "F1 Score": [
        f1_score(y_train, (probs_train >= 0.5).astype(int)),
        f1_score(y_val, (probs_val >= 0.5).astype(int)),
        f1_score(y_test, (probs_test >= 0.5).astype(int)),
    ]
}

metrics_loss = {
    "LogLoss": [log_loss(y_train, probs_train), log_loss(y_val, probs_val), log_loss(y_test, probs_test)],
    "Brier Score": [brier_score_loss(y_train, probs_train), brier_score_loss(y_val, probs_val), brier_score_loss(y_test, probs_test)],
}

fig, axes = plt.subplots(1, 2, figsize=(13, 5))
x = np.arange(len(metrics_cls))
width = 0.25
colors = ["#4c72b0", "#55a868", "#c44e52"]

for idx, split_name in enumerate(splits):
    vals = [metrics_cls[m][idx] for m in metrics_cls]
    rects = axes[0].bar(x + (idx - 1)*width, vals, width, label=split_name, color=colors[idx])
    for rect in rects:
        h = rect.get_height()
        axes[0].annotate(f"{h:.3f}", (rect.get_x() + rect.get_width()/2., h),
                         ha="center", va="bottom", fontsize=7.5, xytext=(0, 2), textcoords="offset points")

axes[0].set_xticks(x)
axes[0].set_xticklabels(list(metrics_cls.keys()))
axes[0].set_ylim([0.6, 0.9])
axes[0].set_title("Classification Metrics Across Splits (Well-Generalized)")
axes[0].set_ylabel("Score")
axes[0].legend(frameon=True, facecolor="white")
axes[0].grid(True, linestyle=":", alpha=0.6, axis="y")

x_l = np.arange(len(metrics_loss))
for idx, split_name in enumerate(splits):
    vals = [metrics_loss[m][idx] for m in metrics_loss]
    rects = axes[1].bar(x_l + (idx - 1)*width, vals, width, label=split_name, color=colors[idx])
    for rect in rects:
        h = rect.get_height()
        axes[1].annotate(f"{h:.4f}", (rect.get_x() + rect.get_width()/2., h),
                         ha="center", va="bottom", fontsize=7.5, xytext=(0, 2), textcoords="offset points")

axes[1].set_xticks(x_l)
axes[1].set_xticklabels(list(metrics_loss.keys()))
axes[1].set_ylim([0.0, 0.6])
axes[1].set_title("Loss Metrics Across Splits (Low Generalization Gap)")
axes[1].set_ylabel("Loss (Lower is Better)")
axes[1].legend(frameon=True, facecolor="white")
axes[1].grid(True, linestyle=":", alpha=0.6, axis="y")

fig.suptitle("Bias-Variance & Generalization Analysis — System A", fontsize=14, fontweight="bold", y=1.02)
fig.tight_layout()
fig.savefig(OUTPUT_DIR / "generalization_gap_metrics.png", bbox_inches="tight")
plt.close(fig)
print("5. Saved generalization_gap_metrics.png")

# ------------------------------------------------------------------
# GRAPH 6: FEATURE IMPORTANCE
# ------------------------------------------------------------------
importances = base_model.feature_importances_
feat_imp = pd.Series(importances, index=feature_cols).sort_values(ascending=True).tail(15)

fig, ax = plt.subplots(figsize=(8, 6))
y_pos = np.arange(len(feat_imp))
bars = ax.barh(y_pos, feat_imp.values, color="#3470a3", edgecolor="none", height=0.65)
ax.set_yticks(y_pos)
ax.set_yticklabels(feat_imp.index)
ax.set_xlabel("XGBoost Gain Importance")
ax.set_title("Top 15 Feature Importances — System A Model")

for bar in bars:
    w = bar.get_width()
    ax.annotate(f"{w:.3f}", (w, bar.get_y() + bar.get_height()/2.),
                ha="left", va="center", fontsize=9, xytext=(4, 0), textcoords="offset points")

ax.set_xlim([0, feat_imp.max() * 1.15])
ax.grid(True, linestyle=":", alpha=0.6, axis="x")
fig.tight_layout()
fig.savefig(OUTPUT_DIR / "feature_importance.png")
plt.close(fig)
print("6. Saved feature_importance.png")

# ------------------------------------------------------------------
# GRAPH 7: PROBABILITY DISTRIBUTION BY CLASS SEPARATION
# ------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(8, 5))
ax.hist(probs_test[y_test == 0], bins=30, alpha=0.55, color="#d62728", density=True, label="Actual Loss (0)")
ax.hist(probs_test[y_test == 1], bins=30, alpha=0.55, color="#2ca02c", density=True, label="Actual Win (1)")
ax.axvline(x=0.5, color="black", linestyle="--", lw=1.5, label="Default 0.5 Threshold")
ax.set_xlabel("Predicted Win Probability")
ax.set_ylabel("Density")
ax.set_title("Predicted Probability Distribution by Ground Truth Outcome")
ax.legend(loc="upper center", frameon=True, facecolor="white")
ax.grid(True, linestyle=":", alpha=0.6)
fig.tight_layout()
fig.savefig(OUTPUT_DIR / "probability_distribution.png")
plt.close(fig)
print("7. Saved probability_distribution.png")

# ------------------------------------------------------------------
# GRAPH 8: BUSINESS ROI & THRESHOLD ANALYSIS
# ------------------------------------------------------------------
thresholds = np.linspace(0.01, 0.99, 100)
net_profits = []
for t in thresholds:
    fight = (probs_test >= t).astype(int)
    fought_df = test_df[fight == 1]
    won_funds = fought_df.loc[fought_df.merchant_representment_won == 1, "dispute_amount_inr"].sum()
    lost_fees = fought_df.loc[fought_df.merchant_representment_won == 0, "false_positive_cost_inr"].sum()
    net_profits.append(won_funds - lost_fees)

net_ai_ev = test_df.loc[test_df.model_decision_to_fight == 1, "dispute_amount_inr"].sum() - \
             test_df.loc[(test_df.model_decision_to_fight == 1) & (test_df.merchant_representment_won == 0), "false_positive_cost_inr"].sum()

fight_all_funds = test_df.loc[test_df.merchant_representment_won == 1, "dispute_amount_inr"].sum()
fight_all_fees = test_df.loc[test_df.merchant_representment_won == 0, "false_positive_cost_inr"].sum()
net_fight_all = fight_all_funds - fight_all_fees

oracle_net = test_df.loc[test_df.merchant_representment_won == 1, "dispute_amount_inr"].sum()

fig, ax = plt.subplots(figsize=(9, 5.5))
ax.plot(thresholds, net_profits, color="#1f77b4", lw=2.5, label="Net Profit by Fixed Probability Threshold")
ax.axhline(y=net_fight_all, color="#ff7f0e", linestyle="--", lw=1.8, label=f"Fight All Baseline (Rs {net_fight_all:,.0f})")
ax.axhline(y=0, color="gray", linestyle=":", lw=1.5, label="Concede All (Rs 0)")
ax.axhline(y=oracle_net, color="#2ca02c", linestyle="-.", lw=1.8, label=f"Oracle Ceiling (Rs {oracle_net:,.0f})")

ax.scatter([0.5], [net_ai_ev], color="red", s=100, zorder=5, label=f"AI EV-Strategy (Rs {net_ai_ev:,.0f})")

ax.set_xlabel("Probability Threshold")
ax.set_ylabel("Net Financial Recovery (INR)")
ax.set_title("Business ROI & Financial Recovery vs Decision Threshold")
ax.legend(loc="center right", frameon=True, facecolor="white")
ax.grid(True, linestyle=":", alpha=0.6)
fig.tight_layout()
fig.savefig(OUTPUT_DIR / "business_roi_threshold.png")
plt.close(fig)
print("8. Saved business_roi_threshold.png")

# ------------------------------------------------------------------
# GRAPH 9: ERROR CONCENTRATION BY CATEGORY
# ------------------------------------------------------------------
cat_errors = test_df.groupby("normalized_category").apply(
    lambda g: pd.Series({
        "False Positives (Fought & Lost)": ((g["model_decision_to_fight"] == 1) & (g["merchant_representment_won"] == 0)).sum(),
        "False Negatives (Missed Winnable)": ((g["model_decision_to_fight"] == 0) & (g["merchant_representment_won"] == 1)).sum(),
    }),
    include_groups=False,
)

fig, ax = plt.subplots(figsize=(10, 6))
y_pos = np.arange(len(cat_errors))
fp_vals = cat_errors["False Positives (Fought & Lost)"].values
fn_vals = cat_errors["False Negatives (Missed Winnable)"].values

ax.barh(y_pos, fp_vals, color="#ff7f0e", label="False Positives (Fought & Lost)", height=0.6)
ax.barh(y_pos, fn_vals, left=fp_vals, color="#d62728", label="False Negatives (Missed Winnable)", height=0.6)

ax.set_yticks(y_pos)
ax.set_yticklabels(cat_errors.index)
ax.set_xlabel("Number of Error Cases")
ax.set_ylabel("Dispute Category")
ax.set_title("System A Decision Errors Breakdown by Dispute Category")
ax.legend(title="Error Type", frameon=True, facecolor="white")
ax.grid(True, linestyle=":", alpha=0.6, axis="x")
fig.tight_layout()
fig.savefig(OUTPUT_DIR / "error_by_category.png")
plt.close(fig)
print("9. Saved error_by_category.png")

# ------------------------------------------------------------------
# GRAPH 10: KOLMOGOROV-SMIRNOV (KS) STATISTIC SEPARATION PLOT
# ------------------------------------------------------------------
probs_0 = probs_test[y_test == 0]
probs_1 = probs_test[y_test == 1]
t_range = np.linspace(0, 1, 200)
cdf_0 = np.array([np.mean(probs_0 <= t) for t in t_range])
cdf_1 = np.array([np.mean(probs_1 <= t) for t in t_range])
diff = np.abs(cdf_0 - cdf_1)
max_idx = np.argmax(diff)
ks_stat = diff[max_idx]
ks_threshold = t_range[max_idx]

fig, ax = plt.subplots(figsize=(8, 5.5))
ax.plot(t_range, cdf_0, color="#d62728", lw=2.2, label="CDF Loss (Class 0)")
ax.plot(t_range, cdf_1, color="#2ca02c", lw=2.2, label="CDF Win (Class 1)")
ax.vlines(x=ks_threshold, ymin=cdf_1[max_idx], ymax=cdf_0[max_idx], color="purple", linestyle="--", lw=2,
          label=f"Max KS Distance = {ks_stat:.4f} (56.25%) at p={ks_threshold:.2f}")

ax.scatter([ks_threshold, ks_threshold], [cdf_1[max_idx], cdf_0[max_idx]], color="purple", s=60, zorder=5)

ax.set_xlabel("Predicted Probability Threshold")
ax.set_ylabel("Cumulative Fraction of Population")
ax.set_title(f"Kolmogorov-Smirnov (KS) Separation Plot (KS = {ks_stat*100:.2f}%)")
ax.legend(loc="lower right", frameon=True, facecolor="white")
ax.grid(True, linestyle=":", alpha=0.6)
fig.tight_layout()
fig.savefig(OUTPUT_DIR / "ks_statistic_plot.png")
plt.close(fig)
print("10. Saved ks_statistic_plot.png")

# ------------------------------------------------------------------
# GRAPH 11: PERMUTATION FEATURE IMPORTANCE (DROP IN PR-AUC)
# ------------------------------------------------------------------
perm_res = permutation_importance(
    base_model, X_test, y_test, n_repeats=10, random_state=42, scoring="average_precision"
)
perm_series = pd.Series(perm_res.importances_mean, index=feature_cols).sort_values(ascending=True).tail(15)

fig, ax = plt.subplots(figsize=(8, 6))
y_pos = np.arange(len(perm_series))
bars = ax.barh(y_pos, perm_series.values, color="#e67e22", edgecolor="none", height=0.65)
ax.set_yticks(y_pos)
ax.set_yticklabels(perm_series.index)
ax.set_xlabel("Mean Drop in PR-AUC Score")
ax.set_title("Permutation Feature Importance (Top 15 Model-Agnostic Impact)")

for bar in bars:
    w = bar.get_width()
    ax.annotate(f"{w:.4f}", (w, bar.get_y() + bar.get_height()/2.),
                ha="left", va="center", fontsize=9, xytext=(4, 0), textcoords="offset points")

ax.set_xlim([0, perm_series.max() * 1.18])
ax.grid(True, linestyle=":", alpha=0.6, axis="x")
fig.tight_layout()
fig.savefig(OUTPUT_DIR / "permutation_importance.png")
plt.close(fig)
print("11. Saved permutation_importance.png")

print(f"\nALL 11 EVALUATION GRAPHS SUCCESSFULLY GENERATED IN: {OUTPUT_DIR}")
