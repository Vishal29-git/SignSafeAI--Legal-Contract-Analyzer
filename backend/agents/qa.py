import json
import urllib.request
from typing import Dict, Any, List
from backend.config import settings
from backend.chromadb_client import search_clauses
from backend.db import save_chat_message

def call_ollama(prompt: str, system: str = "", format_json: bool = False) -> str:
    """Calls local Ollama instance with timeout=300 and optional format: json."""
    url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/generate"
    payload = {
        "model": settings.LLM_MODEL,
        "prompt": prompt,
        "system": system,
        "options": {
            "temperature": settings.TEMPERATURE,
            "num_ctx": 4096
        },
        "stream": False
    }
    if format_json:
        payload["format"] = "json"
        
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as resp:
        result = json.loads(resp.read().decode("utf-8"))
        return result.get("response", "").strip()

def answer_contract_question(contract_id: str, question: str) -> Dict[str, Any]:
    """
    RAG-based verified Q&A:
    1. Retrieves relevant clauses from ChromaDB.
    2. Prompts Qwen2.5:3b (temp 0.2) to verify against retrieved text.
    3. If proof is missing, returns 'Not found in the document'.
    4. Records Q&A in SQLite.
    """
    retrieved_clauses = search_clauses(contract_id, query=question, top_k=4)
    
    if not retrieved_clauses:
        answer = "Not found in the document."
        save_chat_message(contract_id, question, answer, [])
        return {
            "contract_id": contract_id,
            "question": question,
            "answer": answer,
            "source_clauses": [],
            "verified": False
        }

    context_blocks = []
    for c in retrieved_clauses:
        context_blocks.append(
            f"--- CLAUSE {c.get('clause_number', '')}: {c.get('heading', '')} (Page {c.get('page_number', 1)}) ---\n{c.get('text', '')}"
        )
    context_str = "\n\n".join(context_blocks)

    system_prompt = (
        "You are a strict, privacy-first legal contract assistant. "
        "Your task is to answer the user's question using ONLY the provided contract clauses. "
        "CRITICAL RULES:\n"
        "1. Every claim in your answer must be directly supported by the provided text.\n"
        "2. If the answer cannot be proven or is not found in the provided clauses, respond ONLY with:\n"
        "   'Not found in the document.'\n"
        "3. Keep the answer concise, accurate, and professional.\n"
        "4. Do not speculate or introduce outside legal concepts."
    )

    user_prompt = (
        f"Contract Clauses:\n{context_str}\n\n"
        f"User Question: {question}\n\n"
        "Answer strictly according to the clauses above:"
    )

    raw_answer = call_ollama(prompt=user_prompt, system=system_prompt)

    is_not_found = "not found in the document" in raw_answer.lower()
    
    if is_not_found:
        final_answer = "Not found in the document."
        sources = []
        verified = False
    else:
        final_answer = raw_answer
        sources = [
            {
                "clause_number": c.get("clause_number", ""),
                "heading": c.get("heading", ""),
                "text": c.get("text", ""),
                "page_number": c.get("page_number", 1)
            }
            for c in retrieved_clauses
        ]
        verified = True

    save_chat_message(contract_id, question, final_answer, sources)

    return {
        "contract_id": contract_id,
        "question": question,
        "answer": final_answer,
        "source_clauses": sources,
        "verified": verified
    }
