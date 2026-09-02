"""
CHARGEBACK EVIDENCE RESPONDER — SYNTHETIC DATASET GENERATOR (v6)

Optimized with:
  1. Real network-specific Reason Codes & Titles from context_docs/chargeback-reason-codes_artifact2.md
     (Visa, Mastercard, UPI NPCI, RuPay, Amex).
  2. Document types directly mapped to mandatory evidence requirements per network code.
  3. Realistic multi-modal dispute amounts & merchant sector distributions.
  4. Hidden unobserved confounders (issuing bank leniency & cardholder counter-evidence) for metric honesty.

Outputs:
  data/chargeback_cases.csv        - model-facing case features + label
  data/evidence_items.csv          - evidence records linked by case_id
  data/chargeback_cases_DEBUG.csv  - internal only (includes hidden confounders and true flags)
"""

from pathlib import Path
import numpy as np
import pandas as pd

np.random.seed(42)
rng = np.random.default_rng(42)

NUM_CASES = 10_000
MAX_EVIDENCE_PER_CASE = 12
LABEL_NOISE_STD = 0.04
FEATURE_FLIP_PROB = 0.08

# ------------------------------------------------------------------
# 1. NETWORKS & PAYMENT RAILS
# ------------------------------------------------------------------

NETWORKS = ["UPI_NPCI", "RUPAY", "VISA", "MASTERCARD", "AMERICAN_EXPRESS"]
NETWORK_PROBS = [0.42, 0.28, 0.16, 0.10, 0.04]  # Reflects Indian digital payment market share
NETWORK_TO_RAIL = {
    "UPI_NPCI": "UPI", "RUPAY": "CARD", "VISA": "CARD",
    "MASTERCARD": "CARD", "AMERICAN_EXPRESS": "CARD",
}

# ------------------------------------------------------------------
# 2. DISPUTE CATEGORIES & SECTOR-AWARE AMOUNT DISTRIBUTIONS
# ------------------------------------------------------------------

CATEGORIES = [
    "FRAUD_UNAUTHORIZED", "ITEM_NOT_RECEIVED", "NOT_AS_DESCRIBED",
    "RECON_SETTLEMENT_ERROR", "REFUND_NOT_RECEIVED", "DUPLICATE_TRANSACTION",
    "SUBSCRIPTION_CANCELED", "SERVICE_NOT_PROVIDED", "INCORRECT_AMOUNT",
]
CATEGORY_PROBS = [0.28, 0.20, 0.12, 0.10, 0.08, 0.07, 0.06, 0.05, 0.04]

# Multimodal/realistic log-mean and log-sigma by category
CATEGORY_AMOUNT_PARAMS = {
    "FRAUD_UNAUTHORIZED": (7.4, 1.1),      # Avg ~₹2,500 - high risk
    "SERVICE_NOT_PROVIDED": (8.2, 0.9),    # Avg ~₹4,500 - services/travel
    "ITEM_NOT_RECEIVED": (7.1, 1.0),       # Avg ~₹1,800 - e-commerce retail
    "NOT_AS_DESCRIBED": (7.2, 0.9),        # Avg ~₹1,950 - electronics/apparel
    "DUPLICATE_TRANSACTION": (6.8, 1.0),   # Avg ~₹1,200
    "INCORRECT_AMOUNT": (6.7, 1.1),        # Avg ~₹1,100
    "REFUND_NOT_RECEIVED": (7.0, 1.0),     # Avg ~₹1,600
    "RECON_SETTLEMENT_ERROR": (6.2, 0.8),  # Avg ~₹600 - micro-settlements
    "SUBSCRIPTION_CANCELED": (5.6, 0.7),   # Avg ~₹350 - digital SaaS / OTT
}

# ------------------------------------------------------------------
# 3. REASON CODE LOOKUP TABLE (From context_docs/chargeback-reason-codes_artifact2.md)
# ------------------------------------------------------------------

