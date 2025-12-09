"""
API Middleware Components
Rate limiting, authentication, and request tracking
"""

from fastapi import Request, HTTPException, status, Depends
from fastapi.security import APIKeyHeader
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import Optional
import uuid
import time
import logging
import os

logger = logging.getLogger(__name__)

# Rate limiter configuration
limiter = Limiter(key_func=get_remote_address)

# API Key security scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Load API keys from environment (secure)
# Note: API keys should ONLY be set via environment variables, never hardcoded
_demo_key = os.getenv("DEMO_API_KEY")  # No default - must be set explicitly
_api_keys_env = os.getenv("API_KEYS", "")  # Format: "key1:client1:tier1,key2:client2:tier2"

VALID_API_KEYS = {}

# Add demo key only if in demo mode AND a demo key is configured
if os.getenv("DEMO_MODE", "true").lower() == "true" and _demo_key:
    VALID_API_KEYS[_demo_key] = {"client": "demo", "tier": "free"}
    logger.warning("DEMO_MODE enabled with demo API key. Disable in production!")

# Parse production API keys from environment
if _api_keys_env:
    for key_config in _api_keys_env.split(','):
        parts = key_config.strip().split(':')
        if len(parts) == 3:
            key, client, tier = parts
            VALID_API_KEYS[key] = {"client": client, "tier": tier}


async def verify_api_key(api_key: Optional[str] = Depends(api_key_header)) -> dict:
    """
    Verify API key if authentication is enabled.
    Returns client info if valid, raises HTTPException if invalid.

    Security: API keys are not logged to prevent exposure.
    """
    # Check if API key is required (production mode)
    if api_key is None:
        # Only allow anonymous access in demo mode
        if os.getenv("DEMO_MODE", "true").lower() != "true":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error_code": "MISSING_API_KEY",
                    "message": "API key required in production mode"
                }
            )
        # Allow unauthenticated access for demo/development
        return {"client": "anonymous", "tier": "free"}

    if api_key not in VALID_API_KEYS:
        # Security: Do NOT log any part of the invalid API key (prevents brute force)
        logger.warning("Invalid API key attempted from request")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "INVALID_API_KEY",
                "message": "Invalid API key provided",
                "timestamp": time.time(),
            },
        )

    return VALID_API_KEYS[api_key]


async def add_request_id_middleware(request: Request, call_next):
    """
    Add unique request ID to each request for tracking and debugging
    """
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    # Add to response headers
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id

    return response


async def log_request_middleware(request: Request, call_next):
    """
    Log request details for monitoring and debugging
    """
    start_time = time.time()

    # Get request ID if available
    request_id = getattr(request.state, "request_id", "unknown")

    # Log request
    logger.info(f"Request {request_id}: {request.method} {request.url.path}")

    # Process request
    response = await call_next(request)

    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000

    # Log response
    logger.info(
        f"Request {request_id} completed: "
        f"status={response.status_code} duration={duration_ms:.2f}ms"
    )

    # Add performance header
    response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

    return response


async def add_security_headers_middleware(request: Request, call_next):
    """
    Add security headers to all responses
    Protects against common web vulnerabilities
    """
    response = await call_next(request)

    # Prevent MIME type sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"

    # Prevent clickjacking
    response.headers["X-Frame-Options"] = "DENY"

    # Enable XSS protection (for older browsers)
    response.headers["X-XSS-Protection"] = "1; mode=block"

    # Content Security Policy - restrictive default
    # Allow Swagger UI CDN resources for docs pages
    is_docs_page = request.url.path in ["/docs", "/redoc", "/openapi.json"]
    
    if is_docs_page:
        # More permissive CSP for Swagger UI documentation
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data: https:; "
            "font-src 'self' https://cdn.jsdelivr.net; "
            "connect-src 'self'; "
            "frame-ancestors 'none'"
        )
    else:
        # Restrictive CSP for all other endpoints
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'"
        )

    # Referrer policy
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # Permissions policy (formerly Feature-Policy)
    response.headers["Permissions-Policy"] = (
        "geolocation=(), microphone=(), camera=(), payment=()"
    )

    # HTTPS enforcement (if not in development)
    if not os.getenv("DEMO_MODE", "true").lower() == "true":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    return response


def get_error_response(error_code: str, message: str, details: Optional[dict] = None) -> dict:
    """
    Standardized error response format
    Security: Does not include sensitive details in production
    """
    response = {
        "error_code": error_code,
        "message": message,
        "timestamp": time.time()
    }

    # Only include details in demo mode to prevent information disclosure
    if details and os.getenv("DEMO_MODE", "true").lower() == "true":
        response["details"] = details

    return response
