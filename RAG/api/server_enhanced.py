"""
Enhanced RAG server with blockchain verification integration.
This version includes real-time chain status in query responses.
"""
from fastapi import FastAPI
from pydantic import BaseModel
from api.rag_index import RAGIndex
from api.rag_generate import generate
from api.verify_overlay import overlay_verification, format_verification_badge, get_trust_score
import os
import requests

app = FastAPI(title="VetChain RAG API", version="2.0")
idx = RAGIndex()

class QueryIn(BaseModel):
    symptoms: str
    top_k: int = 5
    include_verification: bool = True  # New field to control verification overlay

class QueryOut(BaseModel):
    cases: list
    answer: dict
    verification_summary: dict = None

@app.post("/query", response_model=QueryOut)
def query(q: QueryIn):
    """
    Search for similar veterinary cases with blockchain verification status.
    """
    # Step 1: Retrieve similar cases
    hits = idx.search(q.symptoms, k=q.top_k)
    
    # Step 2: Add blockchain verification status if requested
    if q.include_verification:
        hits = overlay_verification(hits)
        
        # Add trust scores and badges
        for hit in hits:
            hit["trust_score"] = get_trust_score(hit)
            hit["verification_badge"] = format_verification_badge(hit)
    
    # Step 3: Generate answer using LLM
    ans = generate(q.symptoms, hits)
    
    # Step 4: Create verification summary
    verification_summary = None
    if q.include_verification:
        total = len(hits)
        verified = sum(1 for h in hits if h.get("verified_onchain", False))
        with_chain = sum(1 for h in hits if h.get("onChainTxHash") and h["onChainTxHash"] != "")
        
        verification_summary = {
            "total_cases": total,
            "chain_anchored": with_chain,
            "verified_onchain": verified,
            "verification_rate": f"{(verified/total*100):.1f}%" if total > 0 else "0%",
            "trust_level": "high" if verified/total > 0.5 else "medium" if with_chain/total > 0.5 else "low"
        }
    
    return {
        "cases": hits, 
        "answer": ans,
        "verification_summary": verification_summary
    }

@app.get("/health")
def health():
    """
    Enhanced health check including chain verification status.
    """
    try:
        import requests, os
        host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
        r = requests.get(f"{host}/api/version", timeout=3)
        llm_ok = r.ok
    except Exception:
        llm_ok = False
    
    # Check index presence
    try:
        n = len(idx.meta)
        index_ok = True
        
        # Count records with chain data
        with_chain = sum(1 for m in idx.meta if m.get("onChainTxHash") and m["onChainTxHash"] != "")
    except Exception:
        n = 0
        index_ok = False
        with_chain = 0
    
    # Check chain API availability
    try:
        chain_api = os.getenv("PURECHAIN_API", "https://nsllab-kit.onrender.com/purechain/api/v1")
        r = requests.get(f"{chain_api}/health", timeout=3)
        chain_ok = r.ok
    except Exception:
        chain_ok = False
    
    return {
        "index_ok": index_ok, 
        "docs": n,
        "docs_with_chain": with_chain,
        "ollama_ok": llm_ok,
        "chain_api_ok": chain_ok,
        "verification_enabled": True
    }

@app.get("/case/{case_id}")
def get_case_details(case_id: str):
    """
    Get detailed information about a specific case including full verification status.
    """
    # Find the case in metadata
    case = None
    for m in idx.meta:
        if m.get("id") == case_id:
            case = m.copy()
            break
    
    if not case:
        return {"error": "Case not found"}
    
    # Add verification overlay
    cases_with_verification = overlay_verification([case])
    enriched_case = cases_with_verification[0] if cases_with_verification else case
    
    # Add additional details
    enriched_case["trust_score"] = get_trust_score(enriched_case)
    enriched_case["verification_badge"] = format_verification_badge(enriched_case)
    
    return enriched_case

@app.get("/stats")
def get_statistics():
    """
    Get statistics about the RAG index and blockchain verification.
    """
    total = len(idx.meta)
    with_chain = sum(1 for m in idx.meta if m.get("onChainTxHash") and m["onChainTxHash"] != "")
    
    # Get type distribution
    types = {}
    for m in idx.meta:
        t = m.get("type", "Unknown")
        types[t] = types.get(t, 0) + 1
    
    return {
        "total_records": total,
        "blockchain_anchored": with_chain,
        "percentage_anchored": f"{(with_chain/total*100):.1f}%" if total > 0 else "0%",
        "record_types": types,
        "index_status": "ready" if total > 0 else "empty"
    }