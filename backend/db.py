import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from backend.config import settings

def get_connection():
    conn = sqlite3.connect(settings.DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contracts (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                title TEXT,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clauses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contract_id TEXT NOT NULL,
                clause_number TEXT NOT NULL,
                heading TEXT NOT NULL,
                text TEXT NOT NULL,
                page_number INTEGER NOT NULL,
                clause_type TEXT,
                risk_level TEXT,
                risk_reason TEXT,
                FOREIGN KEY(contract_id) REFERENCES contracts(id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contract_id TEXT NOT NULL,
                document_title TEXT,
                summary TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(contract_id) REFERENCES contracts(id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contract_id TEXT NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                source_clauses_json TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(contract_id) REFERENCES contracts(id)
            )
        """)
        conn.commit()

def create_contract(contract_id: str, filename: str, file_path: str, title: Optional[str] = None, status: str = "uploaded") -> Dict[str, Any]:
    created_at = datetime.utcnow().isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO contracts (id, filename, file_path, title, created_at, status) VALUES (?, ?, ?, ?, ?, ?)",
            (contract_id, filename, file_path, title or filename, created_at, status)
        )
        conn.commit()
    return {"id": contract_id, "filename": filename, "file_path": file_path, "title": title or filename, "created_at": created_at, "status": status}

def update_contract(contract_id: str, title: Optional[str] = None, status: Optional[str] = None):
    with get_connection() as conn:
        cursor = conn.cursor()
        if title and status:
            cursor.execute("UPDATE contracts SET title = ?, status = ? WHERE id = ?", (title, status, contract_id))
        elif title:
            cursor.execute("UPDATE contracts SET title = ? WHERE id = ?", (title, contract_id))
        elif status:
            cursor.execute("UPDATE contracts SET status = ? WHERE id = ?", (status, contract_id))
        conn.commit()

def save_clauses(contract_id: str, clauses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    inserted_clauses = []
    with get_connection() as conn:
        cursor = conn.cursor()
        for c in clauses:
            cursor.execute(
                "INSERT INTO clauses (contract_id, clause_number, heading, text, page_number, clause_type, risk_level, risk_reason) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (contract_id, c.get("clause_number", ""), c.get("heading", ""), c.get("text", ""), c.get("page_number", 1),
                 c.get("clause_type"), c.get("risk_level"), c.get("risk_reason"))
            )
            c_id = cursor.lastrowid
            inserted_clauses.append({**c, "id": c_id, "contract_id": contract_id})
        conn.commit()
    return inserted_clauses

def get_contract(contract_id: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM contracts WHERE id = ?", (contract_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_clauses(contract_id: str) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clauses WHERE contract_id = ? ORDER BY id ASC", (contract_id,))
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

def update_clause_classification(clause_id: int, clause_type: str):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE clauses SET clause_type = ? WHERE id = ?", (clause_type, clause_id))
        conn.commit()

def update_clause_risk(clause_id: int, risk_level: str, risk_reason: str):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE clauses SET risk_level = ?, risk_reason = ? WHERE id = ?", (risk_level, risk_reason, clause_id))
        conn.commit()

def save_analysis(contract_id: str, summary: str, document_title: Optional[str] = None):
    created_at = datetime.utcnow().isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO analyses (contract_id, document_title, summary, created_at) VALUES (?, ?, ?, ?)",
            (contract_id, document_title, summary, created_at)
        )
        conn.commit()

def get_analysis(contract_id: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM analyses WHERE contract_id = ? ORDER BY id DESC LIMIT 1", (contract_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def save_chat_message(contract_id: str, question: str, answer: str, source_clauses: List[Dict[str, Any]]):
    created_at = datetime.utcnow().isoformat()
    sources_json = json.dumps(source_clauses)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO chat_messages (contract_id, question, answer, source_clauses_json, created_at) VALUES (?, ?, ?, ?, ?)",
            (contract_id, question, answer, sources_json, created_at)
        )
        conn.commit()

def get_chat_history(contract_id: str) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM chat_messages WHERE contract_id = ? ORDER BY id ASC", (contract_id,))
        rows = cursor.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["source_clauses"] = json.loads(d.get("source_clauses_json") or "[]")
            result.append(d)
        return result

def list_contracts() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT c.*, COUNT(cl.id) as clause_count FROM contracts c LEFT JOIN clauses cl ON c.id = cl.contract_id GROUP BY c.id ORDER BY c.created_at DESC")
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

init_db()
