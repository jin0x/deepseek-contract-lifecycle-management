from typing import List, Optional
from pydantic import BaseModel

class Party(BaseModel):
    party_name: str
    role: str

class ClauseMetadata(BaseModel):
    confidence_score: float
    extracted_by: str

class Clause(BaseModel):
    clause: int
    section_name: Optional[str]
    clause_text: str
    related_dates: List[str]
    related_amounts: Optional[List[str]]
    metadata: ClauseMetadata

class Contract(BaseModel):
    pdf_name: str
    contract_title: str
    contract_date: str
    parties_involved: List[Party]
    clauses: List[Clause]
    summary: str
    amounts: Optional[List[float]]

class ProcessingResponse(BaseModel):
    status: str
    error: Optional[str]
    document: Optional[Contract]