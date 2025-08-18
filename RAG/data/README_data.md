# data/ folder

This folder contains test fixtures for **Vet‑Chain RAG** while keeping the blockchain goal: verifiable, privacy‑preserving retrieval.

Files:
- `petrecords.jsonl` — 8 NeonDB‑style real records (fill `onChainTxHash`/`onChainCid` with your real values to enable chain verification).
- `synth.jsonl` — 50 synthetic cases to improve retrieval signal.
- `all.jsonl` — concatenation of the above (use this when building your FAISS index).

Usage:
1) Build index (from your project root, using your `scripts/build_index.py`):  
   ```bash
   python scripts/build_index.py  # ensure IN_FILE = "data/all.jsonl"
   ```

2) (Optional) Verify blockchain receipts (replace with your real tx hashes):  
   ```bash
   python scripts/verify_receipts.py data/petrecords.jsonl
   ```

3) Run RAG API and query:  
   ```bash
   uvicorn api.server:app --reload
   curl -X POST localhost:8000/query -H 'content-type: application/json'      -d '{"symptoms":"dog dry cough and nasal discharge","top_k":5}'
   ```

Notes:
- Keep PHI out of descriptions. If you later anchor to PureChain, store only content hashes and CIDs on‑chain.
- Timestamps are ISO8601 UTC with trailing 'Z'.
