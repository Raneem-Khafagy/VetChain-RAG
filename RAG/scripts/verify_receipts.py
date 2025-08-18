import json, requests, sys

API = "https://nsllab-kit.onrender.com/purechain/api/v1"

def verify_tx(tx_hash: str):
    r = requests.get(f"{API}/tx/{tx_hash}", timeout=15)
    r.raise_for_status()
    return r.json()

def main(path="data/petrecords.jsonl"):
    ok = 0; total = 0
    with open(path) as f:
        for line in f:
            rec = json.loads(line)
            tx = rec.get("onChainTxHash")
            if not tx:
                continue
            total += 1
            try:
                resp = verify_tx(tx)
                status = (resp.get("success") and
                          resp.get("data", {}).get("status") in ("success","confirmed"))
                print(f"{rec['id']}  {tx}  {'OK' if status else 'NOT CONFIRMED'}")
                ok += 1 if status else 0
            except Exception as e:
                print(f"{rec['id']}  {tx}  ERROR: {e}")
    print(f"Summary: {ok}/{total} confirmed")

if __name__ == "__main__":
    main(*sys.argv[1:])
