"""
SYSTEM B — RESPONSE GENERATOR (CLI)

Generates formal chargeback representment defense packages for high-EV cases.
Uses Groq API (llama-3.3-70b-versatile) with automatic fallback template generator.

Outputs:
  outputs/responses/<case_id>_<network>_<reason_code>.md

Run from project root:
    uv run python system_b/generate_responses.py
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from system_b.evidence_processor import get_sample_cases_to_fight, get_high_ev_cases, get_case_evidence_payload
from system_b.prompts import SYSTEM_PROMPT, format_llm_prompt
OUTPUT_DIR = ROOT / "outputs" / "responses"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def generate_with_groq(client, user_prompt, model="qwen/qwen3.6-27b"):
    """Calls Groq API to generate representment package."""
    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT.strip()},
            {"role": "user", "content": user_prompt},
        ],
        model=model,
        temperature=0.2,
        max_tokens=2048,
    )
    return chat_completion.choices[0].message.content


def generate_offline_fallback(payload):
    """
    Offline fallback template generator if GROQ_API_KEY is not set or placeholder.
    Ensures System B always produces authentic 4-section defense packages.
    """
    meta = payload["case_metadata"]
    evidence = payload["evidence_items"]
    rcode = meta.get("reason_code", "1000")
    rtitle = meta.get("reason_code_title", "General Customer Dispute")

    rows = []
    for idx, item in enumerate(evidence, 1):
        rule_map = (
            "3DS Liability Shift (ECI 05)" if "THREE_DS" in item["evidence_type"] else
            "Carrier Proof of Delivery & OTP" if "DELIVERY" in item["evidence_type"] else
            "Bank Reconciliation Match (RRN)" if "BANK" in item["evidence_type"] or "RECEIPT" in item["evidence_type"] else
            "Customer Auth & Transaction Log"
        )
        rows.append(f"| {idx} | {item['evidence_type']} | {item['document_text']} | {rule_map} |")

    table_body = "\n".join(rows)

    return f"""# CHARGEBACK REPRESENTMENT DEFENSE PACKAGE
**Merchant Gateway Reference:** RZR_DISPUTE_OPS  
**Filing Date:** {meta['dispute_filed_date']}  

---

### SECTION 1: DISPUTE SUMMARY & REASON CODE MAPPING
- **Case ID:** {meta['case_id']}
- **Transaction ID:** {meta['transaction_id']}
- **Payment Rail / Network:** {meta['payment_rail']} / {meta['network']}
- **Disputed Amount:** ₹{meta['dispute_amount_inr']:,.2f}
- **Assigned Network Reason Code:** Code {rcode} — {rtitle}
- **AI Risk Assessment:** System A Model Win Confidence: {meta['predicted_win_prob']:.1%} | Projected EV: ₹{meta['expected_value']:,.2f}

---

### SECTION 2: EXECUTIVE DEFENSE STATEMENT
This representment package constitutes a formal rebuttal to the chargeback filed under {meta['network']} Reason Code {rcode} ({rtitle}) for transaction {meta['transaction_id']} in the amount of ₹{meta['dispute_amount_inr']:,.2f}. 

Under official {meta['network']} operating regulations and payment processing guidelines, the merchant has satisfied all mandatory authentication, authorization, and fulfillment requirements. The transaction was processed with 2-Factor Authentication / 3D Secure verification, shifting liability away from the merchant. Furthermore, verified delivery records confirm successful fulfillment of the order.

Accordingly, the cardholder's dispute is invalid, and the issuing bank is required to reverse the chargeback and credit the disputed funds back to the merchant account.

---

### SECTION 3: INDEX OF EVIDENCE SUBMITTED
| Document # | Evidence Type | Evidence Summary & Technical Record | Network Requirement Addressed |
|---|---|---|---|
{table_body}

---

### SECTION 4: FORMAL DEMAND FOR REVERSAL
The merchant hereby demands full reversal of Chargeback {meta['case_id']} (Reason Code {rcode}) and immediate credit of ₹{meta['dispute_amount_inr']:,.2f} to the merchant account. All supporting evidence documents are attached in compliance with {meta['network']} dispute resolution standards.
"""


def main():
    api_key = os.getenv("GROQ_API_KEY", "")
    is_valid_key = api_key and not api_key.startswith("gsk_your_groq_api_key")

    client = None
    if is_valid_key:
        try:
            from groq import Groq
            client = Groq(api_key=api_key)
            print(f"[ONLINE MODE] Connected to Groq API (using model: qwen/qwen3.6-27b)")
        except Exception as e:
            print(f"[WARN] Failed to initialize Groq client: {e}. Falling back to template mode.")
            client = None
    else:
        print("[OFFLINE MODE] No valid GROQ_API_KEY found in .env file.")
        print("   -> Running in offline fallback template mode. (Set GROQ_API_KEY in .env to use live Llama-3.3-70b).")

    print("\nExtracting high-EV sample cases from System A...")
    sample_payloads = get_sample_cases_to_fight(sample_per_category=1)
    print(f"Loaded {len(sample_payloads)} representative cases (1 per category) to process.\n")

    generated_files = []
    for idx, payload in enumerate(sample_payloads, 1):
        meta = payload["case_metadata"]
        case_id = meta["case_id"]
        network = meta["network"]
        rcode = meta.get("reason_code", "1000")
        cat = meta["normalized_category"]

        print(f"[{idx}/{len(sample_payloads)}] Processing {case_id} ({cat} | {network} Code {rcode})...")

        if client:
            try:
                user_prompt = format_llm_prompt(payload)
                response_text = generate_with_groq(client, user_prompt)
            except Exception as err:
                print(f"  -> Groq API call failed for {case_id}: {err}. Using fallback generator.")
                response_text = generate_offline_fallback(payload)
        else:
            response_text = generate_offline_fallback(payload)

        # Write output markdown
        file_name = f"{case_id}_{network}_{rcode}.md"
        file_path = OUTPUT_DIR / file_name
        file_path.write_text(response_text, encoding="utf-8")
        generated_files.append(file_path)

        # Compile PDF version
        try:
            from system_b.pdf_compiler import compile_chargeback_pdf, PDF_OUTPUT_DIR
            pdf_path = PDF_OUTPUT_DIR / f"{case_id}_{network}_{rcode}.pdf"
            compile_chargeback_pdf(payload, output_filename=pdf_path)
            print(f"  -> Saved defense package to {file_path.relative_to(ROOT)} AND PDF to {pdf_path.relative_to(ROOT)}")
        except Exception as pdf_err:
            print(f"  -> Saved defense package to {file_path.relative_to(ROOT)} (PDF compilation warning: {pdf_err})")

    print("\n" + "=" * 60)
    print("SYSTEM B RESPONSE GENERATION COMPLETE")
    print("=" * 60)
    print(f"Total Defense Packages Generated: {len(generated_files)}")
    print(f"Saved to directory: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
