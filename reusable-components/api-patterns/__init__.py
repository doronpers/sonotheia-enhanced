"""
API Patterns - Reusable FastAPI patterns for robust, maintainable APIs.

This module provides production-ready patterns combining FastAPI framework (OOP)
with functional transformations for building RESTful APIs.

Exports:
    - Middleware utilities (metrics, logging, error handling)
    - Validation functions
    - Response builders
    - Health check patterns
"""

from .middleware import (
    MetricsMiddleware,
    LoggingMiddleware,
    build_error_response,
)
from .validation import (
    validate_file_size,
    validate_content_type,
    validate_audio_properties,
    validate_upload,
)
from .response import (
    convert_numpy_types,
    build_success_response,
    build_analysis_metadata,
    build_health_response,
)

__all__ = [
    # Middleware
    "MetricsMiddleware",
    "LoggingMiddleware",
    "build_error_response",
    # Validation
    "validate_file_size",
    "validate_content_type",
    "validate_audio_properties",
    "validate_upload",
    # Response
    "convert_numpy_types",
    "build_success_response",
    "build_analysis_metadata",
    "build_health_response",
]

__version__ = "1.0.0"
