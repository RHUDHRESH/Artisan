"""
Caching system for Artisan Hub.

Provides Redis-backed caching with fallback to in-memory cache.
"""

import json
import hashlib
from typing import Any, Optional, Callable
from functools import wraps
import asyncio
from datetime import timedelta

import redis.asyncio as redis
from backend.core.config import settings
from backend.core.monitoring import cache_hits_total, cache_misses_total, get_logger

logger = get_logger("cache")


# ============================================================================
# Cache Manager
# ============================================================================

class CacheManager:
    """
    Unified cache manager with Redis backend and in-memory fallback.
    """

    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.memory_cache: dict = {}
        self.cache_type = "memory"

    async def initialize(self):
        """Initialize Redis connection."""
        try:
            self.redis_client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await self.redis_client.ping()
            self.cache_type = "redis"
            logger.info("cache_initialized", type="redis")
        except Exception as e:
            logger.warning("redis_connection_failed", error=str(e), fallback="memory")
            self.cache_type = "memory"

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            if self.cache_type == "redis" and self.redis_client:
                value = await self.redis_client.get(key)
                if value:
                    cache_hits_total.labels(cache_type="redis").inc()
                    return json.loads(value) if value else None
                else:
                    cache_misses_total.labels(cache_type="redis").inc()
                    return None
            else:
                # Fallback to memory cache
                if key in self.memory_cache:
                    cache_hits_total.labels(cache_type="memory").inc()
                    return self.memory_cache[key]
                else:
                    cache_misses_total.labels(cache_type="memory").inc()
                    return None
        except Exception as e:
            logger.error("cache_get_failed", key=key, error=str(e))
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache with optional TTL (seconds)."""
        try:
            if self.cache_type == "redis" and self.redis_client:
                serialized = json.dumps(value)
                if ttl:
                    await self.redis_client.setex(key, ttl, serialized)
                else:
                    await self.redis_client.set(key, serialized)
                return True
            else:
                # Fallback to memory cache
                self.memory_cache[key] = value
                if ttl:
                    # Schedule cleanup
                    asyncio.create_task(self._cleanup_memory_cache(key, ttl))
                return True
        except Exception as e:
            logger.error("cache_set_failed", key=key, error=str(e))
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            if self.cache_type == "redis" and self.redis_client:
                await self.redis_client.delete(key)
            else:
                self.memory_cache.pop(key, None)
            return True
        except Exception as e:
            logger.error("cache_delete_failed", key=key, error=str(e))
            return False

    async def clear(self) -> bool:
        """Clear all cache entries."""
        try:
            if self.cache_type == "redis" and self.redis_client:
                await self.redis_client.flushdb()
            else:
                self.memory_cache.clear()
            logger.info("cache_cleared", type=self.cache_type)
            return True
        except Exception as e:
            logger.error("cache_clear_failed", error=str(e))
            return False

    async def _cleanup_memory_cache(self, key: str, ttl: int):
        """Cleanup memory cache after TTL expires."""
        await asyncio.sleep(ttl)
        self.memory_cache.pop(key, None)

    async def close(self):
        """Close cache connections."""
        if self.redis_client:
            await self.redis_client.close()


# Global cache instance
cache_manager = CacheManager()


# ============================================================================
# Cache Decorators
# ============================================================================

def cache_key_builder(*args, **kwargs) -> str:
    """Build cache key from function arguments."""
    key_parts = [str(arg) for arg in args]
    key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
    key_string = ":".join(key_parts)

    # Hash for consistent key length
    return hashlib.md5(key_string.encode()).hexdigest()


def cached(
    ttl: int = 3600,
    key_prefix: str = "",
    cache_type: str = "default"
):
    """
    Decorator to cache function results.

    Args:
        ttl: Time to live in seconds (default: 1 hour)
        key_prefix: Prefix for cache key
        cache_type: Type of cache (for metrics)
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key
            func_key = f"{key_prefix}:{func.__name__}"
            args_key = cache_key_builder(*args, **kwargs)
            cache_key = f"{func_key}:{args_key}"

            # Try to get from cache
            cached_value = await cache_manager.get(cache_key)
            if cached_value is not None:
                logger.debug("cache_hit", key=cache_key)
                return cached_value

            # Cache miss - call function
            logger.debug("cache_miss", key=cache_key)
            result = await func(*args, **kwargs)

            # Store in cache
            await cache_manager.set(cache_key, result, ttl=ttl)

            return result

        return wrapper
    return decorator


