"""
SAR (Suspicious Activity Report) Data Models
Pydantic models for SAR generation and validation
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import date, datetime
from enum import Enum


class FilingStatus(str, Enum):
    """SAR filing status"""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    FILED = "filed"
    REJECTED = "rejected"


class SARTransaction(BaseModel):
    """Individual transaction in a SAR report"""
    transaction_id: str
    date: date
    type: str
    amount: float
    destination: Optional[str] = None
    source: Optional[str] = None
    currency: str = "USD"
    reference_number: Optional[str] = None
    risk_indicators: List[str] = Field(default_factory=list)


class InvestigationDetails(BaseModel):
    """Investigation details for SAR"""
    investigation_id: str
    investigator_name: str
    investigator_title: str = "Compliance Officer"
    investigation_start_date: date
    customer_contacted: bool = True
    customer_response: Optional[str] = None
    additional_documentation: List[str] = Field(default_factory=list)
    external_sources_checked: List[str] = Field(default_factory=list)
    law_enforcement_notified: bool = False


class KnownScheme(BaseModel):
    """Known fraud scheme pattern"""
    name: str
    similarity_score: float
    description: str


class RiskIntelligence(BaseModel):
    """Risk intelligence analysis for SAR"""
    overall_risk_score: float = Field(ge=0.0, le=1.0)
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    pattern_analysis: Dict[str, float] = Field(default_factory=dict)
    behavioral_anomalies: List[str] = Field(default_factory=list)
    geographic_risks: List[str] = Field(default_factory=list)
    temporal_patterns: List[str] = Field(default_factory=list)
    related_entities: List[str] = Field(default_factory=list)
    similarity_to_known_schemes: List[KnownScheme] = Field(default_factory=list)


class SARContext(BaseModel):
    """Context data for generating SAR narrative"""
    # Basic customer info
    customer_name: str
    customer_id: str
    account_number: str
    account_opened: date
    occupation: str
    
    # Suspicious activity details
    suspicious_activity: str
    start_date: date
    end_date: date
    count: int
    amount: float
    pattern: str
    red_flags: List[str]
    transactions: List[SARTransaction]
    
    # Enhanced fields
    investigation_details: Optional[InvestigationDetails] = None
    risk_intelligence: Optional[RiskIntelligence] = None
    filing_status: FilingStatus = FilingStatus.DRAFT
    priority_level: str = "MEDIUM"  # LOW, MEDIUM, HIGH, URGENT
    
    # Document references
    doc_id: str
    supporting_documents: List[str] = Field(default_factory=list)
    
    # Compliance tracking
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    reviewed_by: Optional[str] = None
    approved_by: Optional[str] = None


class SARReport(BaseModel):
    """Complete SAR report with narrative and metadata"""
    sar_id: str
    context: SARContext
    narrative: str
    quality_score: float
    ready_for_filing: bool
    generated_at: datetime = Field(default_factory=datetime.now)
    filed_at: Optional[datetime] = None


class AuthenticationRequest(BaseModel):
    """Request model for authentication"""
    transaction_id: str
    customer_id: str
    amount_usd: float
    voice_sample: Optional[str] = None  # base64 encoded
    device_info: Optional[dict] = None
    channel: str = "wire_transfer"
    destination_country: str = "US"  # Default for demo purposes
    is_new_beneficiary: bool = True  # Default for demo purposes


class AuthenticationResponse(BaseModel):
    """Response model for authentication"""
    decision: str  # APPROVE, DECLINE, STEP_UP, MANUAL_REVIEW
    confidence: float
    risk_score: float
    risk_level: str
    factor_results: dict
    transaction_risk: dict
    sar_flags: List[str]
