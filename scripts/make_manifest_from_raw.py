# scripts/make_manifest_from_raw.py
import json, os
from pathlib import Path
from datetime import datetime

RAW = Path("data/raw")
MANIFEST = Path("data/metadata/manifest.json")
MANIFEST.parent.mkdir(parents=True, exist_ok=True)
manifest = []

for coach_dir in RAW.iterdir():
    if not coach_dir.is_dir(): continue
    for f in sorted(coach_dir.glob("*.txt")):
        manifest.append({
            "id": f"{coach_dir.name}__{f.stem}",
            "coach": coach_dir.name,
            "type": "raw_text",
            "path": str(f),
            "collected_at": datetime.utcnow().isoformat() + "Z"
        })

MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
print("Wrote", MANIFEST)
