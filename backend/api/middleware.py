"""
API Middleware Components
Rate limiting, authentication, and request tracking
"""

from fastapi import Request, HTTPException, status
from fastapi.security import APIKeyHeader
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from typing import Optional
import uuid
import time
import logging

logger = logging.getLogger(__name__)

# Rate limiter configuration
limiter = Limiter(key_func=get_remote_address)

# API Key security scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Configurable API keys (in production, use environment variables or secrets manager)
VALID_API_KEYS = {
    "demo-key-123": {"client": "demo", "tier": "free"},
    # Add more keys as needed
}


async def verify_api_key(api_key: Optional[str] = None) -> dict:
    """
    Verify API key if authentication is enabled
    Returns client info if valid, raises HTTPException if invalid
    """
    # For now, API key is optional - can be made required by removing Optional
    if api_key is None:
        # Allow unauthenticated access for demo/development
        return {"client": "anonymous", "tier": "free"}
    
    if api_key not in VALID_API_KEYS:
        logger.warning(f"Invalid API key attempted: {api_key[:8]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "INVALID_API_KEY",
                "message": "Invalid API key provided",
                "timestamp": time.time()
            }
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
    request_id = getattr(request.state, 'request_id', 'unknown')
    
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
    response = {
        "error_code": error_code,
        "message": message,
        "timestamp": time.time()
    }
    
    if details:
        response["details"] = details
    
    return response
