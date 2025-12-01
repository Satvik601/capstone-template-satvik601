# scripts/spot_check_chunks.py
import random, json
from pathlib import Path
for coach in ["alex_hormozi","dan_martell","sam_ovens"]:
    f = Path("data/processed")/coach/"chunks.jsonl"
    if not f.exists(): 
        print("No chunks for", coach); continue
    lines = f.read_text(encoding="utf-8").splitlines()
    print("===", coach, "chunks count:", len(lines))
    for i in random.sample(range(len(lines)), min(5, len(lines))):
        print("\n--- chunk", i, "---")
        print(json.loads(lines[i])["text"][:800].replace("\n"," "))
    print()
