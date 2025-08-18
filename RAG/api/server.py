from fastapi import FastAPI
from pydantic import BaseModel
from api.rag_index import RAGIndex
from api.rag_generate import generate

app = FastAPI()
idx = RAGIndex()

class QueryIn(BaseModel):
    symptoms: str
    top_k: int = 5

@app.post("/query")
def query(q: QueryIn):
    hits = idx.search(q.symptoms, k=q.top_k)
    ans = generate(q.symptoms, hits)
    return {"cases": hits, "answer": ans}

@app.get("/health")
def health():
    try:
        import requests, os
        host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
        r = requests.get(f"{host}/api/version", timeout=3)
        llm_ok = r.ok
    except Exception:
        llm_ok = False
    # check index presence
    try:
        n = len(idx.meta)
        index_ok = True
    except Exception:
        n = 0
        index_ok = False
    return {"index_ok": index_ok, "docs": n, "ollama_ok": llm_ok}