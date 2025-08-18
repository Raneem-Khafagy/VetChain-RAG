===============================
RAG 
===============================

Purpose
-------
This module provides the AI (RAG) side of Vet-Chain: it retrieves similar veterinary cases and (optionally) uses a local open-source LLM to generate grounded, citation-style differentials. It is designed to display on-chain provenance fields (tx hash, CID) that you’ve merged from the blockchain track.

Prerequisites
-------------
• Python 3.11 (or Conda env)
• pip install: fastapi uvicorn pydantic "sentence-transformers<3.0" faiss-cpu numpy orjson requests
• (Optional LLM) Ollama running locally
    - macOS: brew install --cask ollama
    - Start: open -a Ollama  (or: ollama serve &)
    - Pull a small model: ollama pull phi3:mini  (or: ollama pull llama3:instruct)
• Data files present under RAG/data/:
    - petrecords.jsonl (from chain/data/petrecords.merged.jsonl)
    - synth.jsonl (provided in repo)
    - all.jsonl (cat petrecords.jsonl + synth.jsonl)

Environment Flags (optional but useful)
---------------------------------------
• NO_LLM=1                 -> skip the model entirely; always return a structured fallback
• OLLAMA_MODEL=phi3:mini   -> choose a fast local model (default in rag_generate.py)
• OLLAMA_HOST=http://127.0.0.1:11434
• OLLAMA_TIMEOUT=15        -> hard timeout in seconds to prevent hanging calls
• IN_FILE=path             -> override scripts/build_index.py input file

Prepare Data From Blockchain Track
----------------------------------
(From project root)
1) cd chain
2) python scripts/merge_anchors.py
   -> writes chain/data/petrecords.merged.jsonl (fills onChainTxHash/CID by id)
3) cp chain/data/petrecords.merged.jsonl RAG/data/petrecords.jsonl
4) (optional) cat RAG/data/petrecords.jsonl RAG/data/synth.jsonl > RAG/data/all.jsonl

Build the Vector Index
----------------------
cd RAG
# Use all.jsonl (real + synthetic)
python scripts/build_index.py
# OR only real records:
IN_FILE=data/petrecords.jsonl python scripts/build_index.py

Expected output:
  OK: <N> vectors -> data/index.faiss
Artifacts:
  data/index.faiss, data/meta.json

Run the API Server
------------------
# Recommend small model or skip LLM for low-latency tests
export OLLAMA_MODEL=phi3:mini
# (Optional) export NO_LLM=1

uvicorn api.server:app --reload
# Server: http://127.0.0.1:8000

Query the System
----------------
In a separate terminal:
curl -X POST http://127.0.0.1:8000/query \
  -H "Content-Type: application/json" \
  -d '{"symptoms":"dog dry cough and nasal discharge","top_k":5}'

Response:
{
  "cases": [ { "id": "...", "title": "...", "onChainTxHash": "...", "onChainCid": "..." }, ... ],
  "answer": {
    ... either JSON with differentials + citations[] (case_ids) or {"raw": "..."} ...
    ... or a fallback {"error":"llm_unavailable", "differentials":[], "citations":[...]} if NO_LLM/timeout ...
  }
}

(Recommended) Health Check Endpoint
-----------------------------------
Add this snippet to api/server.py to quickly see status:

@app.get("/health")
def health():
    import requests, os
    try:
        host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
        r = requests.get(f"{host}/api/version", timeout=2)
        llm_ok = r.ok
    except Exception:
        llm_ok = False
    try:
        n = len(idx.meta); index_ok = True
    except Exception:
        n = 0; index_ok = False
    return {"index_ok": index_ok, "docs": n, "ollama_ok": llm_ok}

Then:
curl http://127.0.0.1:8000/health
-> {"index_ok":true,"docs":<N>,"ollama_ok":true/false}

Troubleshooting
---------------
• /query hangs or 500:
  - Ensure Ollama is running: curl http://127.0.0.1:11434/api/version
  - Use a small model: export OLLAMA_MODEL=phi3:mini
  - Force fallback: export NO_LLM=1
• Retrieval returns few/irrelevant hits:
  - Rebuild index after updating data files
  - Use all.jsonl to increase corpus size
  - Check canonical_text() inside scripts/build_index.py
• Chain fields missing on hits:
  - Confirm you copied chain/data/petrecords.merged.jsonl to RAG/data/petrecords.jsonl
  - Only real records (not synthetic) contain chain fields

Performance Tips
----------------
• Keep top_k small (3–5) to minimize prompt size and latency
• Prefer lightweight models (phi3:mini / llama3:instruct) during dev
• Use cosine (normalized inner product) as implemented for fast search
• Consider enabling NO_LLM=1 in CI to test only retrieval

Makefile (Optional)
-------------------
Create RAG/Makefile:

index:
	python scripts/build_index.py

serve:
	uvicorn api.server:app --reload

query:
	curl -X POST http://127.0.0.1:8000/query \
	  -H "Content-Type: application/json" \
	  -d '{"symptoms":"dog dry cough and nasal discharge","top_k":5}'

real-index:
	IN_FILE=data/petrecords.jsonl python scripts/build_index.py

Then run:
  make -C RAG index
  make -C RAG serve
  make -C RAG query

Backlog / Upcoming Tasks
------------------------
1) Hybrid Retrieval (BM25 + Dense)
   - Implement BM25 scorer in rag_retrieve.py (rank-bm25 locally or OpenSearch).
   - Union top-K from BM25 & dense; dedupe; rerank with cross-encoder.
   - Add species/breed/region filters and determinism tests.

2) Reranker (Cross-Encoder)
   - Use cross-encoder/ms-marco-MiniLM-L-6-v2 to rerank top 50 → top 5.
   - Cache scores; measure p95 latency & accuracy gains.

3) Chain-Aware Enrichment
   - Inline live verification per hit (chainVerified true/false).
   - Surface tx receipt URL and CID link for the UI “Verified ✓” badge.

4) JSON Safety & Guardrails
   - Validate LLM output with Pydantic schema; fail closed to “insufficient evidence”.
   - Add prompt-injection and PHI-leakage checks before presenting output.

5) Evaluation Harness
   - Offline set (N≈150) with expected nearest cases & acceptable differentials.
   - Metrics: Recall@5, nDCG@10, faithfulness (citation-backed), JSON validity.
   - Add CLI: `python scripts/eval.py --queries queries.jsonl`.

6) Caching & Throughput
   - Embedding memoization; FAISS in-memory preload.
   - Response cache keyed by (query, top_ids, model_version).
   - Batch queries for throughput testing.

7) Observability
   - Add request/latency logs, error tags, retrieval depth, #tokens, LLM timing.
   - Optional: /metrics (Prometheus) or OpenTelemetry traces.

8) Packaging & CI
   - Dockerfile + docker-compose for local complete bring-up.
   - GitHub Actions / CI to run index build + NO_LLM queries for smoke tests.

9) Data Governance
   - Field-level de-identification (verify no PHI in descriptions).
   - Redaction pipeline for any free-text fields before indexing.

10) Product UX
   - Simple web UI: symptoms input, filter chips (species/region), results w/ “Verified ✓”.
   - QR/receipt links for each verified case (to pretty HTML receipt page).
