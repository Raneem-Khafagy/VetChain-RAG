import json, sys, requests, hashlib

GATEWAY = "https://ipfs.io/ipfs"

def fetch(cid: str) -> bytes:
    r = requests.get(f"{GATEWAY}/{cid}", timeout=30)
    r.raise_for_status()
    return r.content

def main(path="data/petrecords.jsonl"):
    with open(path) as f:
        for line in f:
            r = json.loads(line)
            cid = r.get("onChainCid")
            if not cid:
                continue
            blob = fetch(cid)
            sha256 = hashlib.sha256(blob).hexdigest()
            print(f"{r['id']} CID={cid} sha256={sha256}")
            # If you store a keccak256 contentHash on-chain, compute it too:
            try:
                import sha3  # pysha3
                k = sha3.keccak_256(); k.update(blob)
                print(f"   keccak256=0x{k.hexdigest()}")
            except Exception:
                pass

if __name__ == "__main__":
    main(*sys.argv[1:])
