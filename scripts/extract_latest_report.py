# scripts/extract_latest_report.py
import json
from pathlib import Path

runs_file = Path("data/metadata/runs.jsonl")
if not runs_file.exists():
    print("No runs.jsonl found")
    exit(1)

lines = runs_file.read_text(encoding="utf-8").strip().split("\n")
latest = None
for line in reversed(lines):
    if line.strip():
        latest = json.loads(line)
        break

if not latest:
    print("No valid runs found")
    exit(1)

output_path = Path("data/metadata/latest_final_report.json")
output_path.write_text(json.dumps(latest["final_report"], indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Extracted latest report to: {output_path}")
print(f"Thread ID: {latest['thread_id']}")
