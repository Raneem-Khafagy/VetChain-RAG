"""
Overlay blockchain verification status onto RAG search results.
This module enriches RAG results with real-time chain verification data.
"""
import json
import pathlib
from typing import List, Dict, Any

# Default paths to verification reports
REPORTS_DIR = pathlib.Path("../chain/out/reports")
TX_REPORT = REPORTS_DIR / "tx_verification.json"
IPFS_REPORT = REPORTS_DIR / "ipfs_verification.json"

def load_verification_status() -> tuple[dict, dict]:
    """Load the latest verification reports from chain module."""
    tx_status = {}
    ipfs_status = {}
    
    # Load transaction verification status
    if TX_REPORT.exists():
        with open(TX_REPORT) as f:
            data = json.load(f)
            for record in data.get("records", []):
                if record.get("id"):
                    tx_status[record["id"]] = {
                        "verified_onchain": record.get("tx_ok", False),
                        "confirmations": record.get("confirmations", 0),
                        "tx_status": record.get("status", "unknown")
                    }
    
    # Load IPFS verification status
    if IPFS_REPORT.exists():
        with open(IPFS_REPORT) as f:
            data = json.load(f)
            for record in data.get("records", []):
                if record.get("id"):
                    ipfs_status[record["id"]] = {
                        "ipfs_sha256": record.get("sha256", ""),
                        "ipfs_match": record.get("match", None)
                    }
    
    return tx_status, ipfs_status

def overlay_verification(cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Enrich RAG search results with blockchain verification status.
    
    Args:
        cases: List of case dictionaries from RAG search
        
    Returns:
        Enriched cases with verification fields added
    """
    tx_status, ipfs_status = load_verification_status()
    
    for case in cases:
        case_id = case.get("id")
        
        # Add transaction verification status
        if case_id in tx_status:
            case.update(tx_status[case_id])
        else:
            case["verified_onchain"] = False
            case["tx_status"] = "unverified"
        
        # Add IPFS verification status
        if case_id in ipfs_status:
            case.update(ipfs_status[case_id])
        
        # Add receipt links if verified
        if case.get("verified_onchain") and case.get("onChainTxHash"):
            tx_hash = case["onChainTxHash"]
            case["receipt_html"] = f"../chain/out/receipts/{tx_hash}.html"
            case["receipt_json"] = f"../chain/out/receipts/{tx_hash}.json"
    
    return cases

def get_trust_score(case: Dict[str, Any]) -> int:
    """
    Calculate a trust score based on verification status.
    
    Returns:
        Score from 0-100 indicating trust level
    """
    score = 0
    
    # Base score for having chain data
    if case.get("onChainTxHash") and case["onChainTxHash"] != "":
        score += 30
    
    # Verified on chain
    if case.get("verified_onchain"):
        score += 40
    
    # IPFS content matches
    if case.get("ipfs_match") == True:
        score += 20
    
    # Has sufficient confirmations
    if case.get("confirmations", 0) >= 6:
        score += 10
    
    return min(score, 100)

def format_verification_badge(case: Dict[str, Any]) -> str:
    """
    Generate a verification badge string for UI display.
    """
    if case.get("verified_onchain"):
        if case.get("ipfs_match"):
            return "✅ Fully Verified"
        else:
            return "🔗 Chain Verified"
    elif case.get("onChainTxHash"):
        return "⏳ Pending Verification"
    else:
        return "❌ Unverified"