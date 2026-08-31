"""
CHARGEBACK EVIDENCE RESPONDER — SYNTHETIC DATASET GENERATOR (v4)
`
Output :
  chargeback_cases.csv        - model-facing case features + label
  evidence_items.csv          - evidence records linked by case_id
  chargeback_cases_DEBUG.csv  - internal only, never train on this
"""

import numpy as np
import pandas as pd

np.random.seed(42)
rng = np.random.default_rng(42)

NUM_CASES = 10_000
MAX_EVIDENCE_PER_CASE = 12
LABEL_NOISE_STD = 0.07
FEATURE_FLIP_PROB = 0.08

# ------------------------------------------------------------------
# 1. NETWORKS
# ------------------------------------------------------------------

NETWORKS = ["UPI_NPCI", "RUPAY", "VISA", "MASTERCARD", "AMERICAN_EXPRESS"]
NETWORK_PROBS = [0.40, 0.30, 0.15, 0.10, 0.05]
NETWORK_TO_RAIL = {
    "UPI_NPCI": "UPI", "RUPAY": "CARD", "VISA": "CARD",
    "MASTERCARD": "CARD", "AMERICAN_EXPRESS": "CARD",
}

# ------------------------------------------------------------------
# 2. CATEGORIES - now weighted, fraud-heavy, instead of uniform.
#    Rough assumption grounded in the "fraud-related codes dominate
#    chargeback volume" finding - not a precise published split.
# ------------------------------------------------------------------

CATEGORIES = [
    "FRAUD_UNAUTHORIZED", "ITEM_NOT_RECEIVED", "NOT_AS_DESCRIBED",
    "RECON_SETTLEMENT_ERROR", "REFUND_NOT_RECEIVED", "DUPLICATE_TRANSACTION",
    "SUBSCRIPTION_CANCELED", "SERVICE_NOT_PROVIDED", "INCORRECT_AMOUNT",
]
CATEGORY_PROBS = [0.28, 0.20, 0.12, 0.10, 0.08, 0.07, 0.06, 0.05, 0.04]

# Typical disputed-amount scale per category (log-space mean for the
# lognormal draw). Higher = bigger typical ticket size.
CATEGORY_AMOUNT_LOGMEAN = {
    "FRAUD_UNAUTHORIZED": 7.5,      # often higher-value targeted purchases
    "SERVICE_NOT_PROVIDED": 7.8,    # service/contract value
    "ITEM_NOT_RECEIVED": 7.0,
    "NOT_AS_DESCRIBED": 7.0,
    "DUPLICATE_TRANSACTION": 7.0,
    "INCORRECT_AMOUNT": 7.0,
    "REFUND_NOT_RECEIVED": 7.0,
    "RECON_SETTLEMENT_ERROR": 6.3,  # typically everyday UPI-scale transactions
    "SUBSCRIPTION_CANCELED": 5.5,   # small recurring amounts
}
AMOUNT_LOGSIGMA = 1.2

# ------------------------------------------------------------------
# 3. EVIDENCE REQUIREMENT RULES (unchanged from v3)
# ------------------------------------------------------------------

