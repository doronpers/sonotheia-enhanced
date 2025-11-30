"""
Response builders for API responses.

Provides pure functions for building consistent API responses.
"""

from typing import Dict, Any, Union, List
from datetime import datetime

# Try to import numpy, but make it optional
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


# Type alias for JSON-serializable values
JSONValue = Union[None, bool, int, float, str, List[Any], Dict[str, Any]]


def convert_numpy_types(obj: Any) -> JSONValue:
    """
    Recursively convert numpy types to JSON-serializable Python types.
    
    Pure function that handles numpy arrays and scalars.
    
    Args:
        obj: Object to convert (may contain numpy types)
    
    Returns:
        JSON-serializable object
    
    Example:
        import numpy as np
        data = {
            'score': np.float64(0.95),
            'values': np.array([1, 2, 3]),
            'flag': np.bool_(True)
        }
        json_data = convert_numpy_types(data)
        # {'score': 0.95, 'values': [1, 2, 3], 'flag': True}
    """
    if HAS_NUMPY:
        if isinstance(obj, (np.integer, np.floating)):
            return obj.item()
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.bool_):
            return bool(obj)
    
    if isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_numpy_types(item) for item in obj]
    else:
        return obj


def build_success_response(
    verdict: str,
    detail: str,
    evidence: Dict[str, Any],
    processing_time: float,
    model_version: str,
) -> Dict[str, Any]:
    """
    Build a standardized success response for analysis endpoints.
    
    Pure function that creates consistent response structure.
    
    Args:
        verdict: Analysis verdict (e.g., "REAL", "SYNTHETIC")
        detail: Detailed explanation of the verdict
        evidence: Dictionary of supporting evidence
        processing_time: Time taken to process in seconds
        model_version: Version of the model used
    
    Returns:
        Standardized response dictionary
    
    Example:
        response = build_success_response(
            verdict="REAL",
            detail="All physics checks passed.",
            evidence={"breath": {...}, "dynamic_range": {...}},
            processing_time=0.234,
            model_version="v9.0"
        )
    """
    response = {
        "verdict": verdict,
        "detail": detail,
        "processing_time_seconds": round(processing_time, 3),
        "model_version": model_version,
        "evidence": evidence,
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    # Convert numpy types for JSON serialization
    return convert_numpy_types(response)


def build_analysis_metadata(
    file_size_mb: float,
    samplerate: int,
    duration_seconds: float,
    num_channels: int,
) -> Dict[str, Any]:
    """
    Build metadata about analyzed audio.
    
    Pure function for creating consistent metadata structure.
    
    Args:
        file_size_mb: File size in megabytes
        samplerate: Audio sample rate in Hz
        duration_seconds: Audio duration in seconds
        num_channels: Number of audio channels
    
    Returns:
        Metadata dictionary
    
    Example:
        metadata = build_analysis_metadata(
            file_size_mb=2.5,
            samplerate=16000,
            duration_seconds=30.5,
            num_channels=1
        )
    """
    return {
        "file_size_mb": round(file_size_mb, 2),
        "samplerate": samplerate,
        "duration_seconds": round(duration_seconds, 2),
        "channels": num_channels,
    }


def build_health_response(
    status: str,
    service_name: str,
    version: str,
    uptime_seconds: float,
    additional_info: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """
    Build a standardized health check response.
    
    Pure function for creating health check payloads.
    
    Args:
        status: Health status (e.g., "healthy", "degraded", "unhealthy")
        service_name: Name of the service
        version: Service version
        uptime_seconds: Time since service started
        additional_info: Optional additional health information
    
    Returns:
        Health check response dictionary
    
    Example:
        health = build_health_response(
            status="healthy",
            service_name="Audio Analysis API",
            version="v9.0",
            uptime_seconds=3600.5
        )
    """
    response = {
        "status": status,
        "service": service_name,
        "version": version,
        "uptime_seconds": round(uptime_seconds, 2),
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    if additional_info:
        response.update(additional_info)
    
    return response


def build_paginated_response(
    items: List[Any],
    page: int,
    page_size: int,
    total_items: int,
) -> Dict[str, Any]:
    """
    Build a paginated response wrapper.
    
    Args:
        items: List of items for current page
        page: Current page number (1-indexed)
        page_size: Number of items per page
        total_items: Total number of items across all pages
    
    Returns:
        Paginated response with items and pagination metadata
    
    Example:
        response = build_paginated_response(
            items=[...],
            page=1,
            page_size=20,
            total_items=100
        )
    """
    total_pages = (total_items + page_size - 1) // page_size if page_size > 0 else 0
    
    return {
        "items": items,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_items": total_items,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_previous": page > 1,
        },
    }


def build_error_details(
    errors: List[Dict[str, Any]],
    request_id: str = None,
) -> Dict[str, Any]:
    """
    Build detailed error response for validation errors.
    
    Args:
        errors: List of error dictionaries with field, message, code
        request_id: Optional request identifier for tracking
    
    Returns:
        Detailed error response
    
    Example:
        errors = [
            {"field": "amount", "message": "Must be positive", "code": "invalid_value"},
            {"field": "user_id", "message": "Required", "code": "missing_field"}
        ]
        response = build_error_details(errors, request_id="req-123")
    """
    response = {
        "error": {
            "type": "validation_error",
            "message": "One or more validation errors occurred",
            "details": errors,
            "timestamp": datetime.utcnow().isoformat(),
        }
    }
    
    if request_id:
        response["error"]["request_id"] = request_id
    
    return response
