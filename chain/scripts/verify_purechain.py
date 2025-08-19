#!/usr/bin/env python3
"""
Verify transactions on PureChain using purechainlib SDK
"""

import os, sys, json, csv, pathlib, asyncio
from typing import Dict, Any, List
from purechainlib import PureChain
from web3 import Web3

# Configuration
NETWORK = "testnet"
PRIVATE_KEY = "742d620beac984c44bea9c3c8533b1d819a386a72ebd9bc3dcb47ee03d0034aa"

OUT_DIR = pathlib.Path("out")
RECEIPTS_DIR = OUT_DIR / "receipts_purechain"
REPORTS_DIR = OUT_DIR / "reports"
RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

def load_jsonl(path: str) -> List[Dict[str, Any]]:
    """Load JSONL file"""
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows

async def verify_transaction(pc: PureChain, tx_hash: str) -> Dict[str, Any]:
    """Verify a single transaction on PureChain"""
    result = {
        "tx_hash": tx_hash,
        "found": False,
        "status": None,
        "block_number": None,
        "from": None,
        "to": None,
        "gas_used": None,
        "error": None
    }
    
    try:
        # Ensure tx_hash is properly formatted
        if not tx_hash.startswith("0x"):
            tx_hash = "0x" + tx_hash
        
        # Try to get transaction receipt
        if hasattr(pc, 'web3'):
            try:
                receipt = pc.web3.eth.get_transaction_receipt(tx_hash)
                if receipt:
                    result["found"] = True
                    result["status"] = "confirmed" if receipt.status == 1 else "failed"
                    result["block_number"] = receipt.blockNumber
                    result["from"] = receipt["from"] if "from" in receipt else None
                    result["to"] = receipt.to
                    result["gas_used"] = receipt.gasUsed
                    
                    # Save receipt to file
                    receipt_path = RECEIPTS_DIR / f"{tx_hash}.json"
                    receipt_dict = dict(receipt)
                    # Convert HexBytes to hex strings for JSON serialization
                    for key, val in receipt_dict.items():
                        if hasattr(val, 'hex'):
                            receipt_dict[key] = val.hex()
                    receipt_path.write_text(json.dumps(receipt_dict, indent=2))
                else:
                    # Try to get transaction (might be pending)
                    tx = pc.web3.eth.get_transaction(tx_hash)
                    if tx:
                        result["found"] = True
                        result["status"] = "pending"
                        result["from"] = tx["from"]
                        result["to"] = tx.to
            except Exception as e:
                if "not found" not in str(e).lower():
                    result["error"] = str(e)
        
        # If web3 not available, try basic verification
        if not result["found"] and not result["error"]:
            result["error"] = "Unable to verify - web3 interface not available"
            
    except Exception as e:
        result["error"] = str(e)
    
    return result

async def main(in_path: str):
    """Main verification function"""
    print(f"Loading records from {in_path}...")
    records = load_jsonl(in_path)
    
    print("Connecting to PureChain...")
    pc = PureChain(NETWORK)
    pc.connect(PRIVATE_KEY)
    print(f"Connected to PureChain: {pc.address}")
    
    # Verify all transactions
    results = []
    for rec in records:
        rid = rec.get("id") or rec.get("case_id", "unknown")
        tx_hash = rec.get("onChainTxHash")
        
        if not tx_hash:
            results.append({
                "id": rid,
                "tx_hash": None,
                "status": "NO_TX",
                "error": "No transaction hash in record"
            })
            continue
        
        print(f"Verifying {rid}: {tx_hash}...", end=" ")
        verification = await verify_transaction(pc, tx_hash)
        
        result_entry = {
            "id": rid,
            "tx_hash": tx_hash,
            "status": verification["status"] or ("NOT_FOUND" if not verification["found"] else "UNKNOWN"),
            "block_number": verification["block_number"],
            "gas_used": verification["gas_used"],
            "error": verification["error"]
        }
        results.append(result_entry)
        
        if verification["found"]:
            print(f"✅ {verification['status']}")
        else:
            print(f"❌ NOT FOUND")
    
    # Summary
    print("\n" + "="*60)
    confirmed = sum(1 for r in results if r["status"] == "confirmed")
    pending = sum(1 for r in results if r["status"] == "pending")
    not_found = sum(1 for r in results if r["status"] == "NOT_FOUND")
    no_tx = sum(1 for r in results if r["status"] == "NO_TX")
    
    print(f"Summary:")
    print(f"  Confirmed: {confirmed}")
    print(f"  Pending: {pending}")
    print(f"  Not Found: {not_found}")
    print(f"  No TX Hash: {no_tx}")
    print(f"  Total: {len(results)}")
    
    # Save reports
    csv_path = REPORTS_DIR / "purechain_verification.csv"
    json_path = REPORTS_DIR / "purechain_verification.json"
    
    # Save CSV
    if results:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            fieldnames = ["id", "tx_hash", "status", "block_number", "gas_used", "error"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        print(f"\nCSV report saved to: {csv_path}")
    
    # Save JSON
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"JSON report saved to: {json_path}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        asyncio.run(main(sys.argv[1]))
    else:
        # Default to synth.jsonl
        asyncio.run(main("../../RAG/data/synth.jsonl"))