NETWORK_REASON_CODES = {
    # UPI (NPCI)
    ("UPI_NPCI", "FRAUD_UNAUTHORIZED"): ("128", "Fraudulent Transaction"),
    ("UPI_NPCI", "ITEM_NOT_RECEIVED"): ("1064", "Goods/Services Not Received"),
    ("UPI_NPCI", "NOT_AS_DESCRIBED"): ("1062", "Goods/Services Not As Described"),
    ("UPI_NPCI", "REFUND_NOT_RECEIVED"): ("1061", "Credit Not Processed"),
    ("UPI_NPCI", "DUPLICATE_TRANSACTION"): ("1084", "Duplicate Processing"),
    ("UPI_NPCI", "INCORRECT_AMOUNT"): ("1085", "Charge Amount Exceeds Authorisation Amount"),
    ("UPI_NPCI", "RECON_SETTLEMENT_ERROR"): ("108", "Remiter Debited but Beneficiary Not Credited"),
    ("UPI_NPCI", "SERVICE_NOT_PROVIDED"): ("1064", "Goods/Services Not Received"),
    ("UPI_NPCI", "SUBSCRIPTION_CANCELED"): ("1062", "Goods/Services Not As Described"),

    # VISA
    ("VISA", "FRAUD_UNAUTHORIZED"): ("10.4", "Other Fraud – Card-Absent Environment"),
    ("VISA", "ITEM_NOT_RECEIVED"): ("13.1", "Merchandise/Services Not Received"),
    ("VISA", "NOT_AS_DESCRIBED"): ("13.3", "Not as Described or Defective Merchandise/Services"),
    ("VISA", "REFUND_NOT_RECEIVED"): ("13.6", "Credit Not Processed"),
    ("VISA", "DUPLICATE_TRANSACTION"): ("12.6.1", "Duplicate Processing – Single Authorisation"),
    ("VISA", "INCORRECT_AMOUNT"): ("12.5", "Incorrect Amount"),
    ("VISA", "RECON_SETTLEMENT_ERROR"): ("12.2", "Incorrect Transaction Code"),
    ("VISA", "SERVICE_NOT_PROVIDED"): ("13.1", "Merchandise/Services Not Received"),
    ("VISA", "SUBSCRIPTION_CANCELED"): ("13.2", "Cancelled Recurring Transaction"),

    # MASTERCARD
    ("MASTERCARD", "FRAUD_UNAUTHORIZED"): ("4837", "No Cardholder Authorisation"),
    ("MASTERCARD", "ITEM_NOT_RECEIVED"): ("4855", "Goods or Services Not Provided"),
    ("MASTERCARD", "NOT_AS_DESCRIBED"): ("4853", "Cardholder Dispute – Defective/Not as Described"),
    ("MASTERCARD", "REFUND_NOT_RECEIVED"): ("4853", "Cardholder Dispute"),
    ("MASTERCARD", "DUPLICATE_TRANSACTION"): ("4834", "Duplicate Processing"),
    ("MASTERCARD", "INCORRECT_AMOUNT"): ("4834", "Duplicate Processing / Incorrect Amount"),
    ("MASTERCARD", "RECON_SETTLEMENT_ERROR"): ("4808", "Authorisation-Related Chargeback"),
    ("MASTERCARD", "SERVICE_NOT_PROVIDED"): ("4855", "Goods or Services Not Provided"),
    ("MASTERCARD", "SUBSCRIPTION_CANCELED"): ("4841", "Cancelled Recurring/Digital Goods Transaction"),

    # RUPAY
    ("RUPAY", "FRAUD_UNAUTHORIZED"): ("1142", "Fraudulent Card-Not-Present Transaction"),
    ("RUPAY", "ITEM_NOT_RECEIVED"): ("1064", "Goods/Services Not Received"),
    ("RUPAY", "NOT_AS_DESCRIBED"): ("1062", "Goods/Services Not As Described"),
    ("RUPAY", "REFUND_NOT_RECEIVED"): ("1061", "Credit Not Processed"),
    ("RUPAY", "DUPLICATE_TRANSACTION"): ("1084", "Duplicate Processing"),
    ("RUPAY", "INCORRECT_AMOUNT"): ("1085", "Charge Amount Exceeds Authorisation Amount"),
    ("RUPAY", "RECON_SETTLEMENT_ERROR"): ("1065", "Debit on Failed Transaction"),
    ("RUPAY", "SERVICE_NOT_PROVIDED"): ("1064", "Goods/Services Not Received"),
    ("RUPAY", "SUBSCRIPTION_CANCELED"): ("1062", "Goods/Services Not As Described"),

    # AMERICAN EXPRESS
    ("AMERICAN_EXPRESS", "FRAUD_UNAUTHORIZED"): ("F24", "No Card Member Authorisation"),
    ("AMERICAN_EXPRESS", "ITEM_NOT_RECEIVED"): ("C08", "Goods/Services Not Received or Only Partially Received"),
    ("AMERICAN_EXPRESS", "NOT_AS_DESCRIBED"): ("C31", "Goods/Services Not as Described"),
    ("AMERICAN_EXPRESS", "REFUND_NOT_RECEIVED"): ("C08", "Goods/Services Not Received"),
    ("AMERICAN_EXPRESS", "DUPLICATE_TRANSACTION"): ("P02", "Duplicate Charge"),
    ("AMERICAN_EXPRESS", "INCORRECT_AMOUNT"): ("P05", "Incorrect Amount"),
    ("AMERICAN_EXPRESS", "RECON_SETTLEMENT_ERROR"): ("P08", "Processing Error"),
    ("AMERICAN_EXPRESS", "SERVICE_NOT_PROVIDED"): ("C08", "Goods/Services Not Received"),
    ("AMERICAN_EXPRESS", "SUBSCRIPTION_CANCELED"): ("C31", "Cancelled Recurring Charge"),
}

