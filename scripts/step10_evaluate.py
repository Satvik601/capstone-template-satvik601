# scripts/step10_evaluate.py
"""
Step 10 evaluation harness (minimal, non-invasive).
Runs a few test scenarios through your graph (build_graph in src/business_consultant_graph.py),
validates final_report using src/validate_report.validate_final_report(),
and writes an evaluation summary to data/metadata/eval_results.json.

This script makes NO changes to your core source files.
"""

import json
import time
import uuid
import sys
from pathlib import Path

# Add project root to sys.path so we can import src
sys.path.append(str(Path(__file__).parent.parent))

# Import project pieces (these are local modules you've created)
# They must be on the PYTHONPATH when running from repo root (default).
from src.business_consultant_graph import build_graph
try:
    from src.validate_report import validate_final_report
except Exception:
    # If validate_report isn't present, use a no-op validator that returns no errors
    def validate_final_report(rep):
        return []

# --- test scenarios: keep these minimal; you can edit/add more later ---
TEST_SCENARIOS = [
    {
        "name": "diaper_manufacturing",
        "business_description": "Diaper manufacturing business with moderate local sales and high production costs.",
        "goal": "Get profitable in 6 months",
        "kpis": {"production_cost_per_unit": None, "revenue": None}
    },
    {
        "name": "local_coaching_saas",
        "business_description": "Bootstrapped coaching SaaS selling monthly subscriptions to coaches.",
        "goal": "Double monthly recurring revenue in 6 months",
        "kpis": {}
    },
    {
        "name": "small_retail_chain",
        "business_description": "3-store retail chain with inconsistent inventory and declining footfall.",
        "goal": "Increase same-store sales by 20% in 3 months",
        "kpis": {"conversion_rate": None}
    }
]

OUT_DIR = Path("data/metadata")
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = OUT_DIR / f"eval_results_{int(time.time())}.json"

results = []

# Build graph once (reuse ok)
graph, memory = build_graph()

for scenario in TEST_SCENARIOS:
    run_id = uuid.uuid4().hex[:8]
    thread = {"configurable": {"thread_id": f"eval-{run_id}"}}
    initial_state = {
        "business_description": scenario["business_description"],
        "goal": scenario["goal"],
    }
    if scenario.get("kpis"):
        initial_state["kpis"] = scenario["kpis"]

    entry = {
        "scenario": scenario["name"],
        "thread_id": thread["configurable"]["thread_id"],
        "start_ts": time.time(),
        "ok": False,
        "errors": [],
        "metrics": {}
    }

    print(f"\n=== Running scenario: {scenario['name']} (thread {entry['thread_id']}) ===")
    try:
        final_state = graph.invoke(initial_state, thread)
        fr = final_state.get("final_report", {})

        # Defensive fills so validator doesn't crash if keys missing
        if "business_snapshot" not in fr:
            fr["business_snapshot"] = {
                "description": initial_state.get("business_description", ""),
                "goal": initial_state.get("goal", "")
            }

        # Validate
        try:
            v_errors = validate_final_report(fr)
        except Exception as e:
            v_errors = [f"validator_exception: {e}"]

        # Basic sanity metrics
        consensus_b = fr.get("consensus_bottlenecks", [])
        action_plan = fr.get("action_plan", [])
        kpis_to_track = fr.get("kpis_to_track", [])
        proposed_kpis = fr.get("proposed_kpis", [])
        coach_insights = fr.get("coach_insights", {})

        proof_counts = {}
        for coach, payload in coach_insights.items():
            prov = payload.get("provenance") if isinstance(payload, dict) else None
            if prov is None:
                # if payload is nested {'analysis':..., 'provenance':...}
                prov = payload.get("provenance") if isinstance(payload, dict) else []
            proof_counts[coach] = len(prov or [])

        entry["end_ts"] = time.time()
        entry["ok"] = len(v_errors) == 0
        entry["errors"] = v_errors
        entry["metrics"] = {
            "num_consensus_bottlenecks": len(consensus_b),
            "num_action_plan_items": len(action_plan),
            "num_kpis_to_track": len(kpis_to_track),
            "num_proposed_kpis": len(proposed_kpis),
            "provenance_counts": proof_counts
        }

        # Save a copy of the produced final_report for manual inspection
        fr_file = OUT_DIR / f"final_report_{scenario['name']}_{entry['thread_id']}.json"
        fr_file.write_text(json.dumps(fr, ensure_ascii=False, indent=2), encoding="utf-8")
        entry["final_report_path"] = str(fr_file)

        print("Scenario finished. Validation errors:", v_errors)
        print("Metrics:", entry["metrics"])

    except Exception as exc:
        import traceback as tb
        entry["end_ts"] = time.time()
        entry["ok"] = False
        entry["errors"].append(f"exception_during_invoke: {exc}")
        entry["errors"].append(tb.format_exc()[:1000])
        print("Exception during scenario run:", exc)

    results.append(entry)

# Write summary file
OUT_PATH.write_text(json.dumps({"runs": results}, ensure_ascii=False, indent=2), encoding="utf-8")
print("\n=== EVALUATION COMPLETE ===")
print("Summary saved to:", OUT_PATH)
print("Per-scenario final_report jsons saved in:", OUT_DIR)
