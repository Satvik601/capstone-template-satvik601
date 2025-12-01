# scripts/test_retrieval.py (updated imports)
from dotenv import load_dotenv
import os
load_dotenv()

# Use langchain-openai + langchain-chroma (recommended)
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

emb = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))
vect = Chroma(persist_directory="chroma_persist", collection_name="alex_hormozi", embedding_function=emb)
docs = vect.similarity_search("offer creation pricing", k=2)
for d in docs:
    print("----")
    print(d.page_content[:800])
