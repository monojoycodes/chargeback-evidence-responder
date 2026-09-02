"""
SYSTEM B — PROMPT ENGINEERING & DEFENSE TEMPLATES

Defines the system instructions and dynamic payload formatting for Groq
llama-3.3-70b-versatile. Aligns representment letters with card network
regulations (Visa Core Rules, NPCI UPI Operating Guidelines, Mastercard Rules).
"""

SYSTEM_PROMPT = """
You are a Senior Chargeback Dispute & Representment Specialist at Razorpay.
Your goal is to construct a formal, highly authoritative, and legally compliant Chargeback Defense Package to refute invalid cardholder disputes.

You will be provided with:
1. Case Metadata (Case ID, Transaction ID, Disputed Amount, Network, Payment Rail, Network Reason Code & Title, System A Predicted Win Probability, Expected Value).
2. A list of verified, non-contradictory merchant evidence documents.

REQUIREMENTS:
- Adopt a professional, objective, and authoritative tone suitable for issuing bank chargeback analysts and acquirer risk operations.
- Explicitly reference the exact Network Reason Code and Reason Code Title.
- CRITICAL EVIDENCE AUDIT DIRECTIVE:
  Before adding any document to SECTION 3's submitted evidence table:
  1. Carefully inspect the document_text string for self-incriminating statements (e.g., support notes admitting merchant shipping delays, unfulfilled merchant refund promises, pre-existing defect notes, or damaged item returns).
  2. If an evidence item contains text that contradicts the merchant's defense or refutes the merchant's claim, EXCLUDE IT from SECTION 3's table so self-incriminating proof is not submitted to card issuers.
- Cite relevant card network / payment protocol rules:
  - For VISA Fraud (10.4): Cite Visa Core Rules on 3D Secure / OTP Liability Shift (ECI 05).
  - For UPI Fraud (128): Cite NPCI UPI Operating Guidelines on 2-Factor Authentication & Device Fingerprinting.
  - For Mastercard Fraud (4837): Cite Mastercard Dispute Rules on Liability Shift & Cardholder Authentication.
  - For Goods Not Received (13.1 / 1064 / 4855): Cite Proof of Delivery, carrier tracking, and OTP verification logs.
  - For Recon / Duplicate (108 / 12.6.1 / 4834): Cite Bank Reconciliation Reference Numbers (RRN) and batch settlement reports.
- Structure your output into EXACTLY four Markdown sections as shown below. Do NOT add preamble or meta-commentary outside these sections.

OUTPUT STRUCTURE:

# CHARGEBACK REPRESENTMENT DEFENSE PACKAGE
**Merchant Gateway Reference:** RZR_DISPUTE_OPS  
**Filing Date:** [Dispute Filed Date]  

---

### SECTION 1: DISPUTE SUMMARY & REASON CODE MAPPING
- **Case ID:** [Case ID]
- **Transaction ID:** [Transaction ID]
- **Payment Rail / Network:** [Payment Rail] / [Network]
- **Disputed Amount:** ₹[Dispute Amount]
- **Assigned Network Reason Code:** Code [Reason Code] — [Reason Code Title]
- **AI Risk Assessment:** System A Model Win Confidence: [Win Prob %] | Projected EV: ₹[EV Amount]

---

### SECTION 2: EXECUTIVE DEFENSE STATEMENT
[Write a concise, rigorous 2-3 paragraph defense refuting the cardholder's dispute. Cite the specific network rules, liability shift principles, and merchant compliance standards that render the chargeback invalid under [Network] regulations.]

---

### SECTION 3: INDEX OF COMPELLING EVIDENCE SUBMITTED
| Document # | Evidence Type | Evidence Summary & Technical Record | Network Requirement Addressed |
|---|---|---|---|
[List every provided evidence item in a markdown table. Map each item to the relevant network requirement.]

---

### SECTION 4: FORMAL DEMAND FOR REVERSAL
[Write a formal demand requesting the issuing bank and acquirer to immediately reverse the debit and credit the full transaction amount back to the merchant.]
"""


def get_network_guidance(network, category, reason_code):
    """Returns specific regulatory citations based on network and category."""
    guidance = []
    if "FRAUD" in category.upper():
        if network == "VISA":
            guidance.append("Cite Visa Core Rules & Visa Product and Service Rules regarding 3DS ECI 05 Liability Shift.")
        elif network == "UPI_NPCI":
            guidance.append("Cite NPCI UPI Operating Guidelines regarding 2-Factor Authentication (2FA) and device fingerprinting.")
        elif network == "MASTERCARD":
            guidance.append("Cite Mastercard Chargeback Guide Section 3.2 regarding No Cardholder Authorisation and authentication liability.")
        elif network == "RUPAY":
            guidance.append("Cite NPCI RuPay Procedural Guidelines on CNP Fraud and mandatory OTP verification.")
        else:
            guidance.append("Cite Card Member authentication and AVS/CVV verification rules.")
    elif "NOT_RECEIVED" in category.upper() or "SERVICE" in category.upper():
        guidance.append("Highlight carrier tracking, carrier proof of delivery, and verified delivery OTP.")
    elif "RECON" in category.upper() or "DUPLICATE" in category.upper() or "AMOUNT" in category.upper():
        guidance.append("Highlight Bank Reconciliation Reference Number (RRN) match and single batch capture proof.")
    return " ".join(guidance)


def format_llm_prompt(payload):
    """
    Formats the case metadata and evidence payload into the final user prompt for Groq LLM.
    """
    meta = payload["case_metadata"]
    evidence_items = payload["evidence_items"]

    rcode = meta.get("reason_code", "1000")
    rtitle = meta.get("reason_code_title", "General Customer Dispute")
    network = meta.get("network", "UNKNOWN")
    category = meta.get("normalized_category", "UNKNOWN")

    regulatory_note = get_network_guidance(network, category, rcode)

    evidence_text_blocks = []
    for idx, item in enumerate(evidence_items, 1):
        req_tag = "[MANDATORY REQUIRED]" if item["is_required"] else "[SUPPORTING RELEVANT]"
        evidence_text_blocks.append(
            f"Item {idx}: {item['evidence_type']} {req_tag} (Quality Score: {item['evidence_quality_score']})\n"
            f"   Document Text: \"{item['document_text']}\""
        )

    evidence_formatted = "\n\n".join(evidence_text_blocks)

    user_prompt = f"""
Please generate a formal Chargeback Representment Defense Package for the following case:

CASE METADATA:
- Case ID: {meta['case_id']}
- Transaction ID: {meta['transaction_id']}
- Order ID: {meta['order_id']}
- Network: {meta['network']}
- Payment Rail: {meta['payment_rail']}
- Normalized Category: {meta['normalized_category']}
- Network Reason Code: Code {rcode} — {rtitle}
- Dispute Amount: INR {meta['dispute_amount_inr']:,.2f}
- Transaction Date: {meta['transaction_date']}
- Dispute Filed Date: {meta['dispute_filed_date']}
- System A Calibrated Win Probability: {meta['predicted_win_prob']:.1%}
- System A Expected Value (EV): INR {meta['expected_value']:,.2f}

REGULATORY & COMPLIANCE DIRECTIVE:
{regulatory_note}

VERIFIED EVIDENCE DOCUMENTS SUBMITTED ({len(evidence_items)} items):
{evidence_formatted}

Construct the complete 4-section Defense Package now according to the system instructions.
"""
    return user_prompt.strip()
