import json, pathlib

def index_by_id(rows): return {r["id"]: r for r in rows if r.get("id")}

def main():
    tx = json.loads((pathlib.Path("out/reports/tx_verification.json")).read_text())
    ip = json.loads((pathlib.Path("out/reports/ipfs_verification.json")).read_text())
    ix_tx, ix_ip = index_by_id(tx), index_by_id(ip)
    merged = []
    ids = sorted(set(ix_tx.keys()) | set(ix_ip.keys()))
    for rid in ids:
        r = { "id": rid }
        r.update(ix_tx.get(rid, {}))
        r.update({f"ipfs_{k}": v for k, v in ix_ip.get(rid, {}).items() if k not in ("id")})
        merged.append(r)
    out = pathlib.Path("out/reports/verification_merged.json")
    out.write_text(json.dumps(merged, ensure_ascii=False, indent=2))
    print(f"Saved {out}")

if __name__ == "__main__":
    main()
