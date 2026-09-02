"""
END-TO-END SYSTEM TEST SCRIPT

Selects 5 random cases from the held-out test set, passes them through System A
(ML Verifier + EV Decision Engine), and if System A approves fighting (EV > 0),
passes the case and evidence payload to System B (LLM Auto-Responder with Groq API)
to generate the bank-ready representment package.

Outputs saved to: outputs/test_runs/
"""

import sys
from pathlib import Path
import random
import pandas as pd
from dotenv import load_dotenv

# Ensure root is in sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

load_dotenv()

from system_b.evidence_processor import load_and_score_cases, get_case_evidence_payload
from system_b.prompts import format_llm_prompt
from system_b.generate_responses import generate_with_groq, generate_offline_fallback
import os
import groq

TEST_OUTPUT_DIR = ROOT / "outputs" / "test_runs"
TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def run_full_flow_test(num_cases=5, seed=2026):
    random.seed(seed)
    print("=" * 70)
    print("RUNNING END-TO-END FLOW TEST: SYSTEM A (VERIFIER) -> SYSTEM B (AUTO-RESPONDER)")
    print("=" * 70)

    # 1. Run System A on entire dataset to get test split predictions
    df_scored = load_and_score_cases()
    test_set = df_scored[df_scored["dataset_split"] == "test"].copy()

    print(f"\nHeld-out Test Set Total: {len(test_set):,} cases")

    # 2. Select 5 random test cases
    random_case_ids = random.sample(test_set["case_id"].tolist(), num_cases)
    sample_df = test_set[test_set["case_id"].isin(random_case_ids)].copy()

    # 3. Setup Groq Client
    api_key = os.getenv("GROQ_API_KEY", "")
    client = None
    if api_key and not api_key.startswith("gsk_your"):
        try:
            client = groq.Groq(api_key=api_key)
            print("[Groq API] Connected successfully (model: qwen/qwen3.6-27b)\n")
        except Exception as e:
            print(f"[Groq API] Connection error: {e}. Fallback enabled.\n")

    test_summary_results = []

    for idx, (_, case_row) in enumerate(sample_df.iterrows(), 1):
        case_id = case_row["case_id"]
        category = case_row["normalized_category"]
        network = case_row["network"]
        rcode = case_row.get("reason_code", "N/A")
        rtitle = case_row.get("reason_code_title", "N/A")
        amount = case_row["dispute_amount_inr"]
        win_prob = case_row["predicted_win_prob"]
        ev = case_row["expected_value"]
        decision = case_row["model_decision_to_fight"]
        actual_won = case_row["merchant_representment_won"]

        decision_str = "FIGHT (EV > 0)" if decision == 1 else "CONCEDE (EV <= 0)"

        print("-" * 70)
        print(f"CASE {idx}/{num_cases}: {case_id}")
        print(f"  Network & Category: {network} | {category}")
        print(f"  Reason Code: Code {rcode} - {rtitle}")
        print(f"  Dispute Amount: Rs {amount:,.2f}")
        print(f"  System A Output: Win Prob = {win_prob:.1%} | Expected Value = Rs {ev:,.2f}")
        print(f"  System A Decision: {decision_str}")
        print(f"  Actual Ground Truth Outcome: {'WON' if actual_won == 1 else 'LOST'}")

        # Gather evidence payload
        payload = get_case_evidence_payload(case_id, cases_df=df_scored)
        clean_evidence_cnt = payload["clean_evidence_count"]
        filtered_cnt = payload["filtered_contradictory_count"]

        print(f"  Evidence Gathered: {clean_evidence_cnt} valid items ({filtered_cnt} contradictory items filtered out)")

        # System B Generation
        if decision == 1:
            print(f"  -> Routing to System B (Auto-Responder)...")
            user_prompt = format_llm_prompt(payload)

            if client:
                try:
                    response_text = generate_with_groq(client, user_prompt)
                    gen_mode = "Live Groq API (qwen/qwen3.6-27b)"
                except Exception as err:
                    response_text = generate_offline_fallback(payload)
                    gen_mode = f"Fallback Generator ({err})"
            else:
                response_text = generate_offline_fallback(payload)
                gen_mode = "Fallback Generator"

            # Save generated defense package
            out_file = TEST_OUTPUT_DIR / f"{case_id}_{network}_{rcode}.md"
            out_file.write_text(response_text, encoding="utf-8")
            print(f"  -> Saved defense package to {out_file.relative_to(ROOT)}")
            print(f"  -> Generation Mode: {gen_mode}")
        else:
            print(f"  -> System A decided CONCEDE. System B skipped (saved merchant Rs {case_row['false_positive_cost_inr']:,.2f} in fees).")
            out_file = None
            gen_mode = "Skipped (Conceded)"

        test_summary_results.append({
            "case_id": case_id,
            "category": category,
            "network": network,
            "reason_code": rcode,
            "amount": amount,
            "win_prob": win_prob,
            "ev": ev,
            "decision": decision_str,
            "actual_won": actual_won,
            "evidence_items": clean_evidence_cnt,
            "gen_mode": gen_mode,
            "output_file": str(out_file) if out_file else "None (Conceded)",
        })

    print("\n" + "=" * 70)
    print("END-TO-END TEST SUMMARY TABLE")
    print("=" * 70)
    res_df = pd.DataFrame(test_summary_results)
    print(res_df[["case_id", "network", "reason_code", "amount", "win_prob", "ev", "decision", "actual_won"]].to_string(index=False))

    return test_summary_results


if __name__ == "__main__":
    run_full_flow_test(num_cases=5, seed=2026)
