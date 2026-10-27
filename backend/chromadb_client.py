import json
import urllib.request
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from backend.config import settings

def get_embedding(text: str) -> List[float]:
    """Generates a 768-dim vector embedding using local Ollama nomic-embed-text."""
    url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/embeddings"
    data = json.dumps({
        "model": settings.EMBED_MODEL,
        "prompt": text
    }).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode("utf-8"))
        return result.get("embedding", [])

_client = None

def get_chroma_client():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=str(settings.CHROMA_DIR))
    return _client

def get_collection(collection_name: str = "contract_clauses"):
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )

def index_clauses(contract_id: str, clauses: List[Dict[str, Any]]):
    """Embeds and indexes contract clauses into persistent ChromaDB."""
    if not clauses:
        return
    
    collection = get_collection()
    
    ids = []
    documents = []
    metadatas = []
    embeddings = []
    
    for c in clauses:
        clause_id_str = f"{contract_id}_{c.get('id', c.get('clause_number', '0'))}"
        # Context to embed: Heading + Clause Text
        text_content = f"{c.get('heading', '')}\n{c.get('text', '')}".strip()
        if not text_content:
            continue
            
        emb = get_embedding(text_content)
        
        ids.append(clause_id_str)
        documents.append(text_content)
        embeddings.append(emb)
        metadatas.append({
            "contract_id": contract_id,
            "clause_id": str(c.get("id", "")),
            "clause_number": str(c.get("clause_number", "")),
            "heading": str(c.get("heading", "")),
            "page_number": int(c.get("page_number", 1))
        })
        
    if ids:
        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )

def search_clauses(contract_id: str, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Performs semantic similarity search for clauses relevant to query."""
    collection = get_collection()
    query_emb = get_embedding(query)
    
    results = collection.query(
        query_embeddings=[query_emb],
        n_results=top_k,
        where={"contract_id": contract_id}
    )
    
    matched = []
    if results and "documents" in results and results["documents"]:
        docs = results["documents"][0]
        metas = results["metadatas"][0] if "metadatas" in results and results["metadatas"] else []
        distances = results.get("distances", [[]])[0] if "distances" in results else []
        
        for i, doc in enumerate(docs):
            meta = metas[i] if i < len(metas) else {}
            dist = distances[i] if i < len(distances) else 0.0
            matched.append({
                "clause_id": meta.get("clause_id"),
                "clause_number": meta.get("clause_number", ""),
                "heading": meta.get("heading", ""),
                "text": doc,
                "page_number": meta.get("page_number", 1),
                "distance": dist
            })
            
    return matched
