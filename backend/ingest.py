import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import pymupdf
from backend.db import save_clauses, update_contract
from backend.chromadb_client import index_clauses

# Regex patterns for detecting clause headings
CLAUSE_PATTERNS = [
    # Pattern 1: Section/Article/Clause X or X.Y
    re.compile(r'^(?P<num>(?:SECTION|ARTICLE|CLAUSE)\s+[0-9IVXLCDM]+(?:\.[0-9]+)*)[\.:\-–\s]*(?P<heading>.*)$', re.IGNORECASE),
    # Pattern 2: Numbered headings like 1., 1.1, 1.1.1, 1)
    re.compile(r'^(?P<num>\d+(?:\.\d+)*[\.\)]?)\s+(?P<heading>.*)$'),
    # Pattern 3: Standard legal blocks
    re.compile(r'^(?P<num>WHEREAS|NOW,\s*THEREFORE|IN\s*WITNESS\s*WHEREOF)[\.:\-–\s]*(?P<heading>.*)$', re.IGNORECASE),
]

def extract_pdf_pages(pdf_path: str) -> List[Dict[str, Any]]:
    """Extracts raw text page by page from the PDF using PyMuPDF."""
    doc = pymupdf.open(pdf_path)
    pages = []
    for page_idx in range(len(doc)):
        page = doc[page_idx]
        text = page.get_text("text")
        pages.append({
            "page_number": page_idx + 1,
            "text": text
        })
    doc.close()
    return pages

def split_into_clauses(pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Splits text across PDF pages into legal clauses based on numbering,
    articles, sections, and legal recitals. Fallback chunking applies if no headings exist.
    """
    raw_clauses = []
    current_clause = {
        "clause_number": "Preamble",
        "heading": "Recitals & Preamble",
        "text_lines": [],
        "page_number": 1
    }
    
    found_any_heading = False

    for page in pages:
        page_num = page["page_number"]
        lines = page["text"].splitlines()

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            # Check if this line is a clause header
            matched = False
            for pattern in CLAUSE_PATTERNS:
                m = pattern.match(stripped)
                if m:
                    num = m.group("num").strip()
                    heading = (m.group("heading") or "").strip()
                    
                    # If heading is empty, use the number as heading or check if next line could be heading
                    if not heading:
                        heading = f"Clause {num}"

                    # Save previous clause if it has text
                    if current_clause["text_lines"]:
                        raw_clauses.append({
                            "clause_number": current_clause["clause_number"],
                            "heading": current_clause["heading"],
                            "text": "\n".join(current_clause["text_lines"]).strip(),
                            "page_number": current_clause["page_number"]
                        })

                    current_clause = {
                        "clause_number": num,
                        "heading": heading,
                        "text_lines": [stripped],
                        "page_number": page_num
                    }
                    matched = True
                    found_any_heading = True
                    break

            if not matched:
                current_clause["text_lines"].append(stripped)

    # Append the last clause
    if current_clause["text_lines"]:
        raw_clauses.append({
            "clause_number": current_clause["clause_number"],
            "heading": current_clause["heading"],
            "text": "\n".join(current_clause["text_lines"]).strip(),
            "page_number": current_clause["page_number"]
        })

    # Fallback: if no headings were detected (e.g. non-standard format), chunk by paragraph/length
    if not found_any_heading or len(raw_clauses) <= 1:
        fallback_clauses = []
        clause_idx = 1
        for page in pages:
            paragraphs = [p.strip() for p in page["text"].split("\n\n") if p.strip()]
            for p in paragraphs:
                if len(p) < 30 and not fallback_clauses:
                    continue
                first_line = p.split("\n")[0][:60]
                fallback_clauses.append({
                    "clause_number": f"Section {clause_idx}",
                    "heading": first_line,
                    "text": p,
                    "page_number": page["page_number"]
                })
                clause_idx += 1
        if fallback_clauses:
            return fallback_clauses

    return raw_clauses

def ingest_pdf(file_path: str, contract_id: str) -> List[Dict[str, Any]]:
    """
    Main ingestion pipeline:
    1. Extracts PDF text with page numbers
    2. Splits into structured clauses
    3. Persists clauses in SQLite DB
    4. Generates embeddings and stores in ChromaDB
    """
    pages = extract_pdf_pages(file_path)
    parsed_clauses = split_into_clauses(pages)
    
    # Store clauses in SQLite
    saved_clauses = save_clauses(contract_id, parsed_clauses)
    
    # Embed and index into ChromaDB
    index_clauses(contract_id, saved_clauses)
    
    # Update contract status
    update_contract(contract_id, status="ingested")
    
    return saved_clauses