# ------------------------------------------------------------------
# 4. EVIDENCE REQUIREMENT RULES (Aligned with context_docs)
# ------------------------------------------------------------------

EVIDENCE_RULES = {
    "FRAUD_UNAUTHORIZED": {
        "required": ["PAYMENT_AUTHORIZATION", "THREE_DS_AUTHENTICATION"],
        "relevant": ["DEVICE_LOG", "IP_LOG", "LOGIN_LOG", "AVS_CVV_VERIFICATION",
                     "PRIOR_UNDISPUTED_TRANSACTION", "ORDER_CONFIRMATION",
                     "CUSTOMER_COMMUNICATION"],
        "distractors": ["REFUND_POLICY", "RETURN_POLICY", "DELIVERY_TRACKING",
                         "SERVICE_COMPLETION_PROOF"],
    },
    "ITEM_NOT_RECEIVED": {
        "required": ["DELIVERY_TRACKING", "PROOF_OF_DELIVERY"],
        "relevant": ["DELIVERY_OTP", "SIGNED_DELIVERY", "ORDER_CONFIRMATION",
                     "CUSTOMER_COMMUNICATION", "INVOICE", "TERMS_AND_CONDITIONS"],
        "distractors": ["DEVICE_LOG", "LOGIN_LOG", "REFUND_POLICY"],
    },
    "NOT_AS_DESCRIBED": {
        "required": ["ORDER_CONFIRMATION", "PRODUCT_DESCRIPTION"],
        "relevant": ["PRODUCT_IMAGES", "CUSTOMER_COMMUNICATION", "QC_RECORDS",
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
        "relevant": ["TRANSACTION_RECEIPT", "BANK_RRN_RECORD", "BATCH_PROCESSING_REPORT",
                     "ORDER_CONFIRMATION", "REFUND_RECORD"],
        "distractors": ["DELIVERY_TRACKING", "PRODUCT_IMAGES", "LOGIN_LOG"],
    },
    "INCORRECT_AMOUNT": {
        "required": ["TRANSACTION_RECEIPT", "INVOICE"],
        "relevant": ["PAYMENT_AUTHORIZATION", "ORDER_CONFIRMATION",
                     "BANK_RRN_RECORD", "PRICE_BREAKDOWN"],
        "distractors": ["DELIVERY_TRACKING", "DEVICE_LOG", "RETURN_POLICY"],
    },
    "REFUND_NOT_RECEIVED": {
        "required": ["REFUND_RECORD"],
        "relevant": ["BANK_RRN_RECORD", "CUSTOMER_COMMUNICATION",
                     "CANCELLATION_RECORD", "TRANSACTION_RECEIPT", "REFUND_POLICY"],
        "distractors": ["DELIVERY_TRACKING", "PRODUCT_IMAGES", "DEVICE_LOG"],
    },
    "SUBSCRIPTION_CANCELED": {
        "required": ["CANCELLATION_RECORD"],
        "relevant": ["SUBSCRIPTION_USAGE_LOG", "TERMS_ACCEPTANCE", "CANCELLATION_POLICY",
                     "CUSTOMER_COMMUNICATION", "PAYMENT_AUTHORIZATION"],
        "distractors": ["DELIVERY_TRACKING", "PROOF_OF_DELIVERY", "PRODUCT_IMAGES"],
    },
    "RECON_SETTLEMENT_ERROR": {
        "required": ["BANK_RRN_RECORD"],
        "relevant": ["SETTLEMENT_RECORD", "PAYMENT_AUTHORIZATION",
                     "TRANSACTION_RECEIPT", "INTERNAL_SYSTEM_LOGS"],
        "distractors": ["PRODUCT_IMAGES", "RETURN_POLICY", "CUSTOMER_COMMUNICATION"],
    },
}

EVIDENCE_TEMPLATES = {
    "PAYMENT_AUTHORIZATION": lambda t, o, a, c, code: f"Payment authorization successful for transaction {t}. Auth Code: AUTH_{t[-6:]}. Amount: INR {a:.2f}.",
    "THREE_DS_AUTHENTICATION": lambda t, o, a, c, code: f"3DS / OTP authentication successfully verified for transaction {t}. ECI: 05 (Liability Shift Active).",
    "AVS_CVV_VERIFICATION": lambda t, o, a, c, code: f"CVV2 match successful (Match code M) and AVS zip code verified for transaction {t}.",
    "DEVICE_LOG": lambda t, o, a, c, code: f"Device fingerprint and MAC recorded during transaction {t}. Device history confirms previous account usage.",
    "IP_LOG": lambda t, o, a, c, code: f"IP address and ISP geolocation record associated with transaction {t} match registered cardholder location.",
    "LOGIN_LOG": lambda t, o, a, c, code: f"Customer account login activity authenticated before transaction {t}.",
    "PRIOR_UNDISPUTED_TRANSACTION": lambda t, o, a, c, code: "Customer completed prior undisputed transaction on same device and card.",
    "ORDER_CONFIRMATION": lambda t, o, a, c, code: f"Order {o} confirmed and receipt dispatched to registered email. Total: INR {a:.2f}.",
    "CUSTOMER_COMMUNICATION": lambda t, o, a, c, code: f"Customer communication logs regarding order {o} for chargeback reason code {code}.",
    "DELIVERY_TRACKING": lambda t, o, a, c, code: f"Courier tracking record for order {o} confirms dispatch and transit.",
    "PROOF_OF_DELIVERY": lambda t, o, a, c, code: f"Carrier proof of delivery confirmation generated for order {o}.",
    "DELIVERY_OTP": lambda t, o, a, c, code: f"Delivery OTP verified at destination for order {o}.",
    "SIGNED_DELIVERY": lambda t, o, a, c, code: f"Signed proof of delivery receipt on file for order {o}.",
    "INVOICE": lambda t, o, a, c, code: f"Tax Invoice generated for order {o} with price breakdown. Total: INR {a:.2f}.",
    "PRODUCT_DESCRIPTION": lambda t, o, a, c, code: "Product specifications and terms displayed during purchase.",
    "PRODUCT_IMAGES": lambda t, o, a, c, code: f"Product photos and QC inspector stamp stored for order {o}.",
    "QC_RECORDS": lambda t, o, a, c, code: f"Quality Control dispatch certificate approved for order {o}.",
    "RETURN_RECORD": lambda t, o, a, c, code: "Return request status and merchant return processing log.",
    "TERMS_AND_CONDITIONS": lambda t, o, a, c, code: "Merchant terms of service and fulfillment policy accepted at checkout.",
    "SERVICE_COMPLETION_PROOF": lambda t, o, a, c, code: f"Service completion sign-off record available for order {o}.",
    "CONTRACT": lambda t, o, a, c, code: f"Executed service contract linked to order {o}.",
    "ACCOUNT_USAGE_LOG": lambda t, o, a, c, code: "Post-activation digital service access and usage logs.",
    "TERMS_ACCEPTANCE": lambda t, o, a, c, code: "Customer explicitly checked acceptance of subscription terms.",
    "TRANSACTION_RECEIPT": lambda t, o, a, c, code: f"Itemized transaction receipt for {t}. Amount: INR {a:.2f}.",
    "BANK_RRN_RECORD": lambda t, o, a, c, code: "Bank Reconciliation Reference Number (RRN) match confirmed by acquiring bank.",
    "BATCH_PROCESSING_REPORT": lambda t, o, a, c, code: f"Acquirer batch settlement report confirming single capture for {t}.",
    "PRICE_BREAKDOWN": lambda t, o, a, c, code: f"Itemized pricing, taxes, and shipping fee breakdown for order {o}.",
    "REFUND_RECORD": lambda t, o, a, c, code: f"Refund ARN processing record generated for transaction {t}.",
    "CANCELLATION_RECORD": lambda t, o, a, c, code: "Customer subscription cancellation log and date timestamp.",
    "CANCELLATION_POLICY": lambda t, o, a, c, code: "Merchant published cancellation policy and deadline disclosure.",
    "SUBSCRIPTION_USAGE_LOG": lambda t, o, a, c, code: "Active digital subscription stream/download log post-billing.",
    "SETTLEMENT_RECORD": lambda t, o, a, c, code: f"Settlement payout record available for transaction {t}.",
    "INTERNAL_SYSTEM_LOGS": lambda t, o, a, c, code: f"Core banking API response logs for transaction {t}.",
    "REFUND_POLICY": lambda t, o, a, c, code: "Merchant refund policy document.",
    "RETURN_POLICY": lambda t, o, a, c, code: "Merchant return policy document.",
}


CONTRADICTORY_SNIPPETS = {
    "CUSTOMER_COMMUNICATION": lambda t, o, a, c, rcode: f"Support Log for order {o}: Support representative admitted merchant dispatch delay and promised a full refund on 2026-05-10.",
    "DELIVERY_TRACKING": lambda t, o, a, c, rcode: f"Courier tracking exception note for order {o}: Package marked as returned to sender due to damaged outer packaging.",
    "QC_RECORDS": lambda t, o, a, c, rcode: f"Quality Control Inspection Log for order {o}: Inspector noted pre-existing cosmetic defect on product before dispatch.",
    "RETURN_RECORD": lambda t, o, a, c, rcode: f"Merchant RMA Record for order {o}: Return request approved by merchant on 2026-05-12; pending refund issuing.",
    "REFUND_RECORD": lambda t, o, a, c, rcode: f"Merchant Finance Log for transaction {t}: Partial refund processed; discrepancy remaining.",
    "TERMS_AND_CONDITIONS": lambda t, o, a, c, rcode: "Merchant Policy Note: Cancellation window disclosed as 14 days, but purchase was billed post-cancellation deadline.",
}

def generate_evidence_text(evidence_type, transaction_id, order_id, amount, category, reason_code, is_contradictory=False):
    if is_contradictory and evidence_type in CONTRADICTORY_SNIPPETS:
        return CONTRADICTORY_SNIPPETS[evidence_type](transaction_id, order_id, amount, category, reason_code)
    fn = EVIDENCE_TEMPLATES.get(evidence_type)
    return fn(transaction_id, order_id, amount, category, reason_code) if fn else f"Evidence record for transaction {transaction_id}."


# ------------------------------------------------------------------
# 5. CASE-LEVEL GENERATION
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

# Map network + category to exact Reason Code & Title from context_docs
reason_code_list = []
reason_code_title_list = []
for net, cat in zip(network, normalized_category):
    code, title = NETWORK_REASON_CODES.get((net, cat), ("1000", "General Dispute"))
    reason_code_list.append(code)
    reason_code_title_list.append(title)

reason_code = np.array(reason_code_list)
reason_code_title = np.array(reason_code_title_list)

# Realistic sector-aware dispute amounts
dispute_amount_inr = np.zeros(n)
for i, cat in enumerate(normalized_category):
    mu, sigma = CATEGORY_AMOUNT_PARAMS[cat]
    dispute_amount_inr[i] = round(float(np.random.lognormal(mean=mu, sigma=sigma)), 2)

BASE_DATE = pd.Timestamp("2026-01-01")
transaction_date = BASE_DATE + pd.to_timedelta(np.random.randint(0, 210, n), unit="D")
filing_delay_days = np.random.randint(1, 90, n)
dispute_filed_date = transaction_date + pd.to_timedelta(filing_delay_days, unit="D")

is_tokenized = np.random.choice([True, False], n, p=[0.72, 0.28])
otp_entry_duration_sec = np.random.randint(1, 45, n)

account_pattern_consistent_true = np.where(
    normalized_category == "FRAUD_UNAUTHORIZED",
    np.random.random(n) < 0.45,
    np.random.random(n) < 0.90,
)
previous_successful_orders = np.where(
    account_pattern_consistent_true,
    np.random.poisson(lam=3.8, size=n),
    np.random.poisson(lam=0.3, size=n),
)
ip_geo_match_true = np.where(
    account_pattern_consistent_true,
    np.random.random(n) < 0.88,
    np.random.random(n) < 0.15,
)

sim_swap_flag_48h_true = np.random.choice([True, False], n, p=[0.02, 0.98])
bank_rrn_match_true = np.random.choice([True, False], n, p=[0.85, 0.15])
delivery_otp_verified_true = np.random.choice([True, False], n, p=[0.62, 0.38])
transaction_record_match_true = np.random.random(n) < 0.76
post_dispute_activity_true = np.random.random(n) < 0.35

previous_refunds = np.random.poisson(lam=0.5, size=n)
previous_chargebacks = np.random.choice([0, 1, 2], n, p=[0.90, 0.08, 0.02])

cases_df = pd.DataFrame({
    "case_id": case_id, "transaction_id": transaction_id, "order_id": order_id,
    "payment_rail": payment_rail, "network": network,
    "normalized_category": normalized_category,
    "reason_code": reason_code,
    "reason_code_title": reason_code_title,
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
# 6. EVIDENCE-LEVEL GENERATION
# ------------------------------------------------------------------

evidence_records = []
for _, case in cases_df.iterrows():
    cid, tid, oid = case["case_id"], case["transaction_id"], case["order_id"]
    amount, category, rcode = case["dispute_amount_inr"], case["normalized_category"], case["reason_code"]
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
            "transaction_id": tid, "order_id": oid,
            "normalized_category": category,
            "reason_code": rcode,
            "evidence_type": evidence_type,
            "document_text": generate_evidence_text(evidence_type, tid, oid, amount, category, rcode, is_contradictory=is_contradictory),
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
# 7. WIN PROBABILITY & HIDDEN CONFOUNDERS
# ------------------------------------------------------------------

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

    (c.normalized_category == "SERVICE_NOT_PROVIDED") & c.post_dispute_activity_true,
    (c.normalized_category == "SERVICE_NOT_PROVIDED"),

    (c.normalized_category == "DUPLICATE_TRANSACTION") & c.transaction_record_match_true,
    (c.normalized_category == "DUPLICATE_TRANSACTION"),
    (c.normalized_category == "INCORRECT_AMOUNT") & c.transaction_record_match_true,
    (c.normalized_category == "INCORRECT_AMOUNT"),
    (c.normalized_category == "REFUND_NOT_RECEIVED") & c.transaction_record_match_true,
    (c.normalized_category == "REFUND_NOT_RECEIVED"),

    (c.normalized_category == "SUBSCRIPTION_CANCELED") & (c.relevant_evidence_count >= 3),
    (c.normalized_category == "SUBSCRIPTION_CANCELED"),
]
choices = [
    0.03, 0.08, 0.55, 0.25,
    0.92, 0.05,
    0.85, 0.45, 0.10,
    0.92, 0.30,
    0.88, 0.18,
    0.90, 0.15,
    0.90, 0.12,
    0.90, 0.10,
    0.75, 0.20,
]
cases_df["base_win_prob"] = np.select(conditions, choices, default=0.50)

_hidden_bank_leniency = np.random.beta(2, 5, size=n)
_hidden_cardholder_counter = np.random.beta(3, 4, size=n)

_hidden_effect = np.where(
    normalized_category == "FRAUD_UNAUTHORIZED",
    0.20 * (_hidden_bank_leniency - 0.30) - 0.15 * _hidden_cardholder_counter,
    0.12 * (_hidden_bank_leniency - 0.30) - 0.10 * _hidden_cardholder_counter,
)
cases_df["_hidden_bank_leniency"] = _hidden_bank_leniency
cases_df["_hidden_cardholder_counter"] = _hidden_cardholder_counter
cases_df["base_win_prob"] = np.clip(cases_df["base_win_prob"] + _hidden_effect, 0.02, 0.98)

noise = np.random.normal(0, LABEL_NOISE_STD, n)
cases_df["noisy_win_prob"] = np.clip(cases_df["base_win_prob"] + noise, 0.02, 0.98)
cases_df["merchant_representment_won"] = np.random.binomial(1, cases_df["noisy_win_prob"])

# ------------------------------------------------------------------
# 8. OBSERVED (noisy) FEATURES
# ------------------------------------------------------------------

def flip_noisy(true_series, p=FEATURE_FLIP_PROB):
    flips = np.random.random(len(true_series)) < p
    return np.where(flips, ~true_series.values, true_series.values)

for col in ["bank_rrn_match", "delivery_otp_verified", "ip_geo_match",
            "sim_swap_flag_48h", "transaction_record_match", "post_dispute_activity"]:
    cases_df[col] = flip_noisy(cases_df[f"{col}_true"])

# ------------------------------------------------------------------
# 9. ECONOMIC FIELDS
# ------------------------------------------------------------------

cases_df["representment_fee_inr"] = np.where(cases_df.network.isin(["RUPAY", "UPI_NPCI"]), 300, 1200)
cases_df["false_positive_cost_inr"] = cases_df["representment_fee_inr"] + 500
cases_df["false_negative_cost_inr"] = cases_df["dispute_amount_inr"]

# ------------------------------------------------------------------
# 10. TIME-BASED SPLIT & EXPORT
# ------------------------------------------------------------------

cases_df = cases_df.sort_values("dispute_filed_date").reset_index(drop=True)
train_cut, val_cut = int(n * 0.70), int(n * 0.85)
cases_df["dataset_split"] = (
    ["train"] * train_cut + ["validation"] * (val_cut - train_cut) + ["test"] * (n - val_cut)
)
evidence_df = evidence_df.merge(cases_df[["case_id", "dataset_split"]], on="case_id", how="left")

OUT_DIR = Path(__file__).resolve().parent
OUT_DIR.mkdir(parents=True, exist_ok=True)

true_cols = ["bank_rrn_match_true", "delivery_otp_verified_true", "ip_geo_match_true",
             "sim_swap_flag_48h_true", "transaction_record_match_true",
             "post_dispute_activity_true", "account_pattern_consistent_true"]

hidden_cols = ["_hidden_bank_leniency", "_hidden_cardholder_counter"]

def safe_to_csv(df, filepath):
    try:
        df.to_csv(filepath, index=False)
    except PermissionError:
        # Fallback if file is open in VSCode / Excel viewer
        alt_path = filepath.with_name(f"{filepath.stem}_v6{filepath.suffix}")
        df.to_csv(alt_path, index=False)
        print(f"Notice: {filepath.name} is locked by an open editor. Wrote data to {alt_path.name}")

model_facing = cases_df.drop(columns=true_cols + hidden_cols + ["base_win_prob", "noisy_win_prob"])

safe_to_csv(cases_df[["case_id"] + true_cols + hidden_cols + ["base_win_prob", "noisy_win_prob", "merchant_representment_won"]], OUT_DIR / "chargeback_cases_DEBUG.csv")
safe_to_csv(model_facing, OUT_DIR / "chargeback_cases.csv")
safe_to_csv(evidence_df, OUT_DIR / "evidence_items.csv")

# ------------------------------------------------------------------
# 11. SANITY CHECKS
# ------------------------------------------------------------------

print(f"Cases: {len(cases_df):,}   Evidence items: {len(evidence_df):,}")
print(f"Overall merchant win rate: {cases_df['merchant_representment_won'].mean():.2%}")
print(f"Reason Code Count: {cases_df['reason_code'].nunique()} unique network reason codes generated.")
print("\nSample Reason Code mapping:")
print(cases_df[["network", "normalized_category", "reason_code", "reason_code_title"]].drop_duplicates().head(10).to_string(index=False))
