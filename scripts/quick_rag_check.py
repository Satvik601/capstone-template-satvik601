# scripts/quick_rag_check.py
from dotenv import load_dotenv
import os, json
load_dotenv()
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

def check(coach, q):
    emb = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))
    vect = Chroma(persist_directory="chroma_persist", collection_name=coach, embedding_function=emb)
    docs = vect.similarity_search(q, k=3)
    print("=== coach:", coach, "query:", q, "->", len(docs), "docs ===")
    for i,d in enumerate(docs,1):
        print(f"--- doc {i} ---")
        print(d.page_content[:700].replace("\n", " ")[:700])
    print()

if __name__=="__main__":
    queries = {
      "alex_hormozi": "how to structure an irresistible offer",
      "dan_martell": "how to delegate and scale operations",
      "sam_ovens": "how to position a consulting offer"
    }
    for c,q in queries.items():
        check(c,q)
