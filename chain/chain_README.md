Here’s a clean **README.txt** you can paste into `vetchain/chain/README.txt`.
It documents what this module does, how to run it, why the data migration matters, and what’s next.

---

# VetChain • Chain Verification Module (read-only)

This module verifies that your veterinary records are **anchored on PureChain** and that their off-chain JSON on **IPFS** hasn’t changed. It’s read-only: we **do not write** to the chain here.

What you get:

* ✅ Transaction status for each `onChainTxHash`
* 🧾 Printable **HTML receipts** and **JSON receipts** per transaction
* 🔒 Integrity check of each `onChainCid` (IPFS) via **sha256** (and optional keccak256)
* 📊 A single merged report for audits
* 📦 A snapshot of the latest block (groundwork for offline verification)
* 🔗 (Optional) Flags (`verified_onchain`, `receipt_html`, `ipfs_match`) overlayed into your RAG API results

---

## 1) Repository Layout

```
vetchain/
  chain/
    data/
      petrecords.jsonl          # one JSON object per line (see format below)
      anchors.json              # (optional) batch anchors to merge in
    out/
      receipts/                 # <tx>.html + <tx>.json (pretty receipt + decoded events)
      reports/                  # tx_verification.json, ipfs_verification.json, verification_merged.json
      snapshot/                 # latest.json (latest block snapshot)
    scripts/
      verify_receipts.py        # check /tx/{hash}, save HTML & JSON receipts
      verify_ipfs_hash.py       # stream hash CIDs (sha256, keccak256*)
      verify_all.py             # join tx + ipfs reports → verification_merged.json
      merge_anchors.py          # (optional) merge anchors.json into petrecords.jsonl by id
      add_expected_hashes.py    # (optional) populate sha256_expected from ipfs report
    schemas/
      petrecord.schema.json     # (optional) sanity schema for JSONL lines
    Makefile
    .env.example
```

---

## 2) Data Model

### 2.1 Minimal data per line (JSONL)

Each line in `data/petrecords.jsonl` is a single record:

```json
{"id":"<record_id>","onChainTxHash":"0x...","onChainCid":"Qm...","sha256_expected":null}
```

* `id` (string): your NeonDB / app record id
* `onChainTxHash` (string, 0x + 64 hex): PureChain transaction hash
* `onChainCid` (string): IPFS CID pointing to canonical JSON
* `sha256_expected` (string, optional): expected sha256 of the IPFS JSON (enables exact MATCH checks)

> Tip: If you already have a list of anchors, drop them into `data/anchors.json` and run `scripts/merge_anchors.py` to enrich existing lines without losing other fields.

### 2.2 Canonical IPFS JSON (off-chain)

Your canonical, PHI-free JSON is stored in IPFS. We verify its blob hash on demand; the chain only carries a short anchor (tx hash, CID, content hash).

---

## 3) Setup

```bash
cd vetchain/chain
cp .env.example .env
# (optional) python -m venv .venv && source .venv/bin/activate

pip install requests pysha3
```

`.env.example`:

```
PURECHAIN_API=https://nsllab-kit.onrender.com/purechain/api/v1
IPFS_GATEWAYS=https://ipfs.io/ipfs,https://cloudflare-ipfs.com/ipfs
TIMEOUT_SECS=20
CONCURRENCY=8
```

---

## 4) How to Run

### 4.1 Verify transactions + save receipts

```bash
python scripts/verify_receipts.py data/petrecords.jsonl
```

**Expect:** per-record status (`OK` / `NOT CONFIRMED` / `NO TX`) and
`out/receipts/<tx>.html` + `out/receipts/<tx>.json` saved.

### 4.2 Verify IPFS content hashes

```bash
python scripts/verify_ipfs_hash.py data/petrecords.jsonl
```

**Expect:** `sha256=<64-hex>` per CID and `out/reports/ipfs_verification.json`.

> If a record has `sha256_expected`, output adds `MATCH` when the blob equals your expected hash.

### 4.3 Merge into a single audit file

```bash
python scripts/verify_all.py
```

**Expect:** `out/reports/verification_merged.json`.

### 4.4 Snapshot latest block (offline groundwork)

```bash
python scripts/snapshot_cache.py
```

**Expect:** `out/snapshot/latest.json`.

### 4.5 One-command flow

```bash
make verify-all   # runs tx + ipfs + merge
make snapshot     # caches latest block
```

---

## 5) Adding Expected Hashes (Recommended)

**Why:** Without expected values, you only know the current IPFS content; with `sha256_expected`, you can assert **exact** integrity (`MATCH: true/false`).

Two options:

