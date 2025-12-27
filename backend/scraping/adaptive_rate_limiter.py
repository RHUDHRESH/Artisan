"""
Adaptive rate limiting system for web scraping
Adjusts delays based on domain behavior and response patterns
"""
import asyncio
import time
from typing import Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import random
from loguru import logger
import statistics


@dataclass
class DomainRateLimit:
    """Rate limiting configuration for a specific domain"""
    base_delay: float = 1.0
    current_delay: float = 1.0
    min_delay: float = 0.5
    max_delay: float = 30.0
    max_requests_per_minute: int = 30
    consecutive_failures: int = 0
    last_request_time: Optional[datetime] = None
    recent_response_times: deque = field(default_factory=lambda: deque(maxlen=20))
    recent_success_rate: deque = field(default_factory=lambda: deque(maxlen=10))
    
    def update_success(self, response_time: float):
        """Update metrics after successful request"""
        self.recent_response_times.append(response_time)
        self.recent_success_rate.append(1)
        self.consecutive_failures = 0
        self.last_request_time = datetime.now()
        
        # Decrease delay if we're being successful
        if len(self.recent_success_rate) >= 5:
            recent_success = statistics.mean(self.recent_success_rate)
            if recent_success >= 0.9:
                self.current_delay = max(self.min_delay, self.current_delay * 0.9)
    
    def update_failure(self, error_type: str = "unknown"):
        """Update metrics after failed request"""
        self.recent_success_rate.append(0)
        self.consecutive_failures += 1
        self.last_request_time = datetime.now()
        
        # Increase delay based on failure type
        if "rate limit" in error_type.lower():
            self.current_delay = min(self.max_delay, self.current_delay * 2.0)
        elif "timeout" in error_type.lower():
            self.current_delay = min(self.max_delay, self.current_delay * 1.5)
        elif "blocked" in error_type.lower() or "ban" in error_type.lower():
            self.current_delay = min(self.max_delay, self.current_delay * 3.0)
        else:
            self.current_delay = min(self.max_delay, self.current_delay * 1.2)
    
    def get_next_delay(self) -> float:
        """Get delay for next request"""
        # Add randomization to appear more human
        jitter = random.uniform(0.8, 1.2)
        return self.current_delay * jitter
    
    def get_success_rate(self) -> float:
        """Get recent success rate"""
        if not self.recent_success_rate:
            return 1.0
        return statistics.mean(self.recent_success_rate)
    
    def get_average_response_time(self) -> float:
        """Get average response time"""
        if not self.recent_response_times:
            return 0.0
        return statistics.mean(self.recent_response_times)


