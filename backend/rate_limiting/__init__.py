"""
Rate Limiting Module
Production-grade rate limiting system with persistent storage for API protection

Features:
- Multiple rate limiting strategies (fixed window, sliding window, token bucket)
- Per-user, per-IP, and per-API-key limits
- Tiered rate limits (free, basic, premium)
- Burst allowance configuration
- Custom rate limit headers in responses
- Graceful degradation if storage unavailable

Usage:
    from backend.rate_limiting import RateLimiter, limit, limit_by_ip

    # Using decorator
    @app.post("/analyze")
    @limit("10/minute", key_func=get_user_id)
    async def analyze_audio(request: Request, file: UploadFile):
        ...

    # Using limiter directly
    limiter = RateLimiter(storage="redis")
    result = limiter.check("user:123", limit="100/minute")
    if not result.allowed:
        raise HTTPException(status_code=429, ...)

Configuration via environment variables:
    - RATE_LIMIT_ENABLED: Enable/disable rate limiting (default: true)
    - RATE_LIMIT_STORAGE: Storage backend - "memory" or "redis" (default: memory)
    - RATE_LIMIT_REDIS_URL: Redis connection URL
    - RATE_LIMIT_DEFAULT: Default rate limit (default: 100/minute)
    - RATE_LIMIT_BYPASS_KEY: Key to bypass rate limiting
"""

from .limiter import RateLimiter, RateLimitExceeded, RateLimitResult, get_limiter, reset_limiter

from .decorators import (
    limit,
    limit_by_ip,
    limit_by_api_key,
    limit_by_user,
    limit_tier,
    get_remote_address,
    get_api_key,
    get_user_id,
    RateLimitMiddleware,
)

from .strategies import (
    RateLimitStrategy,
    FixedWindowStrategy,
    SlidingWindowStrategy,
    TokenBucketStrategy,
    create_strategy,
)

from .storage import BaseStorage, MemoryStorage, RedisStorage

from .config import RateLimitConfig, RateLimitTier, get_config, reset_config

__all__ = [
    # Core
    "RateLimiter",
    "RateLimitExceeded",
    "RateLimitResult",
    "get_limiter",
    "reset_limiter",
    # Decorators
    "limit",
    "limit_by_ip",
    "limit_by_api_key",
    "limit_by_user",
    "limit_tier",
    "get_remote_address",
    "get_api_key",
    "get_user_id",
    "RateLimitMiddleware",
    # Strategies
    "RateLimitStrategy",
    "FixedWindowStrategy",
    "SlidingWindowStrategy",
    "TokenBucketStrategy",
    "create_strategy",
    # Storage
    "BaseStorage",
    "MemoryStorage",
    "RedisStorage",
    # Config
    "RateLimitConfig",
    "RateLimitTier",
    "get_config",
    "reset_config",
]
