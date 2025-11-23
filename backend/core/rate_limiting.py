"""
Rate limiting system for Artisan Hub API.

Implements token bucket and sliding window rate limiting algorithms.
"""

import time
from typing import Dict, Optional
from collections import defaultdict
from datetime import datetime, timedelta

import redis.asyncio as redis
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

from backend.core.config import settings
from backend.core.monitoring import get_logger

logger = get_logger("rate_limit")


# ============================================================================
# Rate Limiter
# ============================================================================

class RateLimiter:
    """
    Redis-backed rate limiter with in-memory fallback.
    Implements sliding window algorithm.
    """

    def __init__(
        self,
        redis_url: str = None,
        default_limit: int = 1000,
        window_seconds: int = 3600
    ):
        self.redis_client: Optional[redis.Redis] = None
        self.default_limit = default_limit
        self.window_seconds = window_seconds

        # In-memory fallback
        self.memory_store: Dict[str, list] = defaultdict(list)

        if redis_url:
            self.redis_url = redis_url
        else:
            self.redis_url = settings.redis_url

    async def initialize(self):
        """Initialize Redis connection."""
        try:
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            logger.info("rate_limiter_initialized", backend="redis")
        except Exception as e:
            logger.warning("redis_unavailable", error=str(e), fallback="memory")

    async def is_allowed(
        self,
        key: str,
        limit: Optional[int] = None,
        window: Optional[int] = None
    ) -> tuple[bool, dict]:
        """
        Check if request is allowed under rate limit.

        Returns:
            (allowed: bool, info: dict)
        """
        limit = limit or self.default_limit
        window = window or self.window_seconds
        current_time = time.time()

        try:
            if self.redis_client:
                return await self._check_redis(key, limit, window, current_time)
            else:
                return await self._check_memory(key, limit, window, current_time)
        except Exception as e:
            logger.error("rate_limit_check_failed", error=str(e))
            # Fail open - allow request if rate limiter fails
            return True, {"error": str(e)}

    async def _check_redis(
        self,
        key: str,
        limit: int,
        window: int,
        current_time: float
    ) -> tuple[bool, dict]:
        """Check rate limit using Redis."""
        window_start = current_time - window

        # Use Redis sorted set for sliding window
        pipe = self.redis_client.pipeline()

        # Remove old entries
        pipe.zremrangebyscore(key, 0, window_start)

        # Count entries in current window
        pipe.zcard(key)

        # Add current request
        pipe.zadd(key, {str(current_time): current_time})

        # Set expiry
        pipe.expire(key, window)

        results = await pipe.execute()
        count = results[1]

        info = {
            "limit": limit,
            "remaining": max(0, limit - count - 1),
            "reset": int(current_time + window)
        }

        allowed = count < limit

        if not allowed:
            logger.warning("rate_limit_exceeded", key=key, count=count, limit=limit)

        return allowed, info

    async def _check_memory(
        self,
        key: str,
        limit: int,
        window: int,
        current_time: float
    ) -> tuple[bool, dict]:
        """Check rate limit using in-memory store."""
        window_start = current_time - window

        # Remove old entries
        self.memory_store[key] = [
            t for t in self.memory_store[key]
            if t > window_start
        ]

        # Count entries
        count = len(self.memory_store[key])

        info = {
            "limit": limit,
            "remaining": max(0, limit - count - 1),
            "reset": int(current_time + window)
        }

        allowed = count < limit

        if allowed:
            # Add current timestamp
            self.memory_store[key].append(current_time)
        else:
            logger.warning("rate_limit_exceeded", key=key, count=count, limit=limit)

        return allowed, info

    async def reset(self, key: str):
        """Reset rate limit for a key."""
        try:
            if self.redis_client:
                await self.redis_client.delete(key)
            else:
                self.memory_store.pop(key, None)

            logger.info("rate_limit_reset", key=key)
        except Exception as e:
            logger.error("rate_limit_reset_failed", key=key, error=str(e))

    async def close(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()


# Global rate limiter instance
rate_limiter = RateLimiter()


# ============================================================================
# Rate Limiting Middleware
# ============================================================================

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware for request rate limiting.
    """

    def __init__(
        self,
        app,
        limit: int = 1000,
        window: int = 3600,
        key_func: callable = None
    ):
        super().__init__(app)
        self.limit = limit
        self.window = window
        self.key_func = key_func or self._default_key_func

    def _default_key_func(self, request: Request) -> str:
        """Default key function using client IP."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0]
        else:
            client_ip = request.client.host

        return f"rate_limit:{client_ip}"

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/monitoring/health/live", "/monitoring/health/ready"]:
            return await call_next(request)

        # Get rate limit key
        key = self.key_func(request)

        # Check rate limit
        allowed, info = await rate_limiter.is_allowed(
            key,
            limit=self.limit,
            window=self.window
        )

        # Add rate limit headers
        response = None
        if allowed:
            response = await call_next(request)
        else:
            response = HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later."
            )

        # Add headers if we have a response
        if hasattr(response, 'headers'):
            response.headers["X-RateLimit-Limit"] = str(info["limit"])
            response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
            response.headers["X-RateLimit-Reset"] = str(info["reset"])

        if not allowed:
            raise response

        return response


