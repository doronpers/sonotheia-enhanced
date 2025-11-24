"""
Input Validation and Sanitization
Security-focused validation for all API inputs
"""

import re
from typing import Optional, Any
import logging
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from config.constants import (
    SAFE_ID_PATTERN,
    SAFE_STRING_PATTERN,
    EMAIL_PATTERN,
    COUNTRY_CODE_PATTERN,
    VALID_CHANNELS,
    MAX_AUDIO_SIZE_BYTES,
    MAX_ID_LENGTH,
    MAX_STRING_LENGTH,
    MAX_TEXT_LENGTH
)

logger = logging.getLogger(__name__)

# Dangerous patterns to reject
SQL_INJECTION_PATTERNS = [
    r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
    r"(--|\;|\/\*|\*\/)",
    r"(\bOR\b.*=.*)",
    r"(\bAND\b.*=.*)",
]

XSS_PATTERNS = [
    r"<script",
    r"javascript:",
    r"onerror=",
    r"onload=",
    r"eval\(",
]

PATH_TRAVERSAL_PATTERNS = [
    r"\.\.",
    r"\/\.\.",
    r"\.\.\/"
]


class ValidationError(ValueError):
    """Custom validation error"""
    pass


def sanitize_string(value: str, max_length: int = 500) -> str:
    """
    Sanitize a string input by removing potentially dangerous characters
    """
    if not value:
        return value
    
    # Trim to max length
    value = value[:max_length]
    
    # Remove null bytes
    value = value.replace('\x00', '')
    
    # Remove control characters except newline and tab
    value = ''.join(char for char in value if ord(char) >= 32 or char in '\n\t')
    
    return value.strip()


def validate_id(value: str, field_name: str = "id") -> str:
    """
    Validate an ID field (transaction ID, customer ID, etc.)
    """
    if not value:
        raise ValidationError(f"{field_name} cannot be empty")
    
    # Check length before sanitization
    if len(value) > MAX_ID_LENGTH:
        raise ValidationError(f"{field_name} exceeds maximum length of {MAX_ID_LENGTH} characters")
    
    value = sanitize_string(value, max_length=MAX_ID_LENGTH)
    
    if not SAFE_ID_PATTERN.match(value):
        raise ValidationError(
            f"{field_name} must contain only alphanumeric characters, "
            f"hyphens, and underscores (max {MAX_ID_LENGTH} chars)"
        )
    
    return value


def validate_amount(value: float, min_amount: float = 0.01, max_amount: float = 1000000000) -> float:
    """
    Validate a monetary amount
    """
    if value < min_amount:
        raise ValidationError(f"Amount must be at least {min_amount}")
    
    if value > max_amount:
        raise ValidationError(f"Amount cannot exceed {max_amount}")
    
    # Check for reasonable precision (max 2 decimal places for USD)
    if round(value, 2) != value:
        raise ValidationError("Amount must have at most 2 decimal places")
    
    return value


def validate_country_code(value: str) -> str:
    """
    Validate a 2-letter country code
    """
    if not value:
        return value
    
    value = value.upper()
    
    if not COUNTRY_CODE_PATTERN.match(value):
        raise ValidationError("Country code must be a 2-letter ISO code (e.g., US, GB)")
    
    return value


def check_sql_injection(value: str) -> None:
    """
    Check for SQL injection patterns
    """
    if not value:
        return
    
    value_upper = value.upper()
    
    for pattern in SQL_INJECTION_PATTERNS:
        if re.search(pattern, value_upper, re.IGNORECASE):
            logger.warning(f"Potential SQL injection detected: {pattern}")
            raise ValidationError("Invalid input: potentially dangerous pattern detected")


def check_xss(value: str) -> None:
    """
    Check for XSS patterns
    """
    if not value:
        return
    
    value_lower = value.lower()
    
    for pattern in XSS_PATTERNS:
        if re.search(pattern, value_lower, re.IGNORECASE):
            logger.warning(f"Potential XSS detected: {pattern}")
            raise ValidationError("Invalid input: potentially dangerous pattern detected")


def check_path_traversal(value: str) -> None:
    """
    Check for path traversal patterns
    """
    if not value:
        return
    
    for pattern in PATH_TRAVERSAL_PATTERNS:
        if re.search(pattern, value):
            logger.warning(f"Potential path traversal detected: {pattern}")
            raise ValidationError("Invalid input: potentially dangerous pattern detected")


def validate_text_input(value: str, field_name: str = "input", max_length: int = 500) -> str:
    """
    Comprehensive text input validation
    """
    if not value:
        return value
    
    # Check length before sanitization
    if len(value) > max_length:
        raise ValidationError(f"{field_name} exceeds maximum length of {max_length} characters")
    
    # Sanitize
    value = sanitize_string(value, max_length=max_length)
    
    # Check for dangerous patterns
    check_sql_injection(value)
    check_xss(value)
    check_path_traversal(value)
    
    return value


def validate_email(value: str) -> str:
    """
    Validate an email address
    """
    if not value:
        return value
    
    value = value.lower().strip()
    
    if not EMAIL_PATTERN.match(value):
        raise ValidationError("Invalid email address format")
    
    if len(value) > 254:  # RFC 5321
        raise ValidationError("Email address too long")
    
    return value


def validate_channel(value: str) -> str:
    """
    Validate a transaction channel
    """
    valid_channels = [
        "wire_transfer",
        "ach",
        "mobile",
        "web",
        "branch",
        "atm",
        "phone"
    ]
    
    value = value.lower().strip()
    
    if value not in valid_channels:
        raise ValidationError(
            f"Invalid channel. Must be one of: {', '.join(valid_channels)}"
        )
    
    return value


def validate_base64_audio(value: Optional[str]) -> Optional[str]:
    """
    Validate base64-encoded audio data
    """
    if not value:
        return value
    
    # Check if it looks like base64
    import base64
    
    try:
        # Try to decode
        decoded = base64.b64decode(value, validate=True)
        
        # Check size (max 10MB)
        if len(decoded) > 10 * 1024 * 1024:
            raise ValidationError("Audio data exceeds maximum size of 10MB")
        
        # Basic sanity check - should have some length
        if len(decoded) < 100:
            raise ValidationError("Audio data too small to be valid")
        
        return value
        
    except Exception as e:
        raise ValidationError(f"Invalid base64 audio data: {str(e)}")


def validate_device_info(value: Optional[dict]) -> Optional[dict]:
    """
    Validate device information dictionary
    """
    if not value:
        return value
    
    if not isinstance(value, dict):
        raise ValidationError("Device info must be a dictionary")
    
    # Validate each field if present
    allowed_fields = {
        'device_id', 'ip_address', 'user_agent', 
        'os', 'browser', 'device_type'
    }
    
    for key in value.keys():
        if key not in allowed_fields:
            logger.warning(f"Unexpected device info field: {key}")
    
    # Validate specific fields
    if 'device_id' in value:
        value['device_id'] = validate_id(str(value['device_id']), "device_id")
    
    if 'user_agent' in value:
        value['user_agent'] = validate_text_input(
            str(value['user_agent']), 
            "user_agent", 
            max_length=500
        )
    
    return value