class AdaptiveRateLimiter:
    """Adaptive rate limiting that adjusts based on domain behavior"""
    
    def __init__(self, default_delay: float = 1.0, max_concurrent: int = 5):
        self.default_delay = default_delay
        self.max_concurrent = max_concurrent
        self.domain_limits: Dict[str, DomainRateLimit] = {}
        self.concurrent_requests: Dict[str, int] = defaultdict(int)
        self.request_locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        self.global_lock = asyncio.Lock()
        
        # Global rate limiting
        self.global_requests_per_minute = 100
        self.global_request_times: deque = deque(maxlen=100)
    
    def get_domain_config(self, domain: str) -> DomainRateLimit:
        """Get or create rate limit config for domain"""
        if domain not in self.domain_limits:
            self.domain_limits[domain] = DomainRateLimit(base_delay=self.default_delay)
        return self.domain_limits[domain]
    
    async def acquire(self, domain: str) -> None:
        """Acquire permission to make a request"""
        # Check global rate limiting
        await self._check_global_rate_limit()
        
        # Check domain-specific rate limiting
        domain_config = self.get_domain_config(domain)
        
        async with self.request_locks[domain]:
            # Check concurrent request limit
            while self.concurrent_requests[domain] >= self.max_concurrent:
                await asyncio.sleep(0.1)
            
            # Calculate delay based on last request
            if domain_config.last_request_time:
                time_since_last = datetime.now() - domain_config.last_request_time
                required_delay = domain_config.get_next_delay()
                
                if time_since_last.total_seconds() < required_delay:
                    sleep_time = required_delay - time_since_last.total_seconds()
                    await asyncio.sleep(sleep_time)
            
            self.concurrent_requests[domain] += 1
    
    def release(self, domain: str, success: bool, response_time: float = 0.0, error_type: str = "unknown"):
        """Release request and update metrics"""
        domain_config = self.get_domain_config(domain)
        
        if success:
            domain_config.update_success(response_time)
        else:
            domain_config.update_failure(error_type)
        
        self.concurrent_requests[domain] = max(0, self.concurrent_requests[domain] - 1)
        
        # Log significant changes
        if domain_config.current_delay > domain_config.base_delay * 2:
            logger.warning(f"Increased delay for {domain} to {domain_config.current_delay:.2f}s due to failures")
    
    async def _check_global_rate_limit(self):
        """Check global rate limiting"""
        now = time.time()
        
        # Clean old requests (older than 1 minute)
        self.global_request_times = deque([
            req_time for req_time in self.global_request_times 
            if now - req_time < 60
        ], maxlen=100)
        
        # Check if we're at the global limit
        if len(self.global_request_times) >= self.global_requests_per_minute:
            oldest_request = min(self.global_request_times)
            sleep_time = 60 - (now - oldest_request)
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
        
        self.global_request_times.append(now)
    
    def get_domain_stats(self, domain: str) -> Dict[str, Any]:
        """Get statistics for a domain"""
        config = self.get_domain_config(domain)
        
        return {
            'domain': domain,
            'current_delay': config.current_delay,
            'base_delay': config.base_delay,
            'success_rate': config.get_success_rate(),
            'average_response_time': config.get_average_response_time(),
            'consecutive_failures': config.consecutive_failures,
            'concurrent_requests': self.concurrent_requests[domain],
            'last_request': config.last_request_time.isoformat() if config.last_request_time else None
        }
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics for all domains"""
        stats = {
            'global': {
                'requests_per_minute': len(self.global_request_times),
                'max_concurrent': self.max_concurrent,
                'total_domains': len(self.domain_limits)
            },
            'domains': {}
        }
        
        for domain in self.domain_limits:
            stats['domains'][domain] = self.get_domain_stats(domain)
        
        return stats
    
    def reset_domain(self, domain: str):
        """Reset rate limiting for a domain"""
        if domain in self.domain_limits:
            del self.domain_limits[domain]
        if domain in self.concurrent_requests:
            del self.concurrent_requests[domain]
        if domain in self.request_locks:
            del self.request_locks[domain]
        
        logger.info(f"Reset rate limiting for {domain}")
    
    def adjust_domain_config(self, domain: str, **kwargs):
        """Manually adjust domain configuration"""
        config = self.get_domain_config(domain)
        
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        logger.info(f"Adjusted config for {domain}: {kwargs}")


class SmartRateLimiter:
    """Smart rate limiter with machine learning-like behavior"""
    
    def __init__(self):
        self.adaptive_limiter = AdaptiveRateLimiter()
        self.domain_patterns: Dict[str, Dict] = {}
        self.learning_enabled = True
    
    async def make_request(self, domain: str, request_func, *args, **kwargs):
        """Make a request with smart rate limiting"""
        await self.adaptive_limiter.acquire(domain)
        
        start_time = time.time()
        success = False
        error_type = "unknown"
        result = None
        
        try:
            result = await request_func(*args, **kwargs)
            success = True
            return result
            
        except asyncio.TimeoutError:
            error_type = "timeout"
            raise
            
        except Exception as e:
            error_type = str(e).lower()
            raise
            
        finally:
            response_time = time.time() - start_time
            self.adaptive_limiter.release(domain, success, response_time, error_type)
            
            # Learn from the request
            if self.learning_enabled:
                self._learn_from_request(domain, success, response_time, error_type)
    
    def _learn_from_request(self, domain: str, success: bool, response_time: float, error_type: str):
        """Learn from request patterns to improve rate limiting"""
        if domain not in self.domain_patterns:
            self.domain_patterns[domain] = {
                'optimal_delay': 1.0,
                'failure_patterns': defaultdict(int),
                'success_patterns': defaultdict(int)
            }
        
        patterns = self.domain_patterns[domain]
        
        if success:
            patterns['success_patterns']['fast_response'] += response_time < 2.0
            patterns['success_patterns']['slow_response'] += response_time >= 2.0
        else:
            patterns['failure_patterns'][error_type] += 1
            
            # Adjust optimal delay based on failure patterns
            if 'rate limit' in error_type:
                patterns['optimal_delay'] *= 1.5
            elif 'timeout' in error_type:
                patterns['optimal_delay'] *= 1.2
    
    def get_optimal_delay(self, domain: str) -> float:
        """Get learned optimal delay for domain"""
        if domain in self.domain_patterns:
            return self.domain_patterns[domain]['optimal_delay']
        return self.adaptive_limiter.default_delay


# Global rate limiter instance
_global_rate_limiter: Optional[AdaptiveRateLimiter] = None
_global_smart_limiter: Optional[SmartRateLimiter] = None


def get_rate_limiter() -> AdaptiveRateLimiter:
    """Get global adaptive rate limiter"""
    global _global_rate_limiter
    if _global_rate_limiter is None:
        _global_rate_limiter = AdaptiveRateLimiter()
    return _global_rate_limiter


def get_smart_rate_limiter() -> SmartRateLimiter:
    """Get global smart rate limiter"""
    global _global_smart_limiter
    if _global_smart_limiter is None:
        _global_smart_limiter = SmartRateLimiter()
    return _global_smart_limiter


async def rate_limited_request(domain: str, request_func, *args, **kwargs):
    """Convenience function for rate-limited requests"""
    limiter = get_smart_rate_limiter()
    return await limiter.make_request(domain, request_func, *args, **kwargs)
