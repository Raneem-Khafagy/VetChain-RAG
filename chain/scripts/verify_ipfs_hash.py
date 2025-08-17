import os, sys, json, time, hashlib, pathlib, requests
from typing import List, Dict, Any

TIMEOUT = int(os.getenv("TIMEOUT_SECS", "30"))
GATEWAYS = [g.strip() for g in os.getenv("IPFS_GATEWAYS","https://ipfs.io/ipfs,https://cloudflare-ipfs.com/ipfs").split(",")]
OUT_DIR = pathlib.Path("out/reports")
OUT_DIR.mkdir(parents=True, exist_ok=True)

session = requests.Session()

def fetch_stream(cid: str) -> bytes:
    last_err = None
    for gw in GATEWAYS:
        url = f"{gw.rstrip('/')}/{cid}"
        try:
            with session.get(url, stream=True, timeout=TIMEOUT) as r:
                r.raise_for_status()
                h = hashlib.sha256()
                keccak = None
                try:
                    import sha3
                    keccak = sha3.keccak_256()
                except Exception:
                    pass
                for chunk in r.iter_content(chunk_size=1 << 16):
                    if chunk:
                        h.update(chunk)
                        if keccak: keccak.update(chunk)
                return h.hexdigest(), (f"0x{keccak.hexdigest()}" if keccak else None)
        except Exception as e:
            last_err = e
            continue
    raise RuntimeError(last_err or "Failed to fetch from all gateways")

def load_jsonl(path: str) -> List[Dict[str, Any]]:
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line: rows.append(json.loads(line))
    return rows

def main(in_path="data/petrecords.jsonl"):
    results = []
    for rec in load_jsonl(in_path):
        rid = rec.get("id") or rec.get("case_id")
        cid = rec.get("onChainCid")
        if not cid:
            results.append({"id": rid, "cid": None, "sha256": None, "keccak256": None, "match": None, "error": "no cid"})
            continue
        try:
            sha256_hex, keccak_hex = fetch_stream(cid)
            expected = rec.get("sha256_expected")
            match = (expected == sha256_hex) if expected else None
            print(f"{rid:<16} CID={cid} sha256={sha256_hex}{' MATCH' if match else ''}")
            results.append({"id": rid, "cid": cid, "sha256": sha256_hex, "keccak256": keccak_hex, "match": match, "error": None})
        except Exception as e:
            print(f"{rid:<16} CID={cid} ERROR: {e}")
            results.append({"id": rid, "cid": cid, "sha256": None, "keccak256": None, "match": None, "error": str(e)})

    p = OUT_DIR / "ipfs_verification.json"
    p.write_text(json.dumps(results, ensure_ascii=False, indent=2))
    print(f"Saved {p}")

if __name__ == "__main__":
    main(*sys.argv[1:])
