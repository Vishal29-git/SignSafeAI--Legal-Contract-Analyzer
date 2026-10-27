import json
import re
from typing import List, Dict, Any
from backend.config import settings
from backend.agents.qa import call_ollama
from backend.db import save_analysis, update_contract

def summarize_contract(contract_id: str, filename: str, clauses: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extracts the document title and generates a plain English explanation of the contract.
    Fast and concise with format: json.
    """
    excerpt_lines = []
    for c in clauses[:6]:
        excerpt_lines.append(f"[{c.get('clause_number', '')}] {c.get('heading', '')}: {c.get('text', '')[:120].replace(chr(10), ' ')}")
    overview = "\n".join(excerpt_lines)

    title = filename.replace(".pdf", "").replace("_", " ").title()
    summary = "This agreement governs the legal rights, confidentiality, and operational responsibilities between the parties."

    prompt = (
        "Based on these contract excerpts, provide:\n"
        "1. The formal document title.\n"
        "2. An executive summary in clear, simple English.\n\n"
        f"Excerpts:\n{overview}\n\n"
        'Return JSON: {"document_title": "Mutual Non-Disclosure Agreement", "summary": "This contract outlines..."}'
    )

    try:
        raw_response = call_ollama(prompt=prompt, format_json=True)
        data = json.loads(raw_response)
        if data.get("document_title"):
            title = data["document_title"].strip()
        if data.get("summary"):
            summary = data["summary"].strip()
    except Exception as e:
        print("Summary parsing error:", e)

    save_analysis(contract_id, summary=summary, document_title=title)
    update_contract(contract_id, title=title)

    return {
        "document_title": title,
        "summary": summary
    }
