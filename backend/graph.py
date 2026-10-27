from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, START, END

from backend.agents.classifier import classify_clauses
from backend.agents.risk_analysis import analyze_clause_risks
from backend.agents.summary import summarize_contract
from backend.agents.verifier import verify_analysis
from backend.db import get_contract, get_clauses

class AgentPipelineGraphState(TypedDict):
    contract_id: str
    filename: str
    clauses: List[Dict[str, Any]]
    classifications: List[Dict[str, Any]]
    risk_ratings: List[Dict[str, Any]]
    summary_data: Dict[str, Any]
    verification_data: Dict[str, Any]
    errors: List[str]

def classifier_node(state: AgentPipelineGraphState) -> Dict[str, Any]:
    contract_id = state["contract_id"]
    clauses = state.get("clauses") or get_clauses(contract_id)
    classifications = classify_clauses(contract_id, clauses)
    return {"classifications": classifications}

def risk_analysis_node(state: AgentPipelineGraphState) -> Dict[str, Any]:
    contract_id = state["contract_id"]
    clauses = state.get("clauses") or get_clauses(contract_id)
    risks = analyze_clause_risks(contract_id, clauses)
    return {"risk_ratings": risks}

def summary_node(state: AgentPipelineGraphState) -> Dict[str, Any]:
    contract_id = state["contract_id"]
    clauses = state.get("clauses") or get_clauses(contract_id)
    filename = state.get("filename", "contract.pdf")
    summary_res = summarize_contract(contract_id, filename, clauses)
    return {"summary_data": summary_res}

def verifier_node(state: AgentPipelineGraphState) -> Dict[str, Any]:
    contract_id = state["contract_id"]
    clauses = state.get("clauses") or get_clauses(contract_id)
    summary_res = state.get("summary_data", {})
    risks = state.get("risk_ratings", [])
    verification_res = verify_analysis(contract_id, clauses, summary_res, risks)
    return {"verification_data": verification_res}

def build_contract_pipeline():
    builder = StateGraph(AgentPipelineGraphState)
    
    builder.add_node("classifier", classifier_node)
    builder.add_node("risk_analysis", risk_analysis_node)
    builder.add_node("summary", summary_node)
    builder.add_node("verifier", verifier_node)

    builder.add_edge(START, "classifier")
    builder.add_edge("classifier", "risk_analysis")
    builder.add_edge("risk_analysis", "summary")
    builder.add_edge("summary", "verifier")
    builder.add_edge("verifier", END)

    return builder.compile()

pipeline_runner = build_contract_pipeline()