# ============================================================================
# Decorator for Route-Specific Rate Limiting
# ============================================================================

def rate_limit(limit: int = 100, window: int = 60):
    """
    Decorator for route-specific rate limiting.

    Args:
        limit: Maximum requests allowed
        window: Time window in seconds
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract request from kwargs
            request = kwargs.get("request")
            if not request:
                # Try to find request in args
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break

            if request:
                # Build key from IP and endpoint
                key = f"rate_limit:{request.client.host}:{request.url.path}"

                # Check rate limit
                allowed, info = await rate_limiter.is_allowed(
                    key,
                    limit=limit,
                    window=window
                )

                if not allowed:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=f"Rate limit exceeded. Try again in {info['reset'] - time.time():.0f} seconds.",
                        headers={
                            "X-RateLimit-Limit": str(info["limit"]),
                            "X-RateLimit-Remaining": str(info["remaining"]),
                            "X-RateLimit-Reset": str(info["reset"])
                        }
                    )

            return await func(*args, **kwargs)

        return wrapper
    return decorator


# ============================================================================
# Token Bucket Rate Limiter
# ============================================================================

class TokenBucket:
    """
    Token bucket rate limiter for burst protection.
    """

    def __init__(
        self,
        capacity: int = 100,
        refill_rate: float = 10.0  # tokens per second
    ):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.buckets: Dict[str, dict] = {}

    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed."""
        now = time.time()

        if key not in self.buckets:
            self.buckets[key] = {
                "tokens": self.capacity,
                "last_refill": now
            }

        bucket = self.buckets[key]

        # Refill tokens
        elapsed = now - bucket["last_refill"]
        tokens_to_add = elapsed * self.refill_rate
        bucket["tokens"] = min(self.capacity, bucket["tokens"] + tokens_to_add)
        bucket["last_refill"] = now

        # Check if token available
        if bucket["tokens"] >= 1:
            bucket["tokens"] -= 1
            return True
        else:
            return False

    def reset(self, key: str):
        """Reset bucket for key."""
        self.buckets.pop(key, None)


# ============================================================================
# Rate Limit Helpers
# ============================================================================

async def get_rate_limit_status(key: str) -> dict:
    """Get current rate limit status for a key."""
    current_time = time.time()

    allowed, info = await rate_limiter.is_allowed(key, limit=0)  # Check without incrementing

    return {
        "key": key,
        "limit": info.get("limit", 0),
        "remaining": info.get("remaining", 0),
        "reset_at": datetime.fromtimestamp(info.get("reset", current_time)).isoformat(),
        "reset_in_seconds": max(0, info.get("reset", current_time) - current_time)
    }


async def clear_rate_limit(key: str):
    """Clear rate limit for a specific key."""
    await rate_limiter.reset(key)
    logger.info("rate_limit_cleared", key=key)
