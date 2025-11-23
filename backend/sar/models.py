"""
SAR (Suspicious Activity Report) Data Models
Pydantic models for SAR generation and validation
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date


class SARTransaction(BaseModel):
    """Individual transaction in a SAR report"""
    transaction_id: str
    date: date
    type: str
    amount: float
    destination: Optional[str] = None


class SARContext(BaseModel):
    """Context data for generating SAR narrative"""
    customer_name: str
    customer_id: str
    account_number: str
    account_opened: date
    occupation: str
    suspicious_activity: str
    start_date: date
    end_date: date
    count: int
    amount: float
    pattern: str
    red_flags: List[str]
    transactions: List[SARTransaction]
    doc_id: str


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
