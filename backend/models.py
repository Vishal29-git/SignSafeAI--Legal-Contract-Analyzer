from pydantic import BaseModel, Field
from typing import List, Optional

class ClauseItem(BaseModel):
    id: Optional[int] = None
    contract_id: str
    clause_number: str
    heading: str
    text: str
    page_number: int
    clause_type: Optional[str] = None
    risk_level: Optional[str] = None
    risk_reason: Optional[str] = None

class ContractResponse(BaseModel):
    id: str
    filename: str
    title: Optional[str] = None
    created_at: str
    status: str
    total_clauses: int

class QARequest(BaseModel):
    contract_id: str
    question: str

class QASourceClause(BaseModel):
    clause_number: str
    heading: str
    text: str
    page_number: Optional[int] = 1

class QAResponse(BaseModel):
    contract_id: str
    question: str
    answer: str
    source_clauses: List[QASourceClause] = []
    verified: bool = True

class ContractHistoryItem(BaseModel):
    id: str
    filename: str
    title: Optional[str] = None
    created_at: str
    status: str
    clause_count: int

class HistoryResponse(BaseModel):
    contracts: List[ContractHistoryItem]

# Multi-Agent Structured Output models
class ClauseClassification(BaseModel):
    clause_id: int
    clause_number: str
    category: str = Field(description='One of: payment, termination, penalty, auto-renewal, non-compete, jurisdiction, other')

class ClauseRisk(BaseModel):
    clause_id: int
    clause_number: str
    risk_level: str = Field(description='Low, Medium, or High')
    reason: str = Field(description='One-line reason for the risk rating')

class SummaryOutput(BaseModel):
    document_title: str
    summary: str

class VerifierCheck(BaseModel):
    clause_id: int
    verified: bool
    proof: str
