"""
Advanced distributed caching system for web scraping
Supports both Redis and in-memory fallback
"""
import json
import pickle
import hashlib
import asyncio
from typing import Any, Optional, Dict, List, Union
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import redis.asyncio as redis
from diskcache import Cache as DiskCache
from loguru import logger
import os
from backend.config import settings


class CacheBackend(ABC):
    """Abstract base class for cache backends"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value by key"""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value with optional TTL"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete key"""
        pass
    
    @abstractmethod
    async def clear(self) -> bool:
        """Clear all cache"""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        pass
    
    @abstractmethod
    async def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching pattern"""
        pass


class RedisCache(CacheBackend):
    """Redis-based distributed cache"""
    
    def __init__(self, redis_url: str = None, key_prefix: str = "scraper:"):
        self.redis_url = redis_url or getattr(settings, 'redis_url', 'redis://localhost:6379')
        self.key_prefix = key_prefix
        self._client: Optional[redis.Redis] = None
        self._connected = False
    
    async def _ensure_connection(self):
        """Ensure Redis connection is established"""
        if not self._connected or not self._client:
            try:
                self._client = redis.from_url(self.redis_url, decode_responses=False)
                await self._client.ping()
                self._connected = True
                logger.info("Connected to Redis cache")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                self._connected = False
                raise
    
    def _make_key(self, key: str) -> str:
        """Add prefix to key"""
        return f"{self.key_prefix}{key}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis"""
        try:
            await self._ensure_connection()
            value = await self._client.get(self._make_key(key))
            if value is not None:
                return pickle.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis get error for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in Redis"""
        try:
            await self._ensure_connection()
            serialized = pickle.dumps(value)
            redis_key = self._make_key(key)
            
            if ttl:
                return await self._client.setex(redis_key, ttl, serialized)
            else:
                return await self._client.set(redis_key, serialized)
        except Exception as e:
            logger.error(f"Redis set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from Redis"""
        try:
            await self._ensure_connection()
            return bool(await self._client.delete(self._make_key(key)))
        except Exception as e:
            logger.error(f"Redis delete error for key {key}: {e}")
            return False
    
    async def clear(self) -> bool:
        """Clear all scraper keys from Redis"""
        try:
            await self._ensure_connection()
            pattern = self._make_key("*")
            keys = await self._client.keys(pattern)
            if keys:
                return bool(await self._client.delete(*keys))
            return True
        except Exception as e:
            logger.error(f"Redis clear error: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis"""
        try:
            await self._ensure_connection()
            return bool(await self._client.exists(self._make_key(key)))
        except Exception as e:
            logger.error(f"Redis exists error for key {key}: {e}")
            return False
    
    async def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching pattern"""
        try:
            await self._ensure_connection()
            redis_pattern = self._make_key(pattern)
            keys = await self._client.keys(redis_pattern)
            # Remove prefix from returned keys
            prefix_len = len(self.key_prefix)
            return [key.decode() if isinstance(key, bytes) else key][prefix_len:] for key in keys
        except Exception as e:
            logger.error(f"Redis keys error: {e}")
            return []
    
    async def close(self):
        """Close Redis connection"""
        if self._client:
            await self._client.close()
            self._connected = False


class DiskCacheBackend(CacheBackend):
    """Disk-based cache using diskcache library"""
    
    def __init__(self, cache_dir: str = "./data/cache/disk"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        self._cache = DiskCache(cache_dir)
        logger.info(f"Initialized disk cache at {cache_dir}")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from disk cache"""
        try:
            return self._cache.get(key)
        except Exception as e:
            logger.error(f"Disk cache get error for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in disk cache"""
        try:
            if ttl:
                expire = timedelta(seconds=ttl)
                return self._cache.set(key, value, expire=expire)
            else:
                return self._cache.set(key, value)
        except Exception as e:
            logger.error(f"Disk cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from disk cache"""
        try:
            return bool(self._cache.delete(key))
        except Exception as e:
            logger.error(f"Disk cache delete error for key {key}: {e}")
            return False
    
    async def clear(self) -> bool:
        """Clear disk cache"""
        try:
            self._cache.clear()
            return True
        except Exception as e:
            logger.error(f"Disk cache clear error: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in disk cache"""
        try:
            return key in self._cache
        except Exception as e:
            logger.error(f"Disk cache exists error for key {key}: {e}")
            return False
    
    async def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching pattern"""
        try:
            import fnmatch
            all_keys = list(self._cache.iterkeys())
            if pattern == "*":
                return all_keys
            return [key for key in all_keys if fnmatch.fnmatch(key, pattern)]
        except Exception as e:
            logger.error(f"Disk cache keys error: {e}")
            return []


class MemoryCache(CacheBackend):
    """In-memory cache with TTL support"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from memory cache"""
        async with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if entry["expires_at"] and datetime.now() > entry["expires_at"]:
                    del self._cache[key]
                    return None
                return entry["value"]
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in memory cache"""
        async with self._lock:
            # Implement LRU eviction if cache is full
            if len(self._cache) >= self.max_size and key not in self._cache:
                # Remove oldest entry
                oldest_key = min(self._cache.keys(), 
                               key=lambda k: self._cache[k]["created_at"])
                del self._cache[oldest_key]
            
            expires_at = None
            if ttl:
                expires_at = datetime.now() + timedelta(seconds=ttl)
            
            self._cache[key] = {
                "value": value,
                "created_at": datetime.now(),
                "expires_at": expires_at
            }
            return True
    
    async def delete(self, key: str) -> bool:
        """Delete key from memory cache"""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    async def clear(self) -> bool:
        """Clear memory cache"""
        async with self._lock:
            self._cache.clear()
            return True
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in memory cache"""
        async with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if entry["expires_at"] and datetime.now() > entry["expires_at"]:
                    del self._cache[key]
                    return False
                return True
            return False
    
    async def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching pattern"""
        async with self._lock:
            import fnmatch
            if pattern == "*":
                return list(self._cache.keys())
            return [key for key in self._cache.keys() if fnmatch.fnmatch(key, pattern)]


class HybridCache:
    """Hybrid cache that tries multiple backends in order"""
    
    def __init__(self, backends: List[CacheBackend]):
        self.backends = backends
        self.primary = backends[0] if backends else None
        self.fallbacks = backends[1:] if len(backends) > 1 else []
    
    async def get(self, key: str) -> Optional[Any]:
        """Try to get from primary, then fallbacks"""
        # Try primary first
        if self.primary:
            try:
                value = await self.primary.get(key)
                if value is not None:
                    return value
            except Exception as e:
                logger.warning(f"Primary cache failed for key {key}: {e}")
        
        # Try fallbacks
        for backend in self.fallbacks:
            try:
                value = await backend.get(key)
                if value is not None:
                    # Repopulate primary cache if possible
                    if self.primary:
                        try:
                            await self.primary.set(key, value)
                        except Exception:
                            pass  # Ignore repopulation errors
                    return value
            except Exception as e:
                logger.warning(f"Fallback cache failed for key {key}: {e}")
        
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set in all available backends"""
        success = False
        
        # Try primary first
        if self.primary:
            try:
                if await self.primary.set(key, value, ttl):
                    success = True
            except Exception as e:
                logger.warning(f"Primary cache set failed for key {key}: {e}")
        
        # Try fallbacks
        for backend in self.fallbacks:
            try:
                if await backend.set(key, value, ttl):
                    success = True
            except Exception as e:
                logger.warning(f"Fallback cache set failed for key {key}: {e}")
        
        return success
    
    async def delete(self, key: str) -> bool:
        """Delete from all backends"""
        success = False
        
        for backend in [self.primary] + self.fallbacks:
            if backend:
                try:
                    if await backend.delete(key):
                        success = True
                except Exception as e:
                    logger.warning(f"Cache delete failed for key {key}: {e}")
        
        return success
    
    async def clear(self) -> bool:
        """Clear all backends"""
        success = False
        
        for backend in [self.primary] + self.fallbacks:
            if backend:
                try:
                    if await backend.clear():
                        success = True
                except Exception as e:
                    logger.warning(f"Cache clear failed: {e}")
        
        return success
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in any backend"""
        for backend in [self.primary] + self.fallbacks:
            if backend:
                try:
                    if await backend.exists(key):
                        return True
                except Exception:
                    continue
        return False
    
    async def keys(self, pattern: str = "*") -> List[str]:
        """Get keys from primary backend"""
        if self.primary:
            try:
                return await self.primary.keys(pattern)
            except Exception as e:
                logger.warning(f"Cache keys failed: {e}")
        return []


class AdvancedScrapingCache:
    """Advanced caching system specifically for web scraping"""
    
    def __init__(self, cache_type: str = "hybrid", redis_url: str = None, 
                 disk_cache_dir: str = "./data/cache/disk", 
                 memory_size: int = 1000):
        """
        Initialize advanced cache
        
        Args:
            cache_type: Type of cache ('redis', 'disk', 'memory', 'hybrid')
            redis_url: Redis connection URL
            disk_cache_dir: Directory for disk cache
            memory_size: Max size for memory cache
        """
        self.cache_type = cache_type
        self.cache: Union[CacheBackend, HybridCache] = None
        self._setup_cache(cache_type, redis_url, disk_cache_dir, memory_size)
    
    def _setup_cache(self, cache_type: str, redis_url: str, disk_cache_dir: str, memory_size: int):
        """Setup cache based on type"""
        if cache_type == "redis":
            self.cache = RedisCache(redis_url)
        elif cache_type == "disk":
            self.cache = DiskCacheBackend(disk_cache_dir)
        elif cache_type == "memory":
            self.cache = MemoryCache(memory_size)
        elif cache_type == "hybrid":
            # Try Redis first, fallback to disk, then memory
            backends = []
            try:
                redis_cache = RedisCache(redis_url)
                # Test connection
                asyncio.create_task(redis_cache._ensure_connection())
                backends.append(redis_cache)
            except Exception:
                logger.warning("Redis not available, using fallback caches")
            
            backends.append(DiskCacheBackend(disk_cache_dir))
            backends.append(MemoryCache(memory_size))
            self.cache = HybridCache(backends)
        else:
            raise ValueError(f"Unknown cache type: {cache_type}")
        
        logger.info(f"Initialized {cache_type} cache for scraping")
    
    def _generate_key(self, url: str, method: str = "GET", **kwargs) -> str:
        """Generate cache key from URL and parameters"""
        key_data = f"{url}:{method}:{json.dumps(kwargs, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def get_search_results(self, query: str, region: str, num_results: int, 
                                sources: List[str], deep_search: bool) -> Optional[List[Dict]]:
        """Get cached search results"""
        key = self._generate_key(
            f"search:{query}", 
            region=region, 
            num_results=num_results, 
            sources=sources, 
            deep_search=deep_search
        )
        return await self.cache.get(key)
    
    async def set_search_results(self, query: str, region: str, num_results: int,
                                sources: List[str], deep_search: bool, 
                                results: List[Dict], ttl: int = 1800) -> bool:
        """Cache search results"""
        key = self._generate_key(
            f"search:{query}", 
            region=region, 
            num_results=num_results, 
            sources=sources, 
            deep_search=deep_search
        )
        return await self.cache.set(key, results, ttl)
    
    async def get_page_content(self, url: str, use_playwright: bool = False) -> Optional[str]:
        """Get cached page content"""
        key = self._generate_key(f"page:{url}", use_playwright=use_playwright)
        return await self.cache.get(key)
    
    async def set_page_content(self, url: str, content: str, use_playwright: bool = False,
                              ttl: int = 3600) -> bool:
        """Cache page content"""
        key = self._generate_key(f"page:{url}", use_playwright=use_playwright)
        return await self.cache.set(key, content, ttl)
    
    async def get_extracted_data(self, url: str, extraction_type: str) -> Optional[Dict]:
        """Get cached extracted data"""
        key = self._generate_key(f"extracted:{url}", type=extraction_type)
        return await self.cache.get(key)
    
    async def set_extracted_data(self, url: str, extraction_type: str, data: Dict,
                                 ttl: int = 7200) -> bool:
        """Cache extracted data"""
        key = self._generate_key(f"extracted:{url}", type=extraction_type)
        return await self.cache.set(key, data, ttl)
    
    async def get_rate_limit_info(self, domain: str) -> Optional[Dict]:
        """Get cached rate limit information"""
        key = f"rate_limit:{domain}"
        return await self.cache.get(key)
    
    async def set_rate_limit_info(self, domain: str, info: Dict, ttl: int = 300) -> bool:
        """Cache rate limit information"""
        key = f"rate_limit:{domain}"
        return await self.cache.set(key, info, ttl)
    
    async def get_proxy_performance(self, proxy_id: str) -> Optional[Dict]:
        """Get cached proxy performance data"""
        key = f"proxy_perf:{proxy_id}"
        return await self.cache.get(key)
    
    async def set_proxy_performance(self, proxy_id: str, performance: Dict, ttl: int = 600) -> bool:
        """Cache proxy performance data"""
        key = f"proxy_perf:{proxy_id}"
        return await self.cache.set(key, performance, ttl)
    
    async def clear_expired_cache(self) -> int:
        """Clear expired entries (implementation depends on backend)"""
        # This is a placeholder - actual implementation depends on backend capabilities
        if hasattr(self.cache, 'clear_expired'):
            return await self.cache.clear_expired()
        return 0
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            keys = await self.cache.keys("*")
            total_keys = len(keys)
            
            # Categorize keys
            search_keys = len([k for k in keys if k.startswith("search:")])
            page_keys = len([k for k in keys if k.startswith("page:")])
            extracted_keys = len([k for k in keys if k.startswith("extracted:")])
            rate_limit_keys = len([k for k in keys if k.startswith("rate_limit:")])
            proxy_keys = len([k for k in keys if k.startswith("proxy_perf:")])
            
            return {
                "total_keys": total_keys,
                "search_cache": search_keys,
                "page_cache": page_keys,
                "extracted_cache": extracted_keys,
                "rate_limit_cache": rate_limit_keys,
                "proxy_cache": proxy_keys,
                "cache_type": self.cache_type
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"error": str(e)}
    
    async def close(self):
        """Close cache connections"""
        if hasattr(self.cache, 'close'):
            await self.cache.close()


# Global cache instance
_global_cache: Optional[AdvancedScrapingCache] = None


def get_cache(cache_type: str = "hybrid") -> AdvancedScrapingCache:
    """Get or create global cache instance"""
    global _global_cache
    if _global_cache is None:
        _global_cache = AdvancedScrapingCache(cache_type=cache_type)
    return _global_cache


async def cleanup_cache():
    """Cleanup global cache"""
    global _global_cache
    if _global_cache:
        await _global_cache.close()
        _global_cache = None