EVIDENCE_RULES = {
    "FRAUD_UNAUTHORIZED": {
        "required": ["PAYMENT_AUTHORIZATION", "THREE_DS_AUTHENTICATION"],
        "relevant": ["DEVICE_LOG", "IP_LOG", "LOGIN_LOG",
                     "PRIOR_UNDISPUTED_TRANSACTION", "ORDER_CONFIRMATION",
                     "CUSTOMER_COMMUNICATION"],
        "distractors": ["REFUND_POLICY", "RETURN_POLICY", "DELIVERY_TRACKING",
                         "SERVICE_COMPLETION_PROOF"],
    },
    "ITEM_NOT_RECEIVED": {
        "required": ["DELIVERY_TRACKING", "PROOF_OF_DELIVERY"],
        "relevant": ["DELIVERY_OTP", "SIGNED_DELIVERY", "ORDER_CONFIRMATION",
                     "CUSTOMER_COMMUNICATION", "INVOICE"],
        "distractors": ["DEVICE_LOG", "LOGIN_LOG", "REFUND_POLICY"],
    },
    "NOT_AS_DESCRIBED": {
        "required": ["ORDER_CONFIRMATION", "PRODUCT_DESCRIPTION"],
        "relevant": ["PRODUCT_IMAGES", "CUSTOMER_COMMUNICATION",
                     "RETURN_RECORD", "INVOICE", "TERMS_AND_CONDITIONS"],
        "distractors": ["IP_LOG", "DEVICE_LOG", "THREE_DS_AUTHENTICATION"],
    },
    "SERVICE_NOT_PROVIDED": {
        "required": ["SERVICE_COMPLETION_PROOF"],
        "relevant": ["CONTRACT", "CUSTOMER_COMMUNICATION", "ACCOUNT_USAGE_LOG",
                     "INVOICE", "TERMS_ACCEPTANCE"],
        "distractors": ["DELIVERY_TRACKING", "PROOF_OF_DELIVERY", "DEVICE_LOG"],
    },
    "DUPLICATE_TRANSACTION": {
        "required": ["PAYMENT_AUTHORIZATION"],
        "relevant": ["TRANSACTION_RECEIPT", "BANK_RRN_RECORD",
                     "ORDER_CONFIRMATION", "REFUND_RECORD"],
        "distractors": ["DELIVERY_TRACKING", "PRODUCT_IMAGES", "LOGIN_LOG"],
    },
    "INCORRECT_AMOUNT": {
        "required": ["TRANSACTION_RECEIPT", "INVOICE"],
        "relevant": ["PAYMENT_AUTHORIZATION", "ORDER_CONFIRMATION",
                     "BANK_RRN_RECORD"],
        "distractors": ["DELIVERY_TRACKING", "DEVICE_LOG", "RETURN_POLICY"],
    },
    "REFUND_NOT_RECEIVED": {
        "required": ["REFUND_RECORD"],
        "relevant": ["BANK_RRN_RECORD", "CUSTOMER_COMMUNICATION",
                     "CANCELLATION_RECORD", "TRANSACTION_RECEIPT"],
        "distractors": ["DELIVERY_TRACKING", "PRODUCT_IMAGES", "DEVICE_LOG"],
    },
    "SUBSCRIPTION_CANCELED": {
        "required": ["CANCELLATION_RECORD"],
        "relevant": ["SUBSCRIPTION_USAGE_LOG", "TERMS_ACCEPTANCE",
                     "CUSTOMER_COMMUNICATION", "PAYMENT_AUTHORIZATION"],
        "distractors": ["DELIVERY_TRACKING", "PROOF_OF_DELIVERY", "PRODUCT_IMAGES"],
    },
    "RECON_SETTLEMENT_ERROR": {
        "required": ["BANK_RRN_RECORD"],
        "relevant": ["SETTLEMENT_RECORD", "PAYMENT_AUTHORIZATION",
                     "TRANSACTION_RECEIPT"],
        "distractors": ["PRODUCT_IMAGES", "RETURN_POLICY", "CUSTOMER_COMMUNICATION"],
    },
}

