import json, os, pathlib, numpy as np
from sentence_transformers import SentenceTransformer
import faiss

IN_FILE = "data/all.jsonl"        # or "data/petrecords.jsonl" if you want only the 8 real
IDX_FILE = "data/index.faiss"
META_FILE = "data/meta.json"

def canonical_text(row: dict) -> str:
    # Minimal, PHI-free canonicalization
    parts = [
        f"Type: {row.get('type','')}",
        f"Title: {row.get('title','')}",
        f"Desc: {row.get('description','')}",
        f"IssuedBy: {row.get('issuedBy','')}",
        f"Date: {row.get('date','')}",
    ]
    return "\n".join(parts)

def main():
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    texts, meta = [], []
    with open(IN_FILE) as f:
        for line in f:
            r = json.loads(line)
            texts.append(canonical_text(r))
            meta.append({
                "id": r["id"],
                "title": r.get("title"),
                "type": r.get("type"),
                "onChainTxHash": r.get("onChainTxHash"),
                "onChainCid": r.get("onChainCid"),
            })

    embs = model.encode(texts, convert_to_numpy=True, show_progress_bar=True)
    dim = embs.shape[1]
    index = faiss.IndexFlatIP(dim)        # cosine via normalized IP
    faiss.normalize_L2(embs)
    index.add(embs.astype("float32"))

    pathlib.Path("data").mkdir(exist_ok=True)
    faiss.write_index(index, IDX_FILE)
    with open(META_FILE, "w") as f:
        json.dump({"meta": meta}, f, ensure_ascii=False)
    print(f"OK: {len(meta)} vectors -> {IDX_FILE}")

if __name__ == "__main__":
    main()
