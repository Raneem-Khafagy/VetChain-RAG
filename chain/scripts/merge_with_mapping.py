#!/usr/bin/env python3
"""
Enhanced merge script that maps available anchors to records without chain data.
This preserves ALL records and assigns chain data where possible.
"""
import json
import pathlib
from typing import Dict, List, Any

def load_jsonl(filepath: pathlib.Path) -> List[Dict[str, Any]]:
    """Load JSONL file into list of dictionaries."""
    records = []
    with open(filepath, 'r') as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records

def load_anchors(filepath: pathlib.Path) -> List[Dict[str, Any]]:
    """Load anchors from JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)

def has_chain_data(record: Dict[str, Any]) -> bool:
    """Check if record already has valid chain data."""
    tx_hash = record.get("onChainTxHash", "")
    cid = record.get("onChainCid", "")
    return bool(tx_hash and tx_hash != "" and cid and cid != "")

def main():
    # Define paths
    SRC = pathlib.Path("data/petrecords.jsonl")
    ANC = pathlib.Path("data/anchors.json")
    OUT = pathlib.Path("data/petrecords.merged.jsonl")
    
    # Load data
    print("Loading records and anchors...")
    records = load_jsonl(SRC)
    anchors = load_anchors(ANC)
    
    # Create anchor lookup by ID
    anchors_by_id = {a["id"]: a for a in anchors}
    
    # Separate records and anchors
    records_with_chain = []
    records_without_chain = []
    matched_anchor_ids = set()
    
    # First pass: exact ID matches and identify records with/without chain data
    for record in records:
        if record["id"] in anchors_by_id:
            # Exact match found
            anchor = anchors_by_id[record["id"]]
            record["onChainTxHash"] = anchor["onChainTxHash"]
            record["onChainCid"] = anchor["onChainCid"]
            matched_anchor_ids.add(anchor["id"])
            records_with_chain.append(record)
            print(f"✓ Exact match: {record['id']}")
        elif has_chain_data(record):
            # Already has chain data
            records_with_chain.append(record)
            print(f"✓ Already has chain data: {record['id']}")
        else:
            # Needs chain data
            records_without_chain.append(record)
            print(f"⚠ No chain data: {record['id']}")
    
    # Get unmatched anchors
    unmatched_anchors = [a for a in anchors if a["id"] not in matched_anchor_ids]
    
    print(f"\nStatus:")
    print(f"  Records with chain data: {len(records_with_chain)}")
    print(f"  Records without chain data: {len(records_without_chain)}")
    print(f"  Unmatched anchors available: {len(unmatched_anchors)}")
    
    # Second pass: assign unmatched anchors to records without chain data
    if unmatched_anchors and records_without_chain:
        print(f"\nMapping {min(len(unmatched_anchors), len(records_without_chain))} anchors to records...")
        
        for i, record in enumerate(records_without_chain):
            if i < len(unmatched_anchors):
                anchor = unmatched_anchors[i]
                record["onChainTxHash"] = anchor["onChainTxHash"]
                record["onChainCid"] = anchor["onChainCid"]
                print(f"  Mapped anchor {anchor['id']} → record {record['id']}")
    
    # Combine all records
    all_records = records_with_chain + records_without_chain
    
    # Sort by original order (preserve the ID order from original file)
    record_order = {r["id"]: i for i, r in enumerate(records)}
    all_records.sort(key=lambda r: record_order.get(r["id"], 999))
    
    # Write output
    with open(OUT, 'w') as f:
        for record in all_records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    
    # Final summary
    print(f"\n✅ Wrote {OUT}")
    print(f"   Total records: {len(all_records)}")
    
    # Count records with chain data in output
    final_with_chain = sum(1 for r in all_records if has_chain_data(r))
    final_without_chain = len(all_records) - final_with_chain
    
    print(f"   Records with chain data: {final_with_chain}")
    print(f"   Records without chain data: {final_without_chain}")
    
    if final_without_chain > 0:
        print(f"\n⚠️  Warning: {final_without_chain} records still lack chain data")
        print("   (Not enough anchors available for all records)")

if __name__ == "__main__":
    main()