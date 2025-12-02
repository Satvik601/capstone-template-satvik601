# src/validate_report.py
from typing import Dict, Any, List

REQUIRED_TOP_KEYS = [
    "business_snapshot",
    "coach_insights",
    "consensus_bottlenecks",
    "action_plan",
    "kpis_to_track",
    "final_summary"
]

def validate_final_report(rep: Dict[str, Any]) -> List[str]:
    errs = []
    if not isinstance(rep, dict):
        return ["final_report must be a dict"]
    for k in REQUIRED_TOP_KEYS:
        if k not in rep:
            errs.append(f"missing top-level key: {k}")
    # business_snapshot checks
    bs = rep.get("business_snapshot", {})
    if not isinstance(bs, dict):
        errs.append("business_snapshot must be an object")
    else:
        for sub in ("description", "goal"):
            if sub not in bs:
                errs.append(f"business_snapshot missing {sub}")
    # coach_insights sanity
    ci = rep.get("coach_insights", {})
    if not isinstance(ci, dict):
        errs.append("coach_insights must be an object")
    # consensus_bottlenecks type
    cb = rep.get("consensus_bottlenecks", [])
    if not isinstance(cb, list):
        errs.append("consensus_bottlenecks must be a list")
    # action_plan type
    if not isinstance(rep.get("action_plan", []), list):
        errs.append("action_plan must be a list")
    # kpis_to_track type
    if not isinstance(rep.get("kpis_to_track", []), list):
        errs.append("kpis_to_track must be a list")
    return errs
