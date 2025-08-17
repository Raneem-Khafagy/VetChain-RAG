import os, sys, json, csv, time, pathlib, concurrent.futures
from typing import Dict, Any, Optional, List
import requests

PURECHAIN_API = os.getenv("PURECHAIN_API", "https://nsllab-kit.onrender.com/purechain/api/v1")
TIMEOUT = int(os.getenv("TIMEOUT_SECS", "20"))
CONCURRENCY = int(os.getenv("CONCURRENCY", "8"))

OUT_DIR = pathlib.Path("out")
RECEIPTS_DIR = OUT_DIR / "receipts"
REPORTS_DIR = OUT_DIR / "reports"
RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

session = requests.Session()

def get_json(url: str) -> Dict[str, Any]:
    r = session.get(url, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()

def get_text(url: str) -> str:
    r = session.get(url, timeout=TIMEOUT)
    r.raise_for_status()
    return r.text

def verify_tx(tx_hash: str) -> Dict[str, Any]:
    """Return dict with fields: ok, status, confirmations, from, to, error"""
    result = {"ok": False, "status": None, "confirmations": None, "from": None, "to": None, "error": None}
    try:
        data = get_json(f"{PURECHAIN_API}/tx/{tx_hash}")
        if not data.get("success"):
            result["error"] = "success=false"
            return result
        d = data.get("data", {})
        result["status"] = d.get("status")
        result["confirmations"] = d.get("confirmations")
        result["from"] = d.get("from")
        result["to"] = d.get("to")
        result["ok"] = (d.get("status") in ("success", "confirmed"))
        return result
    except Exception as e:
        # legacy quick endpoint as fallback
        try:
            data = get_json(f"{PURECHAIN_API.replace('/v1','')}/confirmation/{tx_hash}")
            result["ok"] = bool(data.get("success"))
            result["status"] = "confirmed" if result["ok"] else "unknown"
        except Exception:
            result["error"] = str(e)
        return result

def save_receipts(tx_hash: str) -> Dict[str, Optional[str]]:
    paths = {"html_path": None, "json_path": None, "error": None}
    try:
        html = get_text(f"{PURECHAIN_API}/tx/{tx_hash}/receipt")  # printable
        html_path = RECEIPTS_DIR / f"{tx_hash}.html"
        html_path.write_text(html, encoding="utf-8")
        paths["html_path"] = str(html_path)
    except Exception as e:
        paths["error"] = f"html: {e}"

    try:
        j = get_json(f"{PURECHAIN_API}/receipt/{tx_hash}")        # decoded events
        json_path = RECEIPTS_DIR / f"{tx_hash}.json"
        json_path.write_text(json.dumps(j, ensure_ascii=False, indent=2))
        paths["json_path"] = str(json_path)
    except Exception as e:
        paths["error"] = (paths["error"] + f"; json: {e}") if paths["error"] else f"json: {e}"
    return paths

def load_jsonl(path: str) -> List[Dict[str, Any]]:
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows

def process_record(rec: Dict[str, Any]) -> Dict[str, Any]:
    rid = rec.get("id") or rec.get("case_id")
    tx = rec.get("onChainTxHash")
    result = {
        "id": rid, "tx_hash": tx, "tx_ok": None, "tx_status": None, "confirmations": None,
        "from": None, "to": None, "receipt_html": None, "receipt_json": None, "error": None
    }
    if not tx:
        result["error"] = "no tx hash"
        return result
    txres = verify_tx(tx)
    result.update({
        "tx_ok": txres["ok"], "tx_status": txres["status"], "confirmations": txres["confirmations"],
        "from": txres["from"], "to": txres["to"]
    })
    paths = save_receipts(tx)
    result["receipt_html"] = paths["html_path"]
    result["receipt_json"] = paths["json_path"]
    if txres.get("error") or paths.get("error"):
        errs = [e for e in (txres.get("error"), paths.get("error")) if e]
        result["error"] = " | ".join(errs)
    return result

def main(in_path="data/petrecords.jsonl"):
    records = load_jsonl(in_path)
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENCY) as ex:
        futures = [ex.submit(process_record, r) for r in records]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    # print per-line result and summarize
    ok = sum(1 for r in results if r["tx_ok"])
    total = sum(1 for r in results if r["tx_hash"])
    for r in sorted(results, key=lambda x: (x["id"] or "")):
        status = "OK" if r["tx_ok"] else ("NOT CONFIRMED" if r["tx_hash"] else "NO TX")
        print(f"{r['id']:<16} {r.get('tx_hash','-')}  {status}")

    print(f"Summary: {ok}/{total} confirmed")

    # save reports
    csv_path = REPORTS_DIR / "tx_verification.csv"
    json_path = REPORTS_DIR / "tx_verification.json"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        w.writeheader(); w.writerows(results)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main(*sys.argv[1:])