def invalidate_cache(key_pattern: str):
    """
    Decorator to invalidate cache entries matching pattern after function execution.
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)

            # Invalidate cache
            # Note: In production, you'd want pattern matching for Redis
            if cache_manager.cache_type == "redis" and cache_manager.redis_client:
                # Use Redis SCAN to find matching keys
                cursor = 0
                while True:
                    cursor, keys = await cache_manager.redis_client.scan(
                        cursor,
                        match=key_pattern,
                        count=100
                    )
                    if keys:
                        await cache_manager.redis_client.delete(*keys)
                    if cursor == 0:
                        break
            else:
                # Memory cache: simple pattern matching
                keys_to_delete = [
                    k for k in cache_manager.memory_cache.keys()
                    if key_pattern in k
                ]
                for key in keys_to_delete:
                    cache_manager.memory_cache.pop(key, None)

            logger.info("cache_invalidated", pattern=key_pattern)
            return result

        return wrapper
    return decorator


# ============================================================================
# Specialized Caches
# ============================================================================

class LRUCache:
    """
    Simple LRU cache for in-memory caching.
    """

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache: dict = {}
        self.access_order: list = []

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key in self.cache:
            # Update access order
            self.access_order.remove(key)
            self.access_order.append(key)
            cache_hits_total.labels(cache_type="lru").inc()
            return self.cache[key]
        else:
            cache_misses_total.labels(cache_type="lru").inc()
            return None

    def set(self, key: str, value: Any):
        """Set value in cache."""
        if key in self.cache:
            self.access_order.remove(key)
        elif len(self.cache) >= self.max_size:
            # Evict least recently used
            lru_key = self.access_order.pop(0)
            del self.cache[lru_key]

        self.cache[key] = value
        self.access_order.append(key)

    def clear(self):
        """Clear cache."""
        self.cache.clear()
        self.access_order.clear()


# ============================================================================
# Cache Warming
# ============================================================================

async def warm_cache():
    """
    Warm up cache with frequently accessed data.
    """
    logger.info("cache_warming_started")

    try:
        # Example: Pre-load common supplier searches
        # This would be customized based on your application

        # Warm LLM model cache
        from backend.core.llm_provider import LLMManager
        llm_manager = LLMManager()
        await llm_manager.health_check()

        logger.info("cache_warming_completed")
    except Exception as e:
        logger.error("cache_warming_failed", error=str(e))


# ============================================================================
# Cache Statistics
# ============================================================================

async def get_cache_stats() -> dict:
    """Get cache statistics."""
    stats = {
        "type": cache_manager.cache_type,
        "entries": 0
    }

    try:
        if cache_manager.cache_type == "redis" and cache_manager.redis_client:
            info = await cache_manager.redis_client.info("stats")
            stats["entries"] = info.get("db0", {}).get("keys", 0)
            stats["hits"] = info.get("keyspace_hits", 0)
            stats["misses"] = info.get("keyspace_misses", 0)
            stats["hit_rate"] = (
                stats["hits"] / (stats["hits"] + stats["misses"])
                if (stats["hits"] + stats["misses"]) > 0
                else 0
            )
        else:
            stats["entries"] = len(cache_manager.memory_cache)

        return stats
    except Exception as e:
        logger.error("failed_to_get_cache_stats", error=str(e))
        return stats
