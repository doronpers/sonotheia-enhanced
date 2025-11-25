"""
API Middleware Components
Rate limiting, authentication, and request tracking
"""

from fastapi import Request, HTTPException, status
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

# Load API keys from environment (more secure than hardcoded)
# In production, use a secrets manager or database
_API_KEYS_ENV = os.environ.get("SONOTHEIA_API_KEYS", "")


def _load_api_keys() -> dict:
    """
    Load API keys from environment variables.
    Format: key1:client1:tier1,key2:client2:tier2
    Falls back to demo key if none configured.
    """
    if not _API_KEYS_ENV:
        # Demo mode fallback - WARNING: Do not use in production
        logger.warning(
            "No API keys configured. Using demo key. "
            "Set SONOTHEIA_API_KEYS environment variable in production."
        )
        return {
            "demo-key-123": {"client": "demo", "tier": "free"},
        }

    keys = {}
    for entry in _API_KEYS_ENV.split(","):
        parts = entry.strip().split(":")
        if len(parts) >= 2:
            key = parts[0]
            client = parts[1]
            tier = parts[2] if len(parts) > 2 else "standard"
            keys[key] = {"client": client, "tier": tier}

    return keys


# Load API keys at module initialization
VALID_API_KEYS = _load_api_keys()


async def verify_api_key(api_key: Optional[str] = None) -> dict:
    """
    Verify API key if authentication is enabled.
    Returns client info if valid, raises HTTPException if invalid.

    Security: API keys are not logged to prevent exposure.
    """
    # For now, API key is optional - can be made required by removing Optional
    if api_key is None:
        # Allow unauthenticated access for demo/development
        return {"client": "anonymous", "tier": "free"}

    if api_key not in VALID_API_KEYS:
        # Don't log the actual key to prevent exposure in logs
        logger.warning("Invalid API key attempted")
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


def get_error_response(error_code: str, message: str, details: Optional[dict] = None) -> dict:
    """
    Standardized error response format
    """
    response = {"error_code": error_code, "message": message, "timestamp": time.time()}

    if details:
        response["details"] = details

    return response