**A) Manual:** copy the computed sha256 from `out/reports/ipfs_verification.json` into the matching line of `data/petrecords.jsonl` as `sha256_expected`, then re-run 4.2.

**B) Scripted:** use `scripts/add_expected_hashes.py` to copy known sha256s from the report into your data file:

```bash
python scripts/add_expected_hashes.py
mv data/petrecords.with_expected.jsonl data/petrecords.jsonl
python scripts/verify_ipfs_hash.py data/petrecords.jsonl
```

---

## 6) Wiring Verification Into the RAG API (Quick Glue)

Add `api/verify_overlay.py` in your API project to read the latest reports and attach provenance:

* `verified_onchain`: `true/false` from tx report
* `receipt_html` / `receipt_json`: local paths to the saved receipts
* `ipfs_sha256`, `ipfs_match`: from IPFS report

Then, in your `/query` handler (after retrieval), call `overlay_verification(hits)` before returning. The UI can render a **Verified ✓** badge and link to the printable receipt.

> If your API runs from repo root, set `export CHAIN_REPORT_DIR=chain/out/reports`.

---

## 7) Why a “Migrate” Step Exists (and matters)

You’ll often start with records living in a database (e.g., NeonDB). The **migrate** step converts those raw records into:

1. **Canonical, PHI-free JSON** (stable ordering & formatting)
2. **IPFS upload** of that JSON (returns `onChainCid`)
3. **On-chain anchor** transaction (returns `onChainTxHash`, stores content hash)

Benefits:

* **Integrity**: anyone can prove the record wasn’t tampered with (hash & receipt)
* **Privacy by design**: only minimal anchors sit on-chain; full text stays off-chain
* **Portability**: the same canonical JSON is what your RAG uses for retrieval context
* **Auditability**: receipts + hashes let clinics and auditors independently verify facts
* **Future automation**: a single “migrate” pipeline can move historic and new records seamlessly

> In this repo we **verify** anchors; the actual migration pipeline (creating IPFS JSON + posting anchors) can be added later as a separate `scripts/migrate_to_purechain.py`.

---

## 8) Upcoming Tasks (Backlog)

* **\[Expected Hashes]** Fill or auto-fill `sha256_expected` for all records so IPFS checks show `MATCH`.
* **\[RAG Integration]** Add `verify_overlay` to the API so `/query` returns provenance fields.
* **\[Makefile polish]** Keep `verify-all` and `snapshot` as your standard CI steps.
* **\[CI/Tests]** Add a tiny `pytest` pack:

  * Validate `petrecords.jsonl` against `schemas/petrecord.schema.json`
  * Ensure `<tx>.html` and `<tx>.json` exist for `tx_ok: true`
  * Check hash formats (length/charset) and `MATCH` logic
* **\[Migration Pipeline]** Implement `migrate_to_purechain.py`:

  * Export canonical JSON from DB (deterministic field order)
  * Compute sha256/keccak256 locally
  * Upload to IPFS → write CID back
  * (Optional) Submit anchor TX → write `onChainTxHash` back
  * Append/merge into `petrecords.jsonl`
* **\[Offline Verify]** Extend `snapshot_cache.py` to store a `{tx_hash -> status}` map from the last online run; your clinic wallet can verify QR payloads **without internet** using that snapshot.
* **\[UX]** Add “View Receipt” and “Verified ✓” badges in the clinician UI; hover shows block, confirmations, and CID.

---

## 9) Troubleshooting

* **“NO TX” in output**: the record lacks `onChainTxHash`. Add it (or merge via `anchors.json` + `merge_anchors.py`).
* **Receipt not saved**: confirm API URL in `.env`, network connectivity, and tx hash format (`0x` + 64 hex).
* **IPFS timeouts**: we try multiple gateways; re-run or add more gateways to `IPFS_GATEWAYS`.
* **No `MATCH` shown**: you didn’t set `sha256_expected`. Add it and re-run the IPFS verifier.

---

## 10) “Done” Checklist

* [ ] 8 anchors present in `data/petrecords.jsonl` (each has `onChainTxHash` + `onChainCid`)
* [ ] `out/receipts/<tx>.html` exists for each confirmed tx
* [ ] `out/reports/tx_verification.json` shows `tx_ok: true` where confirmed
* [ ] `out/reports/ipfs_verification.json` shows `sha256` (and `MATCH` where expected provided)
* [ ] `out/reports/verification_merged.json` present
* [ ] RAG API returns `verified_onchain` and `receipt_html` per case
* [ ] `out/snapshot/latest.json` present (latest block cached)

---

**That’s it.** Drop this in as `README.txt`, and you’re ready to verify anchors, prove integrity, and surface trust signals in your RAG answers.
