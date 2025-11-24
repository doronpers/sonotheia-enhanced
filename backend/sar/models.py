"""
SAR (Suspicious Activity Report) Data Models
Pydantic models for SAR generation and validation
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Optional
from datetime import date as date_type
import sys
from pathlib import Path
import re

# Add parent to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from config.constants import SAFE_ID_PATTERN, VALID_CHANNELS, MAX_AUDIO_SIZE_BYTES


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
        if v and len(v) > 200:
            raise ValueError(f"{info.field_name} exceeds maximum length of 200 characters")
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
    
    @field_validator('red_flags')
    @classmethod
    def validate_red_flags_length(cls, v):
        if len(v) > 50:
            raise ValueError("Too many red flags (maximum 50)")
        if any(len(flag) > 200 for flag in v):
            raise ValueError("Each red flag must be 200 characters or less")
        return v
    
    @field_validator('customer_name', 'customer_id', 'account_number', 'occupation', 'pattern', 'doc_id')
    @classmethod
    def validate_string_fields(cls, v, info):
        if len(v) > 200:
            raise ValueError(f"{info.field_name} exceeds maximum length of 200 characters")
        return v
    
    @field_validator('suspicious_activity')
    @classmethod
    def validate_activity_length(cls, v):
        if len(v) > 1000:
            raise ValueError("Suspicious activity description exceeds maximum length of 1000 characters")
        return v
    
    @field_validator('transactions')
    @classmethod
    def validate_transactions_count(cls, v):
        if len(v) > 1000:
            raise ValueError("Too many transactions (maximum 1000)")
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
        if not v.isupper() or not v.isalpha() or len(v) != 2:
            raise ValueError("Country code must be 2 uppercase letters (e.g., US, GB)")
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
