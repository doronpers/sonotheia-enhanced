"""
SAR (Suspicious Activity Report) Data Models
Pydantic models for SAR generation and validation
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Optional
from datetime import date as date_type, datetime
from enum import Enum
import sys
from pathlib import Path
import re

# Add parent to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from config.constants import (
    SAFE_ID_PATTERN, 
    VALID_CHANNELS, 
    MAX_AUDIO_SIZE_BYTES,
    MAX_STRING_LENGTH,
    MAX_TEXT_LENGTH,
    MAX_RED_FLAGS,
    MAX_TRANSACTIONS
)


# Define enums and helper models first (before they're used)
class FilingStatus(str, Enum):
    """SAR filing status"""
    DRAFT = "draft"
    PENDING = "pending"
    FILED = "filed"
    REJECTED = "rejected"


class RiskIntelligence(BaseModel):
    """Risk intelligence for SAR"""
    risk_score: float = Field(default=0.5, ge=0.0, le=1.0)
    risk_level: str = Field(default="MEDIUM")
    indicators: List[str] = Field(default_factory=list)


class KnownScheme(BaseModel):
    """Known fraud scheme"""
    name: str
    description: str
    confidence: float = Field(ge=0.0, le=1.0)


class SARTransaction(BaseModel):
    """Individual transaction in a SAR report"""
    model_config = ConfigDict(populate_by_name=True)
    
    transaction_id: str = Field(..., description="Transaction identifier")
    date: date_type = Field(..., description="Transaction date")
    transaction_type: str = Field(..., description="Transaction type", alias="type")
    amount: float = Field(..., gt=0, le=1000000000, description="Transaction amount")
    destination: Optional[str] = Field(None, description="Transaction destination")
    
    @field_validator('transaction_id', 'transaction_type', 'destination')
    @classmethod
    def validate_string_length(cls, v, info):
        if v and len(v) > MAX_STRING_LENGTH:
            raise ValueError(f"{info.field_name} exceeds maximum length of {MAX_STRING_LENGTH} characters")
        return v


class SARContext(BaseModel):
    """Context data for generating SAR narrative"""
    customer_name: str = Field(..., description="Customer full name")
    customer_id: str = Field(..., description="Customer identifier")
    account_number: str = Field(..., description="Account number")
    account_opened: date_type = Field(..., description="Account opening date")
    occupation: str = Field(..., description="Customer occupation")
    suspicious_activity: str = Field(..., description="Description of suspicious activity")
    start_date: date_type = Field(..., description="Activity start date")
    end_date: date_type = Field(..., description="Activity end date")
    count: int = Field(..., gt=0, le=10000, description="Number of suspicious transactions")
    amount: float = Field(..., gt=0, le=1000000000, description="Total amount involved")
    pattern: str = Field(..., description="Pattern of suspicious activity")
    red_flags: List[str] = Field(..., description="List of red flags identified")
    transactions: List[SARTransaction] = Field(..., description="List of transactions")
    doc_id: str = Field(..., description="Document identifier")
    risk_intelligence: Optional[RiskIntelligence] = Field(default=None, description="Risk intelligence data")
    filing_status: FilingStatus = Field(default=FilingStatus.DRAFT, description="Filing status")
    
    @field_validator('red_flags')
    @classmethod
    def validate_red_flags_length(cls, v):
        if len(v) > MAX_RED_FLAGS:
            raise ValueError(f"Too many red flags (maximum {MAX_RED_FLAGS})")
        if any(len(flag) > MAX_STRING_LENGTH for flag in v):
            raise ValueError(f"Each red flag must be {MAX_STRING_LENGTH} characters or less")
        return v
    
    @field_validator('customer_name', 'customer_id', 'account_number', 'occupation', 'pattern', 'doc_id')
    @classmethod
    def validate_string_fields(cls, v, info):
        if len(v) > MAX_STRING_LENGTH:
            raise ValueError(f"{info.field_name} exceeds maximum length of {MAX_STRING_LENGTH} characters")
        return v
    
    @field_validator('suspicious_activity')
    @classmethod
    def validate_activity_length(cls, v):
        if len(v) > MAX_TEXT_LENGTH:
            raise ValueError(f"Suspicious activity description exceeds maximum length of {MAX_TEXT_LENGTH} characters")
        return v
    
    @field_validator('transactions')
    @classmethod
    def validate_transactions_count(cls, v):
        if len(v) > MAX_TRANSACTIONS:
            raise ValueError(f"Too many transactions (maximum {MAX_TRANSACTIONS})")
        return v


class AuthenticationRequest(BaseModel):
    """Request model for authentication"""
    transaction_id: str = Field(..., description="Transaction identifier")
    customer_id: str = Field(..., description="Customer identifier")
    amount_usd: float = Field(..., gt=0, le=1000000000, description="Transaction amount in USD")
    voice_sample: Optional[str] = Field(None, description="Base64 encoded audio sample")
    device_info: Optional[dict] = Field(None, description="Device information")
    channel: str = Field(default="wire_transfer", description="Transaction channel")
    destination_country: str = Field(default="US", description="Destination country code (2-letter ISO)", min_length=2, max_length=2)
    is_new_beneficiary: bool = Field(default=True, description="Whether beneficiary is new")
    
    @field_validator('transaction_id', 'customer_id')
    @classmethod
    def validate_ids(cls, v, info):
        if len(v) > 100:
            raise ValueError(f"{info.field_name} exceeds maximum length of 100 characters")
        if not re.match(r'^[a-zA-Z0-9_\-]+$', v):
            raise ValueError(f"{info.field_name} must contain only alphanumeric characters, hyphens, and underscores")
        return v
    
    @field_validator('channel')
    @classmethod
    def validate_channel_value(cls, v):
        if v.lower() not in VALID_CHANNELS:
            raise ValueError(f"Channel must be one of: {', '.join(VALID_CHANNELS)}")
        return v.lower()
    
    @field_validator('destination_country')
    @classmethod
    def validate_country_format(cls, v):
        # Normalize to uppercase for consistency
        v = v.upper()
        if not v.isalpha() or len(v) != 2:
            raise ValueError("Country code must be 2 letters (e.g., US, GB)")
        return v
    
    @field_validator('voice_sample')
    @classmethod
    def validate_voice_data(cls, v):
        if v and len(v) > MAX_AUDIO_SIZE_BYTES:
            raise ValueError(f"Voice sample exceeds maximum size of {MAX_AUDIO_SIZE_BYTES // (1024*1024)}MB")
        return v


class AuthenticationResponse(BaseModel):
    """Response model for authentication"""
    decision: str  # APPROVE, DECLINE, STEP_UP, MANUAL_REVIEW
    confidence: float
    risk_score: float
    risk_level: str
    factor_results: dict
    transaction_risk: dict
    sar_flags: List[str]


class SARReport(BaseModel):
    """Complete SAR Report"""
    sar_id: str
    context: SARContext
    narrative: str
    generated_at: datetime = Field(default_factory=datetime.now)
    quality_score: float = Field(default=1.0, ge=0.0, le=1.0)
    ready_for_filing: bool = Field(default=True)
    filing_status: FilingStatus = Field(default=FilingStatus.DRAFT)
