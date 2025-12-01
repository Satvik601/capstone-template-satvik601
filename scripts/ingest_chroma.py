# scripts/ingest_chroma.py
import os
import json
import time
import inspect
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

OPENAI_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_KEY:
    raise SystemExit("Set OPENAI_API_KEY in your .env before running this script.")

# Try imports in order of modern -> community -> fallback
EmbeddingClass = None
ChromaClass = None

try:
    from langchain_openai import OpenAIEmbeddings
    from langchain_chroma import Chroma
    EmbeddingClass = OpenAIEmbeddings
    ChromaClass = Chroma
    print("Using langchain_openai.OpenAIEmbeddings and langchain_chroma.Chroma")
except Exception:
    try:
        from langchain_community.embeddings import OpenAIEmbeddings
        from langchain_community.vectorstores import Chroma
        EmbeddingClass = OpenAIEmbeddings
        ChromaClass = Chroma
        print("Using langchain_community OpenAIEmbeddings + Chroma")
    except Exception:
        try:
            from langchain.embeddings.openai import OpenAIEmbeddings
            from langchain.vectorstores import Chroma
            EmbeddingClass = OpenAIEmbeddings
            ChromaClass = Chroma
            print("Using legacy langchain OpenAIEmbeddings + Chroma")
        except Exception:
            raise SystemExit(
                "Could not import OpenAIEmbeddings/Chroma. "
                "Install one of: langchain-openai + langchain-chroma, or langchain_community, or update packages."
            )

# Settings
PROCESSED_ROOT = Path("data/processed")
PERSIST_DIR = "chroma_persist"
BATCH_SIZE = 128
SLEEP_BETWEEN_BATCHES = 1.0

def read_chunks(chunks_file: Path):
    texts = []
    metadatas = []
    with chunks_file.open("r", encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line)
            texts.append(obj.get("text", ""))
            metadatas.append({
                "source": obj.get("source"),
                "coach": obj.get("coach"),
                "chunk_id": obj.get("chunk_id"),
            })
    return texts, metadatas

def chunked_iter(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i+n]

def ingest_collection(coach_name: str, texts: list, metadatas: list, emb_instance):
    """
    Call ChromaClass.from_texts in a way that adapts to different versions'
    expected parameter names for the embedding object.
    """
    print(f"Ingesting {len(texts)} docs into collection '{coach_name}' (persist dir: {PERSIST_DIR})")

    # Inspect the signature of from_texts if present
    from_texts = getattr(ChromaClass, "from_texts", None)
    tried = []

    if callable(from_texts):
        sig = inspect.signature(from_texts)
        params = sig.parameters
        # choose embedding arg name
        embed_arg = None
        for candidate in ("embeddings", "embedding_function", "embedding"):
            if candidate in params:
                embed_arg = candidate
                break

        kwargs = {
            "texts": texts,
            "metadatas": metadatas,
            "collection_name": coach_name,
            "persist_directory": PERSIST_DIR
        }

        # If embed_arg found, supply embedding instance under that name
        if embed_arg:
            kwargs[embed_arg] = emb_instance
            tried.append(f"from_texts with arg '{embed_arg}'")
            try:
                ChromaClass.from_texts(**kwargs)
                print(f"Finished ingesting collection '{coach_name}' using from_texts({embed_arg}=...)")
                return
            except TypeError as e:
                print(f"from_texts TypeError with '{embed_arg}':", e)
            except Exception as e:
                print(f"from_texts error with '{embed_arg}':", e)

        # Try without embedding param (some versions infer embeddings differently)
        tried.append("from_texts without explicit embedding arg")
        try:
            # remove embedding if present
            ChromaClass.from_texts(texts=texts, metadatas=metadatas, collection_name=coach_name, persist_directory=PERSIST_DIR)
            print(f"Finished ingesting collection '{coach_name}' using from_texts() without explicit embedding param")
            return
        except Exception as e:
            print("from_texts fallback failed:", e)

    # As a last resort, try to construct the ChromaClass then add documents through its instance API
    print("Falling back to instance-based ingestion (construct Chroma then add documents). Tried:", tried)
    try:
        # Find constructor params and try safe init
        init_sig = inspect.signature(ChromaClass)
        init_params = init_sig.parameters
        init_kwargs = {}
        # common constructor args: persist_directory, collection_name, embedding_function
        if "persist_directory" in init_params:
            init_kwargs["persist_directory"] = PERSIST_DIR
        if "collection_name" in init_params:
            init_kwargs["collection_name"] = coach_name
        if "embedding_function" in init_params:
            init_kwargs["embedding_function"] = emb_instance
        elif "embeddings" in init_params:
            init_kwargs["embeddings"] = emb_instance
        # create instance
        chroma_inst = ChromaClass(**init_kwargs)
        # Try instance.add_texts / add_documents / upsert - try common methods
        if hasattr(chroma_inst, "add_texts"):
            chroma_inst.add_texts(texts=texts, metadatas=metadatas)
            print(f"Used chroma_inst.add_texts for '{coach_name}'")
            return
        elif hasattr(chroma_inst, "add_documents"):
            chroma_inst.add_documents(documents=texts, metadatas=metadatas)
            print(f"Used chroma_inst.add_documents for '{coach_name}'")
            return
        elif hasattr(chroma_inst, "upsert"):
            chroma_inst.upsert(documents=texts, metadatas=metadatas)
            print(f"Used chroma_inst.upsert for '{coach_name}'")
            return
        else:
            raise RuntimeError("No known instance ingestion method found on ChromaClass instance.")
    except Exception as e:
        print("Final fallback ingestion attempt failed:", e)
        raise

def main():
    emb = EmbeddingClass(openai_api_key=OPENAI_KEY)
    if not PROCESSED_ROOT.exists():
        raise SystemExit(f"No processed files found at {PROCESSED_ROOT}. Run preprocessing first.")

    for coach_dir in sorted(PROCESSED_ROOT.iterdir()):
        if not coach_dir.is_dir():
            continue
        chunks_file = coach_dir / "chunks.jsonl"
        if not chunks_file.exists():
            print(f"No chunks.jsonl for coach '{coach_dir.name}', skipping.")
            continue

        texts, metadatas = read_chunks(chunks_file)
        if not texts:
            print(f"No text chunks found in {chunks_file}, skipping.")
            continue

        # ingest in batches
        for i, (tb, mb) in enumerate(zip(chunked_iter(texts, BATCH_SIZE), chunked_iter(metadatas, BATCH_SIZE)), start=1):
            print(f"[{coach_dir.name}] ingesting batch {i} (size={len(tb)})")
            ingest_collection(coach_dir.name, tb, mb, emb)
            time.sleep(SLEEP_BETWEEN_BATCHES)

    print("All ingestions complete. Chroma persisted at:", PERSIST_DIR)

if __name__ == "__main__":
    main()