EVIDENCE_TEMPLATES = {
    "PAYMENT_AUTHORIZATION": lambda t, o, a, c: f"Payment authorization successful for transaction {t}. Amount: INR {a:.2f}.",
    "THREE_DS_AUTHENTICATION": lambda t, o, a, c: f"3DS/OTP authentication successfully completed for transaction {t}.",
    "DEVICE_LOG": lambda t, o, a, c: f"Device fingerprint recorded during transaction {t}. Device history available.",
    "IP_LOG": lambda t, o, a, c: f"IP and geolocation record associated with transaction {t}.",
    "LOGIN_LOG": lambda t, o, a, c: f"Customer account login activity recorded before transaction {t}.",
    "PRIOR_UNDISPUTED_TRANSACTION": lambda t, o, a, c: "Customer completed previous undisputed transaction using the same account.",
    "ORDER_CONFIRMATION": lambda t, o, a, c: f"Order {o} was confirmed for INR {a:.2f}.",
    "CUSTOMER_COMMUNICATION": lambda t, o, a, c: f"Customer communication regarding order {o} and dispute category {c}.",
    "DELIVERY_TRACKING": lambda t, o, a, c: f"Courier tracking record for order {o}.",
    "PROOF_OF_DELIVERY": lambda t, o, a, c: f"Delivery confirmation available for order {o}.",
    "DELIVERY_OTP": lambda t, o, a, c: f"Delivery OTP verified successfully for order {o}.",
    "SIGNED_DELIVERY": lambda t, o, a, c: f"Signed proof of delivery recorded for order {o}.",
    "INVOICE": lambda t, o, a, c: f"Invoice generated for order {o}. Amount: INR {a:.2f}.",
    "PRODUCT_DESCRIPTION": lambda t, o, a, c: "Product description displayed during purchase.",
    "PRODUCT_IMAGES": lambda t, o, a, c: f"Product images stored for order {o}.",
    "RETURN_RECORD": lambda t, o, a, c: "Return request and return processing record available.",
    "TERMS_AND_CONDITIONS": lambda t, o, a, c: "Terms and conditions associated with purchase.",
    "SERVICE_COMPLETION_PROOF": lambda t, o, a, c: f"Service completion record available for order {o}.",
    "CONTRACT": lambda t, o, a, c: f"Service contract linked to order {o}.",
    "ACCOUNT_USAGE_LOG": lambda t, o, a, c: "Account usage activity recorded after service activation.",
    "TERMS_ACCEPTANCE": lambda t, o, a, c: "Customer accepted subscription or purchase terms.",
    "TRANSACTION_RECEIPT": lambda t, o, a, c: f"Transaction receipt for {t}. Amount: INR {a:.2f}.",
    "BANK_RRN_RECORD": lambda t, o, a, c: "Bank reconciliation record confirms RRN match.",
    "REFUND_RECORD": lambda t, o, a, c: f"Refund processing record generated for transaction {t}.",
    "CANCELLATION_RECORD": lambda t, o, a, c: "Cancellation request record available.",
    "SUBSCRIPTION_USAGE_LOG": lambda t, o, a, c: "Subscription usage activity recorded.",
    "SETTLEMENT_RECORD": lambda t, o, a, c: f"Settlement record available for transaction {t}.",
    "REFUND_POLICY": lambda t, o, a, c: "Merchant refund policy document.",
    "RETURN_POLICY": lambda t, o, a, c: "Merchant return policy document.",
}


def generate_evidence_text(evidence_type, transaction_id, order_id, amount, category):
    fn = EVIDENCE_TEMPLATES.get(evidence_type)
    return fn(transaction_id, order_id, amount, category) if fn else f"Evidence record for transaction {transaction_id}."


# ------------------------------------------------------------------
# 4. CASE-LEVEL DATA
# ------------------------------------------------------------------

n = NUM_CASES
case_id = np.array([f"CB_IN_2026_{i:05d}" for i in range(n)])
transaction_id_ints = rng.integers(10**11, 10**12, size=n, dtype=np.int64)
transaction_id = np.array([f"TXN_{value}" for value in transaction_id_ints])
order_id_ints = rng.integers(10**9, 10**10, size=n, dtype=np.int64)
order_id = np.array([f"ORD_{value}" for value in order_id_ints])

network = np.random.choice(NETWORKS, n, p=NETWORK_PROBS)
payment_rail = np.array([NETWORK_TO_RAIL[x] for x in network])
normalized_category = np.random.choice(CATEGORIES, n, p=CATEGORY_PROBS)

# Amount now conditioned on category
amount_logmean = np.array([CATEGORY_AMOUNT_LOGMEAN[c] for c in normalized_category])
dispute_amount_inr = np.round(np.random.lognormal(mean=amount_logmean, sigma=AMOUNT_LOGSIGMA), 2)

