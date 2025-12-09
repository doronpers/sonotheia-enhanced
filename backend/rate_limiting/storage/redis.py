"""
Redis Storage Backend
Distributed storage for rate limiting with fallback support
"""

import logging
import time
from typing import Dict, List, Optional, Any

from .base import BaseStorage
from .memory import MemoryStorage

logger = logging.getLogger(__name__)


class RedisStorage(BaseStorage):
    """
    Redis storage backend for distributed rate limiting.

    Provides atomic operations using Redis MULTI/EXEC transactions.
    Falls back to in-memory storage if Redis is unavailable.
    """

    def __init__(
        self,
        redis_url: Optional[str] = None,
        fallback_to_memory: bool = True,
        connection_timeout: float = 1.0,
        socket_timeout: float = 1.0,
        key_prefix: str = "ratelimit:",
    ):
        """
        Initialize Redis storage.

        Args:
            redis_url: Redis connection URL (e.g., "redis://localhost:6379/0")
            fallback_to_memory: If True, fall back to memory storage when Redis unavailable
            connection_timeout: Connection timeout in seconds
            socket_timeout: Socket timeout in seconds
            key_prefix: Prefix for all rate limit keys
        """
        self._redis_url = redis_url
        self._fallback_to_memory = fallback_to_memory
        self._connection_timeout = connection_timeout
        self._socket_timeout = socket_timeout
        self._key_prefix = key_prefix

        self._redis_client = None
        self._fallback_storage: Optional[MemoryStorage] = None
        self._using_fallback = False
        self._last_redis_check = 0.0
        self._redis_check_interval = 30.0  # Check Redis availability every 30 seconds

        # Initialize Redis connection
        self._init_redis()

    def _init_redis(self) -> None:
        """Initialize Redis connection."""
        if not self._redis_url:
            logger.warning("No Redis URL provided, using memory storage fallback")
            self._use_fallback()
            return

        try:
            import redis

            self._redis_client = redis.from_url(
                self._redis_url,
                socket_connect_timeout=self._connection_timeout,
                socket_timeout=self._socket_timeout,
                decode_responses=True,
            )
            # Test connection
            self._redis_client.ping()
            self._using_fallback = False
            logger.info("Redis storage initialized successfully")
        except ImportError:
            logger.warning("redis package not installed, using memory storage fallback")
            self._use_fallback()
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}, using memory storage fallback")
            self._use_fallback()

    def _use_fallback(self) -> None:
        """Switch to fallback memory storage."""
        if self._fallback_to_memory:
            if self._fallback_storage is None:
                self._fallback_storage = MemoryStorage()
            self._using_fallback = True
        else:
            raise RuntimeError("Redis unavailable and fallback disabled")

    def _check_redis_available(self) -> bool:
        """Check if Redis is available (with rate limiting on checks)."""
        if not self._redis_client:
            return False

        current_time = time.time()
        if current_time - self._last_redis_check < self._redis_check_interval:
            return not self._using_fallback

        self._last_redis_check = current_time

        try:
            self._redis_client.ping()
            if self._using_fallback:
                logger.info("Redis connection restored")
                self._using_fallback = False
            return True
        except Exception:
            if not self._using_fallback:
                logger.warning("Redis connection lost, using memory fallback")
                self._use_fallback()
            return False

    def _prefixed_key(self, key: str) -> str:
        """Add prefix to a key."""
        return f"{self._key_prefix}{key}"

    def get(self, key: str) -> Optional[Any]:
        """Get a value from storage."""
        if self._using_fallback or not self._check_redis_available():
            if self._fallback_storage:
                return self._fallback_storage.get(key)
            return None

        try:
            prefixed = self._prefixed_key(key)
            value = self._redis_client.get(prefixed)
            if value is not None:
                try:
                    return float(value)
                except (ValueError, TypeError):
                    return value
            return None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            self._use_fallback()
            if self._fallback_storage:
                return self._fallback_storage.get(key)
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a value in storage."""
        if self._using_fallback or not self._check_redis_available():
            if self._fallback_storage:
                return self._fallback_storage.set(key, value, ttl)
            return False

        try:
            prefixed = self._prefixed_key(key)
            if ttl:
                self._redis_client.setex(prefixed, ttl, value)
            else:
                self._redis_client.set(prefixed, value)
            return True
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            self._use_fallback()
            if self._fallback_storage:
                return self._fallback_storage.set(key, value, ttl)
            return False

    def increment(self, key: str, amount: int = 1, ttl: Optional[int] = None) -> int:
        """Atomically increment a counter."""
        if self._using_fallback or not self._check_redis_available():
            if self._fallback_storage:
                return self._fallback_storage.increment(key, amount, ttl)
            return 0

        try:
            prefixed = self._prefixed_key(key)

            # Use pipeline for atomic increment + expire
            pipe = self._redis_client.pipeline()
            pipe.incrby(prefixed, amount)
            if ttl:
                pipe.expire(prefixed, ttl, nx=True)  # Only set expire if not already set
            results = pipe.execute()

            # Safety: Check that pipeline returned results
            if not results or len(results) == 0:
                raise RuntimeError("Redis pipeline returned no results")
            return results[0]  # Return the incremented value
        except Exception as e:
            logger.error(f"Redis increment error: {e}")
            self._use_fallback()
            if self._fallback_storage:
                return self._fallback_storage.increment(key, amount, ttl)
            return 0

    def delete(self, key: str) -> bool:
        """Delete a key from storage."""
        if self._using_fallback or not self._check_redis_available():
            if self._fallback_storage:
                return self._fallback_storage.delete(key)
            return False

        try:
            prefixed = self._prefixed_key(key)
            return self._redis_client.delete(prefixed) > 0
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            self._use_fallback()
            if self._fallback_storage:
                return self._fallback_storage.delete(key)
            return False

    def exists(self, key: str) -> bool:
        """Check if a key exists in storage."""
        if self._using_fallback or not self._check_redis_available():
            if self._fallback_storage:
                return self._fallback_storage.exists(key)
            return False

        try:
            prefixed = self._prefixed_key(key)
            return self._redis_client.exists(prefixed) > 0
        except Exception as e:
            logger.error(f"Redis exists error: {e}")
            self._use_fallback()
            if self._fallback_storage:
                return self._fallback_storage.exists(key)
            return False

    def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values from storage."""
        if self._using_fallback or not self._check_redis_available():
            if self._fallback_storage:
                return self._fallback_storage.get_many(keys)
            return {}

        try:
            if not keys:
                return {}

            prefixed_keys = [self._prefixed_key(k) for k in keys]
            values = self._redis_client.mget(prefixed_keys)

            result = {}
            for key, value in zip(keys, values):
                if value is not None:
                    try:
                        result[key] = float(value)
                    except (ValueError, TypeError):
                        result[key] = value
            return result
        except Exception as e:
            logger.error(f"Redis get_many error: {e}")
            self._use_fallback()
            if self._fallback_storage:
                return self._fallback_storage.get_many(keys)
            return {}

    def set_many(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set multiple values in storage."""
        if self._using_fallback or not self._check_redis_available():
            if self._fallback_storage:
                return self._fallback_storage.set_many(mapping, ttl)
            return False

        try:
            if not mapping:
                return True

            prefixed_mapping = {self._prefixed_key(k): v for k, v in mapping.items()}

            if ttl:
                # Use pipeline for atomic set with expire
                pipe = self._redis_client.pipeline()
                for key, value in prefixed_mapping.items():
                    pipe.setex(key, ttl, value)
                pipe.execute()
            else:
                self._redis_client.mset(prefixed_mapping)
            return True
        except Exception as e:
            logger.error(f"Redis set_many error: {e}")
            self._use_fallback()
            if self._fallback_storage:
                return self._fallback_storage.set_many(mapping, ttl)
            return False

    def is_available(self) -> bool:
        """Check if storage is available."""
        if self._using_fallback:
            return self._fallback_storage is not None and self._fallback_storage.is_available()
        return self._check_redis_available()

    def cleanup_expired(self) -> int:
        """
        Remove expired entries from storage.

        Redis handles expiration automatically, so this is a no-op.
        For fallback storage, it delegates to memory storage cleanup.
        """
        if self._using_fallback and self._fallback_storage:
            return self._fallback_storage.cleanup_expired()
        return 0

    def is_using_fallback(self) -> bool:
        """Check if currently using fallback storage."""
        return self._using_fallback
