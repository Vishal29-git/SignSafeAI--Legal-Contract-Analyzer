import os
import uuid
import json
import asyncio
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, UploadFile, File, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse

from backend.config import settings
from backend.models import (
    ContractResponse,
    ClauseItem,
    QARequest,
    QAResponse,
    HistoryResponse,
    ContractHistoryItem
)
import backend.db as db
from backend.ingest import ingest_pdf
from backend.agents.qa import answer_contract_question
from backend.agents.classifier import classify_clauses
from backend.agents.risk_analysis import analyze_clause_risks
from backend.agents.summary import summarize_contract
from backend.agents.verifier import verify_analysis

app = FastAPI(
    title="Legal Contract Analyzer API",
    description="Privacy-first, offline legal contract analysis with local LLMs and ChromaDB.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "llm_model": settings.LLM_MODEL,
        "embed_model": settings.EMBED_MODEL,
        "temperature": settings.TEMPERATURE,
        "ollama_url": settings.OLLAMA_BASE_URL
    }

@app.post("/upload", response_model=ContractResponse)
async def upload_contract(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported."
        )

    contract_id = str(uuid.uuid4())
    safe_filename = Path(file.filename).name
    destination_path = settings.UPLOADS_DIR / f"{contract_id}_{safe_filename}"

    try:
        with open(destination_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )

    contract = db.create_contract(
        contract_id=contract_id,
        filename=safe_filename,
        file_path=str(destination_path),
        title=safe_filename.replace(".pdf", ""),
        status="processing"
    )

    try:
        clauses = ingest_pdf(str(destination_path), contract_id)
    except Exception as e:
        db.update_contract(contract_id, status="error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest contract: {str(e)}"
        )

    return ContractResponse(
        id=contract_id,
        filename=safe_filename,
        title=contract.get("title"),
        created_at=contract.get("created_at"),
        status="ingested",
        total_clauses=len(clauses)
    )

@app.get("/analyze/{contract_id}/stream")
async def analyze_stream(contract_id: str, request: Request):
    """
    Robust Server-Sent Events stream with:
    - Checkpoint resumption (never repeats already-completed steps)
    - Keep-alive heartbeats every 4s to prevent connection timeouts
    """
    contract = db.get_contract(contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    async def event_generator():
        clauses = db.get_clauses(contract_id)
        if not clauses:
            yield {
                "event": "step_fail",
                "data": json.dumps({"step": "init", "error": "No clauses extracted for contract."})
            }
            return

        pipeline_steps = [
            ("classifier", "Classifier"),
            ("risk_analysis", "Risk Analysis"),
            ("summary", "Summary"),
            ("verifier", "Verifier")
        ]

        # Check existing state in SQLite to resume instantly without repeating
        existing_analysis = db.get_analysis(contract_id)
        existing_classifications = [
            {"clause_id": c["id"], "category": c["clause_type"]}
            for c in clauses if c.get("clause_type")
        ]
        existing_risks = [
            {"clause_id": c["id"], "risk_level": c["risk_level"], "reason": c.get("risk_reason", "")}
            for c in clauses if c.get("risk_level")
        ]

        state = {
            "contract_id": contract_id,
            "filename": contract["filename"],
            "clauses": clauses,
            "classifications": existing_classifications,
            "risk_ratings": existing_risks,
            "summary_data": {
                "document_title": existing_analysis["document_title"],
                "summary": existing_analysis["summary"]
            } if existing_analysis else {},
            "verification_data": {}
        }

        for step_key, step_title in pipeline_steps:
            if await request.is_disconnected():
                break

            yield {
                "event": "step_start",
                "data": json.dumps({"step": step_key, "name": step_title})
            }

            try:
                # 1. Classifier Step
                if step_key == "classifier":
                    if len(state["classifications"]) >= len(clauses):
                        result = state["classifications"]
                    else:
                        task = asyncio.create_task(asyncio.to_thread(classify_clauses, contract_id, state["clauses"]))
                        while not task.done():
                            done, _ = await asyncio.wait({task}, timeout=3.0)
                            if not done:
                                yield {"event": "ping", "data": "processing"}
                        result = await task
                        state["classifications"] = result

                # 2. Risk Analysis Step
                elif step_key == "risk_analysis":
                    if len(state["risk_ratings"]) >= len(clauses):
                        result = state["risk_ratings"]
                    else:
                        task = asyncio.create_task(asyncio.to_thread(analyze_clause_risks, contract_id, state["clauses"]))
                        while not task.done():
                            done, _ = await asyncio.wait({task}, timeout=3.0)
                            if not done:
                                yield {"event": "ping", "data": "processing"}
                        result = await task
                        state["risk_ratings"] = result

                # 3. Summary Step
                elif step_key == "summary":
                    if state["summary_data"].get("summary"):
                        result = state["summary_data"]
                    else:
                        task = asyncio.create_task(asyncio.to_thread(summarize_contract, contract_id, state["filename"], state["clauses"]))
                        while not task.done():
                            done, _ = await asyncio.wait({task}, timeout=3.0)
                            if not done:
                                yield {"event": "ping", "data": "processing"}
                        result = await task
                        state["summary_data"] = result

                # 4. Verifier Step
                elif step_key == "verifier":
                    task = asyncio.create_task(
                        asyncio.to_thread(
                            verify_analysis,
                            contract_id,
                            state["clauses"],
                            state["summary_data"],
                            state["risk_ratings"]
                        )
                    )
                    while not task.done():
                        done, _ = await asyncio.wait({task}, timeout=3.0)
                        if not done:
                            yield {"event": "ping", "data": "processing"}
                    result = await task
                    state["verification_data"] = result

                yield {
                    "event": "step_finish",
                    "data": json.dumps({
                        "step": step_key,
                        "name": step_title,
                        "result": result
                    })
                }

            except Exception as e:
                yield {
                    "event": "step_fail",
                    "data": json.dumps({
                        "step": step_key,
                        "name": step_title,
                        "error": str(e)
                    })
                }
                return

        db.update_contract(contract_id, status="analyzed")
        
        yield {
            "event": "pipeline_complete",
            "data": json.dumps({
                "status": "completed",
                "contract_id": contract_id,
                "summary": state["summary_data"],
                "verification": state["verification_data"]
            })
        }

    return EventSourceResponse(event_generator())

@app.post("/chat", response_model=QAResponse)
async def chat_qa(req: QARequest):
    contract = db.get_contract(req.contract_id)
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found."
        )

    result = answer_contract_question(req.contract_id, req.question)
    return QAResponse(**result)

@app.get("/history", response_model=HistoryResponse)
def get_history():
    contracts = db.list_contracts()
    items = [
        ContractHistoryItem(
            id=c["id"],
            filename=c["filename"],
            title=c.get("title") or c["filename"],
            created_at=c["created_at"],
            status=c["status"],
            clause_count=c.get("clause_count", 0)
        )
        for c in contracts
    ]
    return HistoryResponse(contracts=items)

@app.get("/contract/{contract_id}")
def get_contract_details(contract_id: str):
    contract = db.get_contract(contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
        
    clauses = db.get_clauses(contract_id)
    analysis = db.get_analysis(contract_id)
    chat_history = db.get_chat_history(contract_id)
    
    return {
        "contract": contract,
        "clauses": clauses,
        "analysis": analysis,
        "chat_history": chat_history
    }
