# scripts/dedupe_chunks.py
import json
from pathlib import Path
from collections import defaultdict

PROCESSED_ROOT = Path("data/processed")
OUT_SUFFIX = "_dedup.jsonl"

def dedupe_coach(coach):
    f = PROCESSED_ROOT / coach / "chunks.jsonl"
    if not f.exists():
        print("No chunks for", coach); return
    seen = set()
    out = PROCESSED_ROOT / coach / ("chunks"+OUT_SUFFIX)
    with f.open("r", encoding="utf-8") as fin, out.open("w", encoding="utf-8") as fout:
        for line in fin:
            obj = json.loads(line)
            key = obj["text"].strip()[:300]  # first 300 chars
            if key in seen:
                continue
            seen.add(key)
            fout.write(json.dumps(obj, ensure_ascii=False) + "\n")
    print("Wrote deduped:", out)

if __name__ == "__main__":
    for d in PROCESSED_ROOT.iterdir():
        if d.is_dir():
            dedupe_coach(d.name)
