import os, sys, json, csv, time, pathlib, asyncio
from typing import Dict, Any, Optional, List
from purechainlib import PureChain

OUT_DIR = pathlib.Path("out")
RECEIPTS_DIR = OUT_DIR / "receipts"
REPORTS_DIR = OUT_DIR / "reports"
RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

async def verify_tx_with_sdk(pc: PureChain, tx_hash: str) -> Dict[str, Any]:
    """Verify transaction using PureChain SDK"""
    result = {"ok": False, "status": None, "confirmations": None, "from": None, "to": None, "error": None}
    try:
        # Get transaction receipt using PureChain SDK
        receipt = await pc.get_receipt(tx_hash)
        if receipt:
            result["ok"] = True
            result["status"] = "confirmed" if receipt.get("status") == 1 else "pending"
            result["confirmations"] = receipt.get("blockNumber", 0)
            result["from"] = receipt.get("from")
            result["to"] = receipt.get("to")
        else:
            # Try getting transaction directly
            tx = await pc.get_transaction(tx_hash)
            if tx:
                result["status"] = "pending"
                result["from"] = tx.get("from")
                result["to"] = tx.get("to")
            else:
                result["error"] = "Transaction not found"
    except Exception as e:
        result["error"] = str(e)
    return result

def save_receipt_data(tx_hash: str, receipt_data: dict) -> Dict[str, Optional[str]]:
    """Save receipt data to files"""
    paths = {"json_path": None, "error": None}
    try:
        json_path = RECEIPTS_DIR / f"{tx_hash}.json"
        json_path.write_text(json.dumps(receipt_data, ensure_ascii=False, indent=2))
        paths["json_path"] = str(json_path)
    except Exception as e:
        paths["error"] = str(e)
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

async def process_record(pc: PureChain, rec: Dict[str, Any]) -> Dict[str, Any]:
    rid = rec.get("id") or rec.get("case_id")
    tx = rec.get("onChainTxHash")
    result = {
        "id": rid, "tx_hash": tx, "tx_ok": None, "tx_status": None, "confirmations": None,
        "from": None, "to": None, "receipt_json": None, "error": None
    }
    if not tx:
        result["error"] = "no tx hash"
        return result
    
    # Verify transaction using SDK
    txres = await verify_tx_with_sdk(pc, tx)
    result.update({
        "tx_ok": txres["ok"], "tx_status": txres["status"], "confirmations": txres["confirmations"],
        "from": txres["from"], "to": txres["to"]
    })
    
    # Save receipt if we got one
    if txres["ok"]:
        receipt = await pc.get_receipt(tx)
        if receipt:
            paths = save_receipt_data(tx, receipt)
            result["receipt_json"] = paths["json_path"]
            if paths.get("error"):
                result["error"] = paths["error"]
    
    if txres.get("error"):
        result["error"] = txres["error"]
    
    return result

async def main_async(in_path="data/petrecords.jsonl"):
    # Initialize PureChain
    pc = PureChain()
    await pc.init()
    
    records = load_jsonl(in_path)
    results = []
    
    # Process records
    for r in records:
        result = await process_record(pc, r)
        results.append(result)
    
    # Print per-line result and summarize
    ok = sum(1 for r in results if r["tx_ok"])
    total = sum(1 for r in results if r["tx_hash"])
    for r in sorted(results, key=lambda x: (x["id"] or "")):
        status = "CONFIRMED" if r["tx_ok"] else ("NOT FOUND" if r["tx_hash"] else "NO TX")
        print(f"{r['id']:<16} {r.get('tx_hash','-')}  {status}")
    
    print(f"\nSummary: {ok}/{total} confirmed on PureChain")
    
    # Save reports
    if results:
        csv_path = REPORTS_DIR / "tx_verification_purechain.csv"
        json_path = REPORTS_DIR / "tx_verification_purechain.json"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
            w.writeheader()
            w.writerows(results)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"Reports saved to {csv_path} and {json_path}")

def main(in_path="data/petrecords.jsonl"):
    asyncio.run(main_async(in_path))

if __name__ == "__main__":
    main(*sys.argv[1:])