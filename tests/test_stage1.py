import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pymupdf
from fastapi.testclient import TestClient
from backend.main import app
import backend.db as db

def generate_sample_pdf(pdf_path: str):
    """Generates a synthetic NDA PDF with numbered clauses using PyMuPDF."""
    doc = pymupdf.open()
    page = doc.new_page()
    
    text = (
        "MUTUAL NON-DISCLOSURE AGREEMENT\n\n"
        "This Mutual Non-Disclosure Agreement (the 'Agreement') is entered into as of January 1, 2026.\n\n"
        "1. Definition of Confidential Information\n"
        "Confidential Information refers to proprietary business, technical, or financial data disclosed by Discloser to Recipient.\n\n"
        "2. Obligations and Restrictions\n"
        "The Recipient shall exercise reasonable care to protect the Confidential Information and shall not disclose it to third parties without prior written consent.\n\n"
        "3. Term and Termination\n"
        "This Agreement shall remain in effect for a term of two (2) years from the Effective Date. Either party may terminate with 30 days prior written notice.\n\n"
        "4. Penalty and Liquidated Damages\n"
        "In the event of an intentional unauthorized breach of this Agreement, the breaching party shall pay liquidated damages of $50,000 per occurrence.\n\n"
        "5. Governing Law and Jurisdiction\n"
        "This Agreement shall be governed by and construed under the laws of the State of Delaware, with jurisdiction in Delaware state courts.\n"
    )
    
    rect = pymupdf.Rect(50, 50, 550, 750)
    page.insert_textbox(rect, text, fontsize=11, fontname="helv")
    doc.save(pdf_path)
    doc.close()
    print(f"Generated sample PDF at: {pdf_path}")

def run_tests():
    test_pdf_path = "tests/sample_nda.pdf"
    generate_sample_pdf(test_pdf_path)

    client = TestClient(app)

    # 1. Health check
    print("\n[TEST 1] Testing /health...")
    health_res = client.get("/health")
    assert health_res.status_code == 200, f"Health check failed: {health_res.text}"
    print("Health check response:", health_res.json())

    # 2. Upload contract
    print("\n[TEST 2] Testing /upload...")
    with open(test_pdf_path, "rb") as f:
        upload_res = client.post("/upload", files={"file": ("sample_nda.pdf", f, "application/pdf")})
    assert upload_res.status_code == 200, f"Upload failed: {upload_res.text}"
    upload_data = upload_res.json()
    contract_id = upload_data["id"]
    print(f"Uploaded contract ID: {contract_id}, Total Clauses extracted: {upload_data['total_clauses']}")
    assert upload_data["total_clauses"] >= 5, f"Expected at least 5 clauses, got {upload_data['total_clauses']}"

    # Verify clauses in SQLite
    clauses = db.get_clauses(contract_id)
    print(f"Retrieved {len(clauses)} clauses from SQLite:")
    for c in clauses:
        print(f" - [{c['clause_number']}] {c['heading']}")

    # 3. Test Q&A with known question
    print("\n[TEST 3] Testing /chat with known question...")
    q1 = "What is the penalty for an unauthorized breach?"
    chat_res1 = client.post("/chat", json={"contract_id": contract_id, "question": q1})
    assert chat_res1.status_code == 200, f"Chat failed: {chat_res1.text}"
    ans1 = chat_res1.json()
    print(f"Question: {q1}")
    print(f"Answer: {ans1['answer']}")
    print(f"Verified: {ans1['verified']}")
    print(f"Source clauses cited: {len(ans1['source_clauses'])}")
    assert "50,000" in ans1["answer"] or "fifty thousand" in ans1["answer"].lower(), "Expected $50,000 penalty in answer"
    assert len(ans1["source_clauses"]) > 0, "Expected source clauses for valid answer"

    # 4. Test Q&A with unknown question (verifier rule)
    print("\n[TEST 4] Testing /chat with unknown question (verifier test)...")
    q2 = "What is the employee stock option vesting cliff?"
    chat_res2 = client.post("/chat", json={"contract_id": contract_id, "question": q2})
    assert chat_res2.status_code == 200, f"Chat failed: {chat_res2.text}"
    ans2 = chat_res2.json()
    print(f"Question: {q2}")
    print(f"Answer: {ans2['answer']}")
    print(f"Verified: {ans2['verified']}")
    assert "not found in the document" in ans2["answer"].lower(), "Expected 'Not found in the document' response"

    # 5. Test /history
    print("\n[TEST 5] Testing /history...")
    hist_res = client.get("/history")
    assert hist_res.status_code == 200, f"History failed: {hist_res.text}"
    contracts = hist_res.json()["contracts"]
    assert any(c["id"] == contract_id for c in contracts), "Uploaded contract missing from history"
    print(f"Total contracts in history: {len(contracts)}")

    print("\n==========================================")
    print("ALL STAGE 1 TESTS PASSED SUCCESSFULLY! :)")
    print("==========================================")

if __name__ == "__main__":
    run_tests()
