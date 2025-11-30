"""
Validation utilities for API input validation.

Provides pure functions for validating file uploads, content types, and data properties.
"""

from typing import Tuple, Optional, List, Any

# Try to import numpy, but make it optional
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


def validate_file_size(
    file_size: int,
    max_size_mb: int = 50,
) -> Tuple[bool, Optional[str]]:
    """
    Validate file size is within acceptable limits.
    
    Pure function that checks file size constraints.
    
    Args:
        file_size: Size of file in bytes
        max_size_mb: Maximum allowed size in megabytes
    
    Returns:
        Tuple of (is_valid, error_message)
        error_message is None if valid
    
    Example:
        is_valid, error = validate_file_size(len(file_content), max_size_mb=50)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error)
    """
    max_bytes = max_size_mb * 1024 * 1024

    if file_size == 0:
        return False, "Empty file uploaded"

    if file_size > max_bytes:
        return False, f"File too large. Maximum size is {max_size_mb}MB"

    return True, None


def validate_content_type(
    content_type: Optional[str],
    allowed_types: Optional[List[str]] = None,
) -> Tuple[bool, Optional[str]]:
    """
    Validate content type matches allowed types.
    
    Pure function that checks MIME type prefixes.
    
    Args:
        content_type: MIME type of the content
        allowed_types: List of allowed type prefixes (default: ["audio/"])
    
    Returns:
        Tuple of (is_valid, error_message)
    
    Example:
        is_valid, error = validate_content_type(
            file.content_type,
            allowed_types=["audio/", "video/"]
        )
    """
    if allowed_types is None:
        allowed_types = ["audio/"]

    if not content_type:
        return True, None  # Allow missing content-type

    if not any(content_type.startswith(t) for t in allowed_types):
        return False, f"Invalid file type. Expected one of {allowed_types}, got {content_type}"

    return True, None


def validate_audio_properties(
    audio_data: Any,
    samplerate: int,
    min_samplerate: int = 8000,
    max_samplerate: int = 192000,
    max_duration_seconds: float = 300.0,
) -> Tuple[bool, Optional[str]]:
    """
    Validate audio data properties.
    
    Pure function that checks sample rate and duration constraints.
    
    Args:
        audio_data: Audio data array (numpy ndarray)
        samplerate: Sample rate in Hz
        min_samplerate: Minimum allowed sample rate
        max_samplerate: Maximum allowed sample rate
        max_duration_seconds: Maximum allowed duration
    
    Returns:
        Tuple of (is_valid, error_message)
    
    Example:
        is_valid, error = validate_audio_properties(audio_data, 16000)
    """
    # Validate samplerate
    if samplerate < min_samplerate or samplerate > max_samplerate:
        return False, (
            f"Invalid sample rate: {samplerate}Hz. "
            f"Must be between {min_samplerate}Hz and {max_samplerate}Hz"
        )

    # Validate duration
    if HAS_NUMPY:
        length = len(audio_data) if hasattr(audio_data, '__len__') else 0
    else:
        length = len(audio_data) if hasattr(audio_data, '__len__') else 0
    
    duration = length / samplerate if samplerate > 0 else 0
    if duration > max_duration_seconds:
        return False, (
            f"Audio too long: {duration:.1f}s. "
            f"Maximum duration is {max_duration_seconds}s"
        )

    return True, None


def validate_upload(
    file_size: int,
    content_type: Optional[str],
    audio_data: Any,
    samplerate: int,
    max_size_mb: int = 50,
    allowed_types: Optional[List[str]] = None,
) -> Tuple[bool, Optional[str]]:
    """
    Compose all upload validations.
    
    Runs all validation checks in sequence, returning the first error found.
    
    Args:
        file_size: Size of uploaded file in bytes
        content_type: MIME type of the file
        audio_data: Audio data array
        samplerate: Audio sample rate
        max_size_mb: Maximum file size in MB
        allowed_types: Allowed MIME type prefixes
    
    Returns:
        Tuple of (is_valid, error_message)
    
    Example:
        is_valid, error = validate_upload(
            file_size=len(file_content),
            content_type=file.content_type,
            audio_data=audio_data,
            samplerate=samplerate
        )
        if not is_valid:
            raise HTTPException(status_code=400, detail=error)
    """
    # File size validation
    valid, error = validate_file_size(file_size, max_size_mb)
    if not valid:
        return False, error

    # Content type validation
    valid, error = validate_content_type(content_type, allowed_types)
    if not valid:
        return False, error

    # Audio properties validation
    valid, error = validate_audio_properties(audio_data, samplerate)
    if not valid:
        return False, error

    return True, None


def validate_required_fields(
    data: dict,
    required_fields: List[str],
) -> Tuple[bool, Optional[str]]:
    """
    Validate that all required fields are present in a dictionary.
    
    Args:
        data: Dictionary to validate
        required_fields: List of required field names
    
    Returns:
        Tuple of (is_valid, error_message)
    
    Example:
        is_valid, error = validate_required_fields(
            request_data,
            ["user_id", "transaction_id", "amount"]
        )
    """
    missing = [field for field in required_fields if field not in data]
    if missing:
        return False, f"Missing required fields: {', '.join(missing)}"
    return True, None


def validate_numeric_range(
    value: float,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
    field_name: str = "value",
) -> Tuple[bool, Optional[str]]:
    """
    Validate a numeric value is within specified range.
    
    Args:
        value: The numeric value to validate
        min_value: Minimum allowed value (inclusive)
        max_value: Maximum allowed value (inclusive)
        field_name: Name of field for error message
    
    Returns:
        Tuple of (is_valid, error_message)
    
    Example:
        is_valid, error = validate_numeric_range(
            amount, min_value=0, max_value=1000000, field_name="amount"
        )
    """
    if min_value is not None and value < min_value:
        return False, f"{field_name} must be at least {min_value}, got {value}"
    if max_value is not None and value > max_value:
        return False, f"{field_name} must be at most {max_value}, got {value}"
    return True, None
