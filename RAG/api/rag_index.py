import json, faiss, numpy as np
from sentence_transformers import SentenceTransformer

class RAGIndex:
    def __init__(self, idx_path="data/index.faiss", meta_path="data/meta.json"):
        self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        self.index = faiss.read_index(idx_path)
        with open(meta_path) as f:
            self.meta = json.load(f)["meta"]

    def search(self, query: str, k: int = 5):
        q = self.model.encode([query], convert_to_numpy=True)
        faiss.normalize_L2(q)
        D, I = self.index.search(q.astype("float32"), k)
        out = []
        for i in I[0]:
            if i < 0: continue
            out.append(self.meta[i])
        return out