BASE_DATE = pd.Timestamp("2026-01-01")
transaction_date = BASE_DATE + pd.to_timedelta(np.random.randint(0, 210, n), unit="D")
filing_delay_days = np.random.randint(1, 90, n)
dispute_filed_date = transaction_date + pd.to_timedelta(filing_delay_days, unit="D")

is_tokenized = np.random.choice([True, False], n, p=[0.7, 0.3])
otp_entry_duration_sec = np.random.randint(1, 45, n)

# --- Fraud-conditioning fix ---
# A case's account activity looks different depending on whether it's a
# genuine account takeover or a mislabeled friendly-fraud claim. FRAUD_
# UNAUTHORIZED cases get a much lower "looks like the real accountholder"
# rate than everything else, and the two behavioral features below are
# drawn CONDITIONAL on this - not independently, like v3 did.
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

# --- New signals to close the coverage gap ---
# transaction_record_match: do internal billing records clearly back the
# merchant (single clean charge, invoice matches amount, refund actually
# processed)? Drives the "billing accuracy" categories.
transaction_record_match_true = np.random.random(n) < 0.75
# post_dispute_activity: evidence contradicting the customer's claim -
# a return that was never processed (NOT_AS_DESCRIBED), or usage logs
# showing the service was used after the "not provided" claim.
post_dispute_activity_true = np.random.random(n) < 0.35

previous_refunds = np.random.poisson(lam=0.5, size=n)
previous_chargebacks = np.random.choice([0, 1, 2], n, p=[0.90, 0.08, 0.02])

