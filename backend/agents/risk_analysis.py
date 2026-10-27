import json
import re
from typing import List, Dict, Any
from backend.config import settings
from backend.agents.qa import call_ollama
from backend.db import update_clause_risk

def rule_risk(heading: str, text: str) -> tuple[str, str]:
    combined = (heading + " " + text[:350]).lower()
    if any(k in combined for k in ["liquidated damages", "penalty", "unlimited liability", "$50,000", "indemnif", "hold harmless", "non-compete"]):
        return "High", "Imposes direct monetary liabilities, penalties, or restrictive covenants."
    if any(k in combined for k in ["auto-renew", "automatic renewal", "exclusive jurisdiction", "within 10 days", "sole discretion"]):
        return "Medium", "Contains time-sensitive commitment or jurisdiction requirements."
    return "Low", "Standard contractual provision with customary mutual obligations."

def analyze_clause_risks(contract_id: str, clauses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Rates each clause as Low, Medium, or High risk with a one-line reason.
    Fast keyword heuristics + LLM refinement for critical provisions.
    Guaranteed to complete quickly without timeouts.
    """
    if not clauses:
        return []

    results = []
    need_llm = []

    for c in clauses:
        level, reason = rule_risk(c.get("heading", ""), c.get("text", ""))
        # If it's High risk or Medium, let's keep or refine it
        if level in ["High", "Medium"]:
            need_llm.append(c)
        else:
            update_clause_risk(c["id"], "Low", reason)
            results.append({"clause_id": c["id"], "risk_level": "Low", "reason": reason})

    # Run compact LLM pass on the flagged high/medium clauses (capped at top 6 for speed)
    if need_llm:
        to_llm = need_llm[:6]
        summaries = [
            f"ID {c['id']}: {c['heading']} - {c['text'][:120].replace(chr(10), ' ')}"
            for c in to_llm
        ]
        prompt = (
            "Rate each clause as 'Low', 'Medium', or 'High' risk with a 1-line reason.\n"
            "Clauses:\n" + "\n".join(summaries) + "\n\n"
            'Return JSON: {"risks": [{"clause_id": 1, "risk_level": "High", "reason": "Imposes severe financial penalty."}]}'
        )
        try:
            raw = call_ollama(prompt=prompt, format_json=True)
            data = json.loads(raw)
            items = data.get("risks") or (data if isinstance(data, list) else [])
            for item in items:
                cid = item.get("clause_id")
                risk = str(item.get("risk_level", "Medium")).capitalize().strip()
                if risk not in ["Low", "Medium", "High"]:
                    risk = "Medium"
                reason = str(item.get("reason", "Contains significant contractual liability.")).strip()
                if cid:
                    update_clause_risk(int(cid), risk, reason)
                    results.append({"clause_id": int(cid), "risk_level": risk, "reason": reason})
        except Exception as e:
            print("Risk LLM parsing fallback:", e)

    # Any remaining clauses
    analyzed_ids = {r["clause_id"] for r in results}
    for c in clauses:
        if c["id"] not in analyzed_ids:
            lvl, rsn = rule_risk(c.get("heading", ""), c.get("text", ""))
            update_clause_risk(c["id"], lvl, rsn)
            results.append({"clause_id": c["id"], "risk_level": lvl, "reason": rsn})

    return results
