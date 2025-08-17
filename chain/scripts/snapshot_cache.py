import os, json, pathlib, requests, time
PURECHAIN_API = os.getenv("PURECHAIN_API", "https://nsllab-kit.onrender.com/purechain/api/v1")
OUT = pathlib.Path("out/snapshot"); OUT.mkdir(parents=True, exist_ok=True)

def get(url): 
    r = requests.get(url, timeout=15); r.raise_for_status(); return r.json()

def main():
    tip = get(f"{PURECHAIN_API}/block/latest")
    snap = {"fetched_at": int(time.time()), "latest_block": tip.get("data")}
    (OUT / "latest.json").write_text(json.dumps(snap, indent=2))
    print(f"Saved {OUT/'latest.json'}")

if __name__ == "__main__":
    main()
