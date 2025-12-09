"""
Input Validation and Sanitization
Security-focused validation for all API inputs
"""

import re
from typing import Optional, Any, Dict
from pydantic import BaseModel
import logging
import sys
from pathlib import Path
import base64
import struct

# Add parent to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from config.constants import (
    SAFE_ID_PATTERN,
    EMAIL_PATTERN,
    COUNTRY_CODE_PATTERN,
    VALID_CHANNELS,
    MAX_AUDIO_SIZE_BYTES,
    MAX_ID_LENGTH
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
    value = value.lower().strip()
    
    if value not in VALID_CHANNELS:
        raise ValidationError(
            f"Invalid channel. Must be one of: {', '.join(VALID_CHANNELS)}"
        )
    
    return value


def validate_base64_audio(value: Optional[str]) -> Optional[str]:
    """
    Validate base64-encoded audio data with magic byte checking
    Security: Validates actual file type to prevent arbitrary file uploads
    """
    if not value:
        return value

    # Check if it looks like base64
    import base64

    try:
        # Try to decode
        decoded = base64.b64decode(value, validate=True)

        # Check size (use constant)
        if len(decoded) > MAX_AUDIO_SIZE_BYTES:
            raise ValidationError(f"Audio data exceeds maximum size of {MAX_AUDIO_SIZE_BYTES // (1024*1024)}MB")

        # Basic sanity check - should have some length
        if len(decoded) < 100:
            raise ValidationError("Audio data too small to be valid")

        # Security: Validate file type by magic bytes (file signature)
        # Common audio formats magic bytes
        audio_magic_bytes = [
            b'RIFF',           # WAV
            b'ID3',            # MP3 with ID3
            b'\xFF\xFB',       # MP3 (MPEG-1 Layer 3)
            b'\xFF\xF3',       # MP3 (MPEG-1 Layer 3)
            b'\xFF\xF2',       # MP3 (MPEG-2 Layer 3)
            b'OggS',           # OGG/Vorbis/Opus
            b'fLaC',           # FLAC
            b'\x1A\x45\xDF\xA3',  # WebM/MKA (Matroska)
        ]

        # Check if file starts with any valid audio magic bytes
        is_valid_audio = any(decoded.startswith(magic) for magic in audio_magic_bytes)

        if not is_valid_audio:
            # Additional check for WAV files (RIFF...WAVE)
            if decoded.startswith(b'RIFF') and len(decoded) > 12:
                if decoded[8:12] == b'WAVE':
                    is_valid_audio = True

        if not is_valid_audio:
            raise ValidationError("Invalid audio file format. Only audio files are accepted.")

        return value

    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(f"Invalid base64 audio data: {str(e)}")


def decode_base64_audio(value: str) -> bytes:
    """
    Decode base64-encoded audio string and return raw bytes.
    Raises ValidationError when invalid.
    """
    if not value:
        raise ValidationError("No audio data provided")

    try:
        decoded = base64.b64decode(value, validate=True)
        return decoded
    except Exception as e:
        logger.error("Failed to decode base64 audio", exc_info=True)
        raise ValidationError(f"Invalid base64 audio data: {e}")


def get_wav_info(decoded: bytes) -> Optional[Dict[str, Any]]:
    """
    Extract WAV file info (sample_rate, byte_rate, channels, bits_per_sample, data_size, duration) from raw bytes.
    Returns None for non-WAV formats.
    """
    if not decoded or len(decoded) < 44:
        return None

    # Check RIFF/WAVE header
    if not (decoded.startswith(b'RIFF') and decoded[8:12] == b'WAVE'):
        return None

    i = 12
    fmt_info = None
    data_size = None
    byte_rate = None

    # Parse chunks
    try:
        while i + 8 <= len(decoded):
            chunk_id = decoded[i:i+4]
            chunk_size = struct.unpack('<I', decoded[i+4:i+8])[0]
            chunk_data_start = i + 8

            if chunk_id == b'fmt ':
                # fmt chunk: audio format (2), channels (2), sample_rate (4), byte_rate (4), block_align (2), bits_per_sample (2)
                fmt_raw = decoded[chunk_data_start:chunk_data_start+16]
                if len(fmt_raw) >= 16:
                    audio_format, num_channels, sample_rate, byte_rate, block_align, bits_per_sample = struct.unpack('<HHIIHH', fmt_raw[:16])
                    fmt_info = {
                        'audio_format': audio_format,
                        'num_channels': num_channels,
                        'sample_rate': sample_rate,
                        'byte_rate': byte_rate,
                        'block_align': block_align,
                        'bits_per_sample': bits_per_sample
                    }
            elif chunk_id == b'data':
                # chunk_size is the size of the data
                data_size = chunk_size

            # Move to next chunk (8-byte header + chunk_size, padded to even)
            i = chunk_data_start + chunk_size
            if chunk_size % 2 == 1:
                i += 1

        if fmt_info and data_size and fmt_info.get('byte_rate'):
            return {
                'sample_rate': fmt_info['sample_rate'],
                'byte_rate': fmt_info['byte_rate'],
                'num_channels': fmt_info['num_channels'],
                'bits_per_sample': fmt_info['bits_per_sample'],
                'data_size': data_size,
                'duration': data_size / float(fmt_info['byte_rate'])
            }

    except Exception:
        # Failed to parse WAV info - return None
        logger.debug('Failed to parse WAV info', exc_info=True)
        return None

    return None


def validate_audio_duration(value: Optional[str], min_seconds: float = 1.0, max_seconds: float = 30.0) -> Optional[str]:
    """
    Validate that the base64-encoded audio is a WAV and has duration within the limits.
    Returns the original value if valid, raises ValidationError otherwise.
    """
    if not value:
        return value

    decoded = decode_base64_audio(value)
    info = get_wav_info(decoded)
    if not info:
        raise ValidationError("Unable to determine WAV audio duration - unsupported format or missing metadata")

    duration = info.get('duration')
    if duration is None:
        raise ValidationError("Unable to compute audio duration")

    if duration < min_seconds:
        raise ValidationError(f"Audio duration {duration:.2f}s is shorter than minimum allowed {min_seconds}s")

    if duration > max_seconds:
        raise ValidationError(f"Audio duration {duration:.2f}s exceeds maximum allowed {max_seconds}s")

    return value


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


class SensorResult(BaseModel):
    """
    Standardized sensor result model
    """
    sensor_name: str
    passed: Optional[bool] = None
    value: float
    threshold: float
    reason: Optional[str] = None
    detail: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
