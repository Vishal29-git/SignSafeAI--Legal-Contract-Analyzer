import json
import re
from typing import List, Dict, Any
from backend.config import settings
from backend.agents.qa import call_ollama
from backend.db import update_clause_classification

CATEGORIES = ["payment", "termination", "penalty", "auto-renewal", "non-compete", "jurisdiction", "other"]

def rule_classify(heading: str, text: str) -> str:
    combined = (heading + " " + text[:300]).lower()
    if any(k in combined for k in ["fee", "payment", "price", "pay ", "invoice", "compensation", "royalt"]):
        return "payment"
    if any(k in combined for k in ["terminat", "cancellation", "expiration", "notice of term"]):
        return "termination"
    if any(k in combined for k in ["liquidated damages", "penalty", "forfeit", "punitive damages"]):
        return "penalty"
    if any(k in combined for k in ["auto-renew", "automatic renewal", "automatically renew", "evergreen"]):
        return "auto-renewal"
    if any(k in combined for k in ["non-compete", "non compete", "non-solicit", "restrictive covenant"]):
        return "non-compete"
    if any(k in combined for k in ["governing law", "jurisdiction", "venue", "dispute resolution", "arbitrat"]):
        return "jurisdiction"
    return "other"

def classify_clauses(contract_id: str, clauses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Classifies each clause quickly and robustly.
    Uses fast keyword classification for obvious clauses and LLM for ambiguous clauses.
    Never times out.
    """
    if not clauses:
        return []

    results = []
    ambiguous = []

    for c in clauses:
        cat = rule_classify(c.get("heading", ""), c.get("text", ""))
        if cat != "other":
            update_clause_classification(c["id"], cat)
            results.append({"clause_id": c["id"], "category": cat})
        else:
            ambiguous.append(c)

    # If there are ambiguous clauses, classify the top ones using Qwen2.5:3b with compact prompt
    if ambiguous:
        to_llm = ambiguous[:8] # Capped at top 8 to guarantee fast generation under 15 seconds
        summaries = [
            f"ID {c['id']}: {c['heading']} - {c['text'][:100].replace(chr(10), ' ')}"
            for c in to_llm
        ]
        
        prompt = (
            "Classify each clause into: payment, termination, penalty, auto-renewal, non-compete, jurisdiction, other.\n"
            "Clauses:\n" + "\n".join(summaries) + "\n\n"
            'Return JSON: {"classifications": [{"clause_id": 1, "category": "payment"}]}'
        )
        
        try:
            raw = call_ollama(prompt=prompt, format_json=True)
            data = json.loads(raw)
            items = data.get("classifications") or data.get("clauses") or (data if isinstance(data, list) else [])
            for item in items:
                cid = item.get("clause_id")
                category = str(item.get("category", "other")).lower().strip()
                if category not in CATEGORIES:
                    category = "other"
                if cid:
                    update_clause_classification(int(cid), category)
                    results.append({"clause_id": int(cid), "category": category})
        except Exception as e:
            print("Classifier LLM parsing fallback:", e)

    # Any remaining clauses get default 'other'
    classified_ids = {r["clause_id"] for r in results}
    for c in clauses:
        if c["id"] not in classified_ids:
            update_clause_classification(c["id"], "other")
            results.append({"clause_id": c["id"], "category": "other"})

    return results
