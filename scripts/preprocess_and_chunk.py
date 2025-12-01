# scripts/preprocess_and_chunk.py
import re, json
from pathlib import Path
import tiktoken

RAW_ROOT = Path("data/raw")
PROCESSED_ROOT = Path("data/processed")
MODEL_FOR_TOKENIZER = "gpt-3.5-turbo"

def clean_text(s: str) -> str:
    s = re.sub(r"\[?\d{1,2}:\d{2}(?::\d{2})?\]?", " ", s)
    s = re.sub(r"\s+\n\s+", "\n", s)
    s = re.sub(r"\n{2,}", "\n\n", s)
    return s.strip()

def chunk_text_tokens(text: str, max_tokens: int=450, overlap_tokens: int=80):
    enc = tiktoken.encoding_for_model(MODEL_FOR_TOKENIZER) if hasattr(tiktoken, "encoding_for_model") else tiktoken.get_encoding("cl100k_base")
    toks = enc.encode(text)
    chunks = []
    i = 0
    L = len(toks)
    while i < L:
        j = min(i + max_tokens, L)
        chunk = enc.decode(toks[i:j])
        chunks.append(chunk.strip())
        i += max_tokens - overlap_tokens
    return chunks

def process_all():
    PROCESSED_ROOT.mkdir(parents=True, exist_ok=True)
    for coach_dir in RAW_ROOT.iterdir():
        if not coach_dir.is_dir():
            continue
        out_dir = PROCESSED_ROOT / coach_dir.name
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / "chunks.jsonl"
        print("Processing coach:", coach_dir.name)
        with out_file.open("w", encoding="utf-8") as fout:
            for txt in sorted(coach_dir.glob("*.txt")):
                raw = txt.read_text(encoding="utf-8")
                cleaned = clean_text(raw)
                chunks = chunk_text_tokens(cleaned)
                for idx, c in enumerate(chunks):
                    doc = {"text": c, "source": str(txt.name), "coach": coach_dir.name, "chunk_id": idx}
                    fout.write(json.dumps(doc, ensure_ascii=False) + "\n")
        print("Wrote chunks to:", out_file)

if __name__ == "__main__":
    process_all()
