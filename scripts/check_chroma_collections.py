# scripts/check_chroma_collections.py
import os
from dotenv import load_dotenv
load_dotenv()

try:
    from langchain_openai import OpenAIEmbeddings
    from langchain_chroma import Chroma
    print("Using langchain_openai + langchain_chroma")
except Exception:
    try:
        from langchain_community.embeddings import OpenAIEmbeddings
        from langchain_community.vectorstores import Chroma
        print("Using langchain_community")
    except Exception:
        from langchain.embeddings.openai import OpenAIEmbeddings
        from langchain.vectorstores import Chroma
        print("Using legacy langchain")

import chromadb

# Check ChromaDB directly
client = chromadb.PersistentClient(path="chroma_persist")
collections = client.list_collections()

print(f"\nFound {len(collections)} collections in chroma_persist:")
for col in collections:
    print(f"  - {col.name}: {col.count()} documents")

# Try to query each coach collection
emb = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))

for coach in ["alex_hormozi", "dan_martell", "sam_ovens"]:
    print(f"\nTesting {coach}:")
    try:
        vect = Chroma(
            persist_directory="chroma_persist",
            collection_name=coach,
            embedding_function=emb
        )
        results = vect.similarity_search("business growth", k=1)
        print(f"  ✓ Successfully retrieved {len(results)} documents")
        if results:
            print(f"    Sample: {results[0].page_content[:100]}...")
    except Exception as e:
        print(f"  ✗ Error: {e}")
