# quick check snippet
import tiktoken, json
enc = tiktoken.encoding_for_model("gpt-3.5-turbo")
from pathlib import Path
for coach in ["alex_hormozi","dan_martell","sam_ovens"]:
    p = Path("data/processed")/coach/"chunks.jsonl"
    lens=[]
    if p.exists():
        for i,line in enumerate(p.open(encoding="utf-8")):
            if i>=200: break
            obj=json.loads(line)
            lens.append(len(enc.encode(obj["text"])))
    print(coach,"avg tokens:", sum(lens)/len(lens) if lens else 0)