cases_df = pd.DataFrame({
    "case_id": case_id, "transaction_id": transaction_id, "order_id": order_id,
    "payment_rail": payment_rail, "network": network,
    "normalized_category": normalized_category,
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

# ------------------------------------------------------------------
# 5. EVIDENCE-LEVEL DATA (unchanged from v3)
# ------------------------------------------------------------------

evidence_records = []
for _, case in cases_df.iterrows():
    cid, tid, oid = case["case_id"], case["transaction_id"], case["order_id"]
    amount, category = case["dispute_amount_inr"], case["normalized_category"]
    rules = EVIDENCE_RULES[category]
    required, relevant, distractors = rules["required"], rules["relevant"], rules["distractors"]

    selected_required = required.copy()
    num_relevant = np.random.randint(1, len(relevant) + 1)
    selected_relevant = list(np.random.choice(relevant, size=num_relevant, replace=False))
    num_distractors = np.random.randint(2, min(len(distractors), MAX_EVIDENCE_PER_CASE) + 1)
    selected_distractors = list(np.random.choice(distractors, size=num_distractors, replace=False))

    all_evidence = (selected_required + selected_relevant + selected_distractors)[:MAX_EVIDENCE_PER_CASE]

    for j, evidence_type in enumerate(all_evidence):
        is_required = evidence_type in required
        is_relevant = is_required or evidence_type in relevant
        is_contradictory = bool(np.random.choice([True, False], p=[0.03, 0.97])) if is_relevant else False
        evidence_strength = (
            np.random.uniform(0.75, 1.0) if is_required else
            np.random.uniform(0.55, 0.90) if is_relevant else
            np.random.uniform(0.05, 0.40)
        )
        evidence_quality = float(np.clip(evidence_strength + np.random.normal(0, 0.08), 0, 1))

        evidence_records.append({
            "evidence_id": f"{cid}_EV_{j:02d}", "case_id": cid,
            "transaction_id": tid, "order_id": oid, "normalized_category": category,
            "evidence_type": evidence_type,
            "document_text": generate_evidence_text(evidence_type, tid, oid, amount, category),
            "is_required": is_required, "is_relevant": is_relevant,
            "is_contradictory": is_contradictory,
            "evidence_strength_score": round(float(evidence_strength), 4),
            "evidence_quality_score": round(evidence_quality, 4),
            "ground_truth_rank": 1 if is_required else 2 if is_relevant else 0,
        })

evidence_df = pd.DataFrame(evidence_records)

evidence_summary = evidence_df.groupby("case_id").agg(
    total_evidence=("evidence_id", "count"),
    relevant_evidence_count=("is_relevant", "sum"),
    required_evidence_count=("is_required", "sum"),
    contradictory_evidence_count=("is_contradictory", "sum"),
).reset_index()

cases_df = cases_df.merge(evidence_summary, on="case_id", how="left")

# ------------------------------------------------------------------
# 6. WIN PROBABILITY - now every category has real logic, and none of
#    it is gated by network (fraud and reconciliation issues can
#    happen on any rail; network only affects the economics later).
# ------------------------------------------------------------------

c = cases_df
conditions = [
    # FRAUD_UNAUTHORIZED - account-takeover signature always loses
    (c.normalized_category == "FRAUD_UNAUTHORIZED") & (c.sim_swap_flag_48h_true | (c.otp_entry_duration_sec <= 2)),
    # genuinely inconsistent account pattern (looks like real theft)
    (c.normalized_category == "FRAUD_UNAUTHORIZED") & ~c.account_pattern_consistent_true,
    # consistent pattern + strong corroborating evidence (CE3.0-style)
    (c.normalized_category == "FRAUD_UNAUTHORIZED") & c.account_pattern_consistent_true & (c.previous_successful_orders >= 2) & c.ip_geo_match_true,
    # consistent pattern but thin evidence
    (c.normalized_category == "FRAUD_UNAUTHORIZED"),

    # RECON_SETTLEMENT_ERROR - applies on any network now
    (c.normalized_category == "RECON_SETTLEMENT_ERROR") & c.bank_rrn_match_true,
    (c.normalized_category == "RECON_SETTLEMENT_ERROR"),

    # ITEM_NOT_RECEIVED - unchanged from v3, already worked
    (c.normalized_category == "ITEM_NOT_RECEIVED") & c.delivery_otp_verified_true,
    (c.normalized_category == "ITEM_NOT_RECEIVED") & ~c.delivery_otp_verified_true & (c.filing_delay_days > 60),
    (c.normalized_category == "ITEM_NOT_RECEIVED"),

    # NOT_AS_DESCRIBED - a return already on file is close to a slam dunk
    (c.normalized_category == "NOT_AS_DESCRIBED") & c.post_dispute_activity_true,
    (c.normalized_category == "NOT_AS_DESCRIBED"),

    # SERVICE_NOT_PROVIDED - usage after the "not provided" claim contradicts it
    (c.normalized_category == "SERVICE_NOT_PROVIDED") & c.post_dispute_activity_true,
    (c.normalized_category == "SERVICE_NOT_PROVIDED"),

    # DUPLICATE_TRANSACTION / INCORRECT_AMOUNT / REFUND_NOT_RECEIVED -
    # all three are "do the records clearly match" style disputes
    (c.normalized_category == "DUPLICATE_TRANSACTION") & c.transaction_record_match_true,
    (c.normalized_category == "DUPLICATE_TRANSACTION"),
    (c.normalized_category == "INCORRECT_AMOUNT") & c.transaction_record_match_true,
    (c.normalized_category == "INCORRECT_AMOUNT"),
    (c.normalized_category == "REFUND_NOT_RECEIVED") & c.transaction_record_match_true,
    (c.normalized_category == "REFUND_NOT_RECEIVED"),

    # SUBSCRIPTION_CANCELED - unchanged from v3
    (c.normalized_category == "SUBSCRIPTION_CANCELED") & (c.relevant_evidence_count >= 3),
    (c.normalized_category == "SUBSCRIPTION_CANCELED"),
]
choices = [
    0.03, 0.08, 0.55, 0.25,          # fraud
    0.92, 0.05,                       # recon
    0.85, 0.45, 0.10,                 # item not received
    0.92, 0.30,                       # not as described
    0.88, 0.18,                       # service not provided
    0.90, 0.15,                       # duplicate transaction
    0.90, 0.12,                       # incorrect amount
    0.90, 0.10,                       # refund not received
    0.75, 0.20,                       # subscription canceled
]
cases_df["base_win_prob"] = np.select(conditions, choices, default=0.50)  # default should now never fire

noise = np.random.normal(0, LABEL_NOISE_STD, n)
cases_df["noisy_win_prob"] = np.clip(cases_df["base_win_prob"] + noise, 0.02, 0.98)
cases_df["merchant_representment_won"] = np.random.binomial(1, cases_df["noisy_win_prob"])

# ------------------------------------------------------------------
# 7. OBSERVED (noisy) versions of every "_true" signal
# ------------------------------------------------------------------

def flip_noisy(true_series, p=FEATURE_FLIP_PROB):
    flips = np.random.random(len(true_series)) < p
    return np.where(flips, ~true_series.values, true_series.values)

for col in ["bank_rrn_match", "delivery_otp_verified", "ip_geo_match",
            "sim_swap_flag_48h", "transaction_record_match", "post_dispute_activity"]:
    cases_df[col] = flip_noisy(cases_df[f"{col}_true"])

# ------------------------------------------------------------------
# 8. ECONOMIC FIELDS
# ------------------------------------------------------------------

cases_df["representment_fee_inr"] = np.where(cases_df.network.isin(["RUPAY", "UPI_NPCI"]), 300, 1200)
cases_df["false_positive_cost_inr"] = cases_df["representment_fee_inr"] + 500
cases_df["false_negative_cost_inr"] = cases_df["dispute_amount_inr"]

# ------------------------------------------------------------------
# 9. TIME-BASED SPLIT
# ------------------------------------------------------------------

cases_df = cases_df.sort_values("dispute_filed_date").reset_index(drop=True)
train_cut, val_cut = int(n * 0.70), int(n * 0.85)
cases_df["dataset_split"] = (
    ["train"] * train_cut + ["validation"] * (val_cut - train_cut) + ["test"] * (n - val_cut)
)
evidence_df = evidence_df.merge(cases_df[["case_id", "dataset_split"]], on="case_id", how="left")

# ------------------------------------------------------------------
# 10. EXPORT
# ------------------------------------------------------------------

true_cols = ["bank_rrn_match_true", "delivery_otp_verified_true", "ip_geo_match_true",
             "sim_swap_flag_48h_true", "transaction_record_match_true",
             "post_dispute_activity_true", "account_pattern_consistent_true"]

cases_df[["case_id"] + true_cols + ["base_win_prob", "noisy_win_prob", "merchant_representment_won"]].to_csv(
    "chargeback_cases_DEBUG.csv", index=False)

model_facing = cases_df.drop(columns=true_cols + ["base_win_prob", "noisy_win_prob"])
model_facing.to_csv("chargeback_cases.csv", index=False)
evidence_df.to_csv("evidence_items.csv", index=False)

# ------------------------------------------------------------------
# 11. SANITY CHECKS
# ------------------------------------------------------------------

print(f"Cases: {len(cases_df):,}   Evidence items: {len(evidence_df):,}")
print(f"Overall merchant win rate: {cases_df['merchant_representment_won'].mean():.2%}\n")

print("Category distribution (should now be fraud-heavy, not uniform):")
print(cases_df["normalized_category"].value_counts(normalize=True).round(3))

print("\nRows still landing on the 0.50 dead-default (should be ~0 now):")
print((cases_df["base_win_prob"] == 0.50).sum())

print("\nWin rate by category:")
print(cases_df.groupby("normalized_category")["merchant_representment_won"].mean().round(3))

print("\nFRAUD_UNAUTHORIZED win rate by network (real-world target ~17%):")
print(cases_df[cases_df.normalized_category == "FRAUD_UNAUTHORIZED"].groupby("network")["merchant_representment_won"].mean().round(3))

print("\nMedian disputed amount by category (should now differ):")
print(cases_df.groupby("normalized_category")["dispute_amount_inr"].median().round(0))

print("\nSplit sizes and date ranges:")
print(cases_df.groupby("dataset_split")["dispute_filed_date"].agg(["count", "min", "max"]))