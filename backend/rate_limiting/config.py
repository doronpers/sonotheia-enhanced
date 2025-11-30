"""
Rate Limiting Configuration
Environment-based configuration for rate limiting
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class RateLimitTier:
    """Rate limit configuration for a specific tier."""

    requests_per_minute: int
    requests_per_hour: int
    burst_size: int


@dataclass
class RateLimitConfig:
    """Rate limiting configuration loaded from environment variables."""

    # Global settings
    enabled: bool = field(
        default_factory=lambda: os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    )

    # Storage settings
    storage_type: str = field(default_factory=lambda: os.getenv("RATE_LIMIT_STORAGE", "memory"))
    redis_url: Optional[str] = field(
        default_factory=lambda: os.getenv("RATE_LIMIT_REDIS_URL", None)
    )

    # Default rate limit (format: "requests/period" e.g., "100/minute")
    default_limit: str = field(
        default_factory=lambda: os.getenv("RATE_LIMIT_DEFAULT", "100/minute")
    )

    # Bypass settings
    bypass_header: str = field(
        default_factory=lambda: os.getenv("RATE_LIMIT_BYPASS_HEADER", "X-RateLimit-Bypass")
    )
    bypass_key: Optional[str] = field(
        default_factory=lambda: os.getenv("RATE_LIMIT_BYPASS_KEY", None)
    )

    # Tiered rate limits
    tiers: Dict[str, RateLimitTier] = field(
        default_factory=lambda: {
            "free": RateLimitTier(requests_per_minute=20, requests_per_hour=500, burst_size=5),
            "basic": RateLimitTier(requests_per_minute=60, requests_per_hour=2000, burst_size=15),
            "premium": RateLimitTier(
                requests_per_minute=200, requests_per_hour=10000, burst_size=50
            ),
            "admin": RateLimitTier(
                requests_per_minute=1000, requests_per_hour=100000, burst_size=100
            ),
        }
    )

    # Memory storage cleanup interval (seconds)
    cleanup_interval: int = field(
        default_factory=lambda: int(os.getenv("RATE_LIMIT_CLEANUP_INTERVAL", "60"))
    )

    @classmethod
    def from_env(cls) -> "RateLimitConfig":
        """Create configuration from environment variables."""
        return cls()

    def get_tier(self, tier_name: str) -> RateLimitTier:
        """Get rate limit tier by name, defaulting to 'free' if not found."""
        return self.tiers.get(tier_name.lower(), self.tiers["free"])


# Global configuration instance
_config: Optional[RateLimitConfig] = None


def get_config() -> RateLimitConfig:
    """Get the global rate limiting configuration."""
    global _config
    if _config is None:
        _config = RateLimitConfig.from_env()
    return _config


def reset_config() -> None:
    """Reset configuration (useful for testing)."""
    global _config
    _config = None
