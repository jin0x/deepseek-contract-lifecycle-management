from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime

class ClauseCategory(str, Enum):
    # Core Business Terms
    PAYMENT = "PAYMENT"  # Payment terms, pricing, fees, invoicing
    SERVICES = "SERVICES"  # Scope of services/deliverables
    TERM_LENGTH = "TERM_LENGTH"  # Contract duration, renewal terms

    # Rights and Restrictions
    INTELLECTUAL_PROPERTY = "INTELLECTUAL_PROPERTY"  # IP rights, ownership, licensing
    CONFIDENTIALITY = "CONFIDENTIALITY"  # NDAs, trade secrets, data protection
    NON_COMPETE = "NON_COMPETE"  # Competition restrictions, exclusivity

    # Risk and Compliance
    LIABILITY = "LIABILITY"  # Limitations of liability, indemnification
    WARRANTY = "WARRANTY"  # Warranties, representations, disclaimers
    COMPLIANCE = "COMPLIANCE"  # Regulatory compliance, certifications
    DATA_PRIVACY = "DATA_PRIVACY"  # Data handling, privacy requirements

    # Operational
    TERMINATION = "TERMINATION"  # Termination rights, process
    PERFORMANCE = "PERFORMANCE"  # Performance standards, SLAs
    FORCE_MAJEURE = "FORCE_MAJEURE"  # Force majeure events
    NOTICE = "NOTICE"  # Notice requirements, communication

    # Resolution
    DISPUTE_RESOLUTION = "DISPUTE_RESOLUTION"  # Dispute handling, arbitration
    GOVERNING_LAW = "GOVERNING_LAW"  # Choice of law, jurisdiction

    # Administrative
    DEFINITIONS = "DEFINITIONS"  # Term definitions
    ASSIGNMENT = "ASSIGNMENT"  # Transfer rights, delegation
    AMENDMENT = "AMENDMENT"  # Modification procedures
    MISCELLANEOUS = "MISCELLANEOUS"  # General/boilerplate provisions

class ClauseMetadata(BaseModel):
    confidence_score: float = Field(..., description="Confidence score of the clause extraction and classification")
    processing_date: datetime = Field(default_factory=datetime.now, description="When the clause was processed")
    warnings: List[str] = Field(default_factory=list, description="Any warnings or flags during processing")

class Clause(BaseModel):
    clause_category: ClauseCategory = Field(..., description="Category of the clause")
    clause_name: str = Field(..., description="Name or title of the clause")
    section_name: Optional[str] = Field(None, description="Name of the section containing this clause")
    clause_text: str = Field(..., description="Full text content of the clause")
    related_dates: List[str] = Field(default_factory=list, description="Dates mentioned in the clause")
    related_amounts: Optional[List[str]] = Field(None, description="Monetary amounts mentioned in the clause")
    metadata: ClauseMetadata = Field(..., description="Metadata about the clause processing")

class Party(BaseModel):
    party_name: str = Field(..., description="Name of the party")
    role: str = Field(..., description="Role of the party in the contract")

class Contract(BaseModel):
    pdf_name: str = Field(..., description="Name of the processed PDF file")
    contract_title: str = Field(..., description="Title of the contract")
    contract_date: str = Field(..., description="Effective date of the contract")
    parties_involved: List[Party] = Field(..., description="Parties involved in the contract")
    clauses: List[Clause] = Field(..., description="List of contract clauses")
    summary: str = Field(..., description="Executive summary of the contract")
    amounts: Optional[List[float]] = Field(None, description="Key monetary amounts in the contract")
    processing_date: datetime = Field(default_factory=datetime.now, description="When the contract was processed")
    confidence_score: float = Field(..., description="Overall confidence score of the processing")

class ProcessingResponse(BaseModel):
    status: str = Field(..., description="Status of the processing (success/error)")
    error: Optional[str] = Field(None, description="Error message if processing failed")
    document: Optional[Contract] = Field(None, description="Processed contract data")