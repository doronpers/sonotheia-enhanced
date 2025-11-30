"""
FastAPI Rate Limiting Decorators
Decorators for easy rate limiting integration with FastAPI endpoints
"""

import functools
import logging
import time
from typing import Optional, Callable

from fastapi import Request, HTTPException, Response
from fastapi.responses import JSONResponse

from .limiter import RateLimitResult, get_limiter
from .config import get_config

logger = logging.getLogger(__name__)


def get_remote_address(request: Request) -> str:
    """
    Extract client IP address from request.

    Handles common proxy headers (X-Forwarded-For, X-Real-IP).

    Args:
        request: FastAPI Request object

    Returns:
        Client IP address string
    """
    # Check for forwarded headers (reverse proxy)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # X-Forwarded-For can contain multiple IPs; the first is the client
        return forwarded.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    # Fall back to direct client
    if request.client:
        return request.client.host

    return "unknown"


def get_api_key(request: Request) -> Optional[str]:
    """
    Extract API key from request.

    Checks X-API-Key header and Authorization header.

    Args:
        request: FastAPI Request object

    Returns:
        API key string or None
    """
    # Check X-API-Key header
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return api_key

    # Check Authorization header (Bearer token)
    auth = request.headers.get("Authorization")
    if auth and auth.startswith("Bearer "):
        return auth[7:]

    return None


def get_user_id(request: Request) -> Optional[str]:
    """
    Extract user ID from request.

    Checks request state and headers.

    Args:
        request: FastAPI Request object

    Returns:
        User ID string or None
    """
    # Check request state (set by authentication middleware)
    if hasattr(request.state, "user_id"):
        return request.state.user_id

    if hasattr(request.state, "user"):
        user = request.state.user
        if isinstance(user, dict):
            return user.get("id") or user.get("user_id")
        if hasattr(user, "id"):
            return str(user.id)

    return None


KeyFunc = Callable[[Request], str]


def _make_rate_limit_key(request: Request, key_func: Optional[KeyFunc], prefix: str = "") -> str:
    """
    Generate a rate limit key for a request.

    Args:
        request: FastAPI Request object
        key_func: Optional custom key function
        prefix: Optional key prefix

    Returns:
        Rate limit key string
    """
    if key_func:
        key = key_func(request)
    else:
        # Default: use IP address
        key = get_remote_address(request)

    # Include endpoint in key
    endpoint = request.url.path

    if prefix:
        return f"{prefix}:{endpoint}:{key}"
    return f"{endpoint}:{key}"


def _create_rate_limit_response(result: RateLimitResult) -> JSONResponse:
    """
    Create a 429 Too Many Requests response.

    Args:
        result: RateLimitResult from the rate limit check

    Returns:
        JSONResponse with proper status and headers
    """
    reset_time_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(result.reset_time))

    content = {
        "error_code": "RATE_LIMIT_EXCEEDED",
        "message": "Rate limit exceeded. Please retry later.",
        "retry_after": result.retry_after,
        "reset_time": result.reset_time,
        "reset_time_iso": reset_time_iso,
        "limit": result.limit,
        "remaining": result.remaining,
    }

    headers = {
        "X-RateLimit-Limit": str(result.limit),
        "X-RateLimit-Remaining": str(result.remaining),
        "X-RateLimit-Reset": str(result.reset_time),
        "Retry-After": str(result.retry_after),
    }

    return JSONResponse(status_code=429, content=content, headers=headers)


def limit(
    limit_string: str,
    key_func: Optional[KeyFunc] = None,
    strategy: Optional[str] = None,
    tier: Optional[str] = None,
    per_method: bool = True,
    exempt_when: Optional[Callable[[Request], bool]] = None,
):
    """
    Rate limiting decorator for FastAPI endpoints.

    Usage:
        @app.get("/api/data")
        @limit("100/minute")
        async def get_data(request: Request):
            ...

        @app.post("/api/analyze")
        @limit("10/minute", key_func=get_user_id)
        async def analyze(request: Request):
            ...

    Args:
        limit_string: Rate limit string (e.g., "100/minute", "1000/hour")
        key_func: Function to extract rate limit key from request
        strategy: Rate limiting strategy to use
        tier: Rate limit tier name (overrides limit_string if provided)
        per_method: Include HTTP method in key (default: True)
        exempt_when: Function that returns True to exempt request from rate limiting

    Returns:
        Decorator function
    """

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Find Request object in args or kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if not request:
                request = kwargs.get("request")

            if not request:
                # Can't rate limit without request, just call the function
                logger.warning(f"No Request object found for rate-limited endpoint {func.__name__}")
                return await func(*args, **kwargs)

            # Get limiter
            limiter = get_limiter()
            config = get_config()

            # Check if rate limiting is enabled
            if not config.enabled:
                response = await func(*args, **kwargs)
                return response

            # Check for bypass
            if limiter.check_bypass(dict(request.headers), get_api_key(request)):
                response = await func(*args, **kwargs)
                return response

            # Check exemption
            if exempt_when and exempt_when(request):
                response = await func(*args, **kwargs)
                return response

            # Generate rate limit key
            key = _make_rate_limit_key(request, key_func)
            if per_method:
                key = f"{request.method}:{key}"

            # Check rate limit
            if tier:
                result = limiter.check(key, tier=tier, strategy=strategy)
            else:
                result = limiter.check(key, limit=limit_string, strategy=strategy)

            # If not allowed, return 429
            if not result.allowed:
                logger.warning(
                    f"Rate limit exceeded for {key} "
                    f"(limit: {result.limit}, retry_after: {result.retry_after}s)"
                )
                return _create_rate_limit_response(result)

            # Process request
            response = await func(*args, **kwargs)

            # Add rate limit headers to response
            headers = limiter.get_headers(result)

            if isinstance(response, Response):
                for header, value in headers.items():
                    response.headers[header] = value
                return response
            else:
                # If response is a dict or other non-Response, wrap it in JSONResponse
                return JSONResponse(content=response, headers=headers)

        return wrapper

    return decorator


def limit_by_ip(limit_string: str, **kwargs):
    """
    Rate limiting decorator that limits by IP address.

    Args:
        limit_string: Rate limit string
        **kwargs: Additional arguments for limit decorator
    """
    return limit(limit_string, key_func=get_remote_address, **kwargs)


def limit_by_api_key(limit_string: str, **kwargs):
    """
    Rate limiting decorator that limits by API key.

    Falls back to IP if no API key is present.

    Args:
        limit_string: Rate limit string
        **kwargs: Additional arguments for limit decorator
    """

    def key_func(request: Request) -> str:
        api_key = get_api_key(request)
        if api_key:
            return f"apikey:{api_key}"
        return f"ip:{get_remote_address(request)}"

    return limit(limit_string, key_func=key_func, **kwargs)


def limit_by_user(limit_string: str, fallback_to_ip: bool = True, **kwargs):
    """
    Rate limiting decorator that limits by user ID.

    Args:
        limit_string: Rate limit string
        fallback_to_ip: Fall back to IP if no user ID (default: True)
        **kwargs: Additional arguments for limit decorator
    """

    def key_func(request: Request) -> str:
        user_id = get_user_id(request)
        if user_id:
            return f"user:{user_id}"
        if fallback_to_ip:
            return f"ip:{get_remote_address(request)}"
        raise HTTPException(status_code=401, detail="Authentication required for this endpoint")

    return limit(limit_string, key_func=key_func, **kwargs)


def limit_tier(tier: str, **kwargs):
    """
    Rate limiting decorator that uses a configured tier.

    Args:
        tier: Tier name (e.g., "free", "basic", "premium")
        **kwargs: Additional arguments for limit decorator
    """
    return limit("", tier=tier, **kwargs)


class RateLimitMiddleware:
    """
    ASGI middleware for global rate limiting.

    Applies rate limiting to all requests before they reach endpoints.

    Usage:
        app.add_middleware(RateLimitMiddleware, limit_string="1000/minute")
    """

    def __init__(
        self,
        app,
        limit_string: str = "1000/minute",
        key_func: Optional[KeyFunc] = None,
        exempt_paths: Optional[list] = None,
    ):
        """
        Initialize middleware.

        Args:
            app: ASGI application
            limit_string: Default rate limit
            key_func: Custom key function
            exempt_paths: List of paths to exempt from rate limiting
        """
        self.app = app
        self.limit_string = limit_string
        self.key_func = key_func or get_remote_address
        self.exempt_paths = exempt_paths or ["/health", "/docs", "/redoc", "/openapi.json"]

    async def __call__(self, scope, receive, send):
        """Handle ASGI request."""
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        # Check exempt paths
        path = scope.get("path", "")
        if any(path.startswith(exempt) for exempt in self.exempt_paths):
            return await self.app(scope, receive, send)

        # Create a minimal request-like object for key extraction
        from starlette.requests import Request

        request = Request(scope, receive)

        # Get limiter and check
        limiter = get_limiter()
        config = get_config()

        if not config.enabled:
            return await self.app(scope, receive, send)

        key = f"global:{self.key_func(request)}"
        result = limiter.check(key, limit=self.limit_string)

        if not result.allowed:
            # Send 429 response
            response = _create_rate_limit_response(result)
            await response(scope, receive, send)
            return

        # Continue with request
        return await self.app(scope, receive, send)
