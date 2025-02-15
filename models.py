from typing import List, Optional
from pydantic import BaseModel

class Party(BaseModel):
    party_name: str
    role: str

class ClauseMetadata(BaseModel):
    confidence_score: float
    extracted_by: str

class Clause(BaseModel):
    clause_category: str
    clause_name: str
    clause_text: str
    related_dates: List[str]
    amounts: Optional[List[str]] = []  # Optional since some clauses might not have amounts
    metadata: ClauseMetadata

class Contract(BaseModel):
    contract_title: str
    contract_date: str
    parties_involved: List[Party]
    clauses: List[Clause]
    summary: str

class ProcessingResponse(BaseModel):
    status: str
    error: Optional[str] = None
    document: Optional[Contract] = None