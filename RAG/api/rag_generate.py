# api/rag_generate.py
import os, json, requests

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "phi3:mini")   # fast default
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "15")) # hard cap to prevent hangs
NO_LLM = os.getenv("NO_LLM", "0") == "1"                # emergency bypass

SYSTEM = "You are a veterinary assistant. Use ONLY the provided cases and cite their case_id."

def _ollama_generate(model: str, prompt: str) -> str:
    url = f"{OLLAMA_HOST}/api/generate"
    payload = {"model": model, "prompt": prompt, "stream": False}
    r = requests.post(url, json=payload, timeout=OLLAMA_TIMEOUT)
    r.raise_for_status()
    return r.json().get("response", "").strip()

def _fallback_answer(query: str, cases: list) -> dict:
    # no LLM: still return something useful & structured
    return {
        "differentials": [],
        "rationale": "LLM unavailable; returning retrieved cases only.",
        "citations": [c["id"] for c in cases]
    }

def generate(query: str, cases: list, model: str | None = None) -> dict:
    if NO_LLM:
        return _fallback_answer(query, cases)

    model = model or OLLAMA_MODEL
    ctx = "\n".join([f"- case_id={c['id']} title={c.get('title','')} tx={c.get('onChainTxHash','')}" for c in cases])
    prompt = f"""{SYSTEM}

Symptoms: {query}

Cases:
{ctx}

Task: Provide 2–4 differential diagnoses with brief rationale.
Output JSON with keys: differentials[], rationale, citations[] (use case_id).
If insufficient evidence, say so explicitly.
"""
    try:
        txt = _ollama_generate(model, prompt)
        try:
            return json.loads(txt)  # if the model produced JSON
        except Exception:
            return {"raw": txt}     # if it returned text
    except Exception as e:
        # never crash the API; return structured fallback
        return {"error": "llm_unavailable", "detail": str(e), **_fallback_answer(query, cases)}
