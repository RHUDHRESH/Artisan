"""
Scraping health checks and auto-recovery system
Monitors scraping health and automatically recovers from failures
"""
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from loguru import logger
import time
import traceback


class HealthStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    RECOVERING = "recovering"
    FAILED = "failed"


@dataclass
class HealthCheck:
    """Individual health check configuration"""
    name: str
    check_func: Callable
    interval: int = 60  # seconds
    timeout: int = 30
    max_failures: int = 3
    recovery_func: Optional[Callable] = None
    enabled: bool = True
    
    # Runtime state
    last_check: Optional[datetime] = None
    consecutive_failures: int = 0
    status: HealthStatus = HealthStatus.HEALTHY
    last_error: Optional[str] = None
    recovery_attempts: int = 0


@dataclass
class SystemHealth:
    """Overall system health status"""
    status: HealthStatus = HealthStatus.HEALTHY
    total_checks: int = 0
    healthy_checks: int = 0
    warning_checks: int = 0
    critical_checks: int = 0
    last_update: datetime = field(default_factory=datetime.now)
    issues: List[str] = field(default_factory=list)
    
    @property
    def health_score(self) -> float:
        """Calculate overall health score (0-100)"""
        if self.total_checks == 0:
            return 100.0
        
        healthy_weight = self.healthy_checks * 1.0
        warning_weight = self.warning_checks * 0.5
        critical_weight = self.critical_checks * 0.1
        
        return ((healthy_weight + warning_weight + critical_weight) / self.total_checks) * 100


class ScrapingHealthMonitor:
    """Comprehensive health monitoring for scraping system"""
    
    def __init__(self):
        self.health_checks: Dict[str, HealthCheck] = {}
        self.system_health = SystemHealth()
        self.monitoring_task: Optional[asyncio.Task] = None
        self.is_monitoring = False
        self.alert_callbacks: List[Callable] = []
        
        # Auto-recovery settings
        self.auto_recovery_enabled = True
        self.max_recovery_attempts = 3
        self.recovery_backoff_factor = 2.0
        
        # Default health checks
        self._setup_default_checks()
    
    def _setup_default_checks(self):
        """Setup default health checks"""
        
        # API connectivity check
        self.add_health_check(
            name="tavily_api",
            check_func=self._check_tavily_api,
            interval=300,
            timeout=30,
            recovery_func=self._recover_api_connection
        )
        
        # Cache health check
        self.add_health_check(
            name="cache_system",
            check_func=self._check_cache_system,
            interval=180,
            timeout=10,
            recovery_func=self._recover_cache_system
        )
        
        # Proxy pool health
        self.add_health_check(
            name="proxy_pool",
            check_func=self._check_proxy_pool,
            interval=240,
            timeout=15,
            recovery_func=self._recover_proxy_pool
        )
        
        # Rate limiter health
        self.add_health_check(
            name="rate_limiter",
            check_func=self._check_rate_limiter,
            interval=120,
            timeout=5
        )
        
        # Memory usage check
        self.add_health_check(
            name="memory_usage",
            check_func=self._check_memory_usage,
            interval=60,
            timeout=5
        )
    
    def add_health_check(self, name: str, check_func: Callable, **kwargs):
        """Add a new health check"""
        health_check = HealthCheck(name=name, check_func=check_func, **kwargs)
        self.health_checks[name] = health_check
        logger.info(f"Added health check: {name}")
    
    def remove_health_check(self, name: str):
        """Remove a health check"""
        if name in self.health_checks:
            del self.health_checks[name]
            logger.info(f"Removed health check: {name}")
    
    def add_alert_callback(self, callback: Callable):
        """Add callback for health alerts"""
        self.alert_callbacks.append(callback)
    
    async def start_monitoring(self):
        """Start continuous health monitoring"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Started health monitoring")
    
    async def stop_monitoring(self):
        """Stop health monitoring"""
        self.is_monitoring = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped health monitoring")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                await self._run_health_checks()
                await self._update_system_health()
                await asyncio.sleep(30)  # Check every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _run_health_checks(self):
        """Run all enabled health checks"""
        tasks = []
        
        for name, check in self.health_checks.items():
            if check.enabled:
                task = asyncio.create_task(self._run_single_check(name, check))
                tasks.append(task)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _run_single_check(self, name: str, check: HealthCheck):
        """Run a single health check"""
        try:
            # Skip if not enough time has passed
            if check.last_check:
                time_since = datetime.now() - check.last_check
                if time_since.total_seconds() < check.interval:
                    return
            
            # Run the check
            start_time = time.time()
            result = await asyncio.wait_for(check.check_func(), timeout=check.timeout)
            check_time = time.time() - start_time
            
            # Update check status
            check.last_check = datetime.now()
            
            if result:
                check.consecutive_failures = 0
                check.status = HealthStatus.HEALTHY
                check.last_error = None
                check.recovery_attempts = 0
                
                if check_time > check.timeout * 0.8:
                    logger.warning(f"Health check {name} is slow: {check_time:.2f}s")
                else:
                    logger.debug(f"Health check {name} passed")
            else:
                await self._handle_check_failure(name, check)
                
        except asyncio.TimeoutError:
            await self._handle_check_failure(name, check, "timeout")
        except Exception as e:
            await self._handle_check_failure(name, check, str(e))
    
    async def _handle_check_failure(self, name: str, check: HealthCheck, error: str = "unknown"):
        """Handle health check failure"""
        check.consecutive_failures += 1
        check.last_error = error
        check.last_check = datetime.now()
        
        # Determine status based on failures
        if check.consecutive_failures >= check.max_failures:
            check.status = HealthStatus.CRITICAL
        elif check.consecutive_failures >= check.max_failures // 2:
            check.status = HealthStatus.WARNING
        else:
            check.status = HealthStatus.WARNING
        
        logger.warning(f"Health check {name} failed: {error} (consecutive: {check.consecutive_failures})")
        
        # Trigger auto-recovery if enabled
        if self.auto_recovery_enabled and check.recovery_func:
            await self._attempt_recovery(name, check)
        
        # Send alerts
        await self._send_alert(name, check)
    
    async def _attempt_recovery(self, name: str, check: HealthCheck):
        """Attempt to recover from a failed health check"""
        if check.recovery_attempts >= self.max_recovery_attempts:
            logger.error(f"Max recovery attempts reached for {name}")
            check.status = HealthStatus.FAILED
            return
        
        check.recovery_attempts += 1
        check.status = HealthStatus.RECOVERING
        
        try:
            logger.info(f"Attempting recovery for {name} (attempt {check.recovery_attempts})")
            
            # Calculate backoff delay
            backoff_delay = min(300, 30 * (self.recovery_backoff_factor ** (check.recovery_attempts - 1)))
            await asyncio.sleep(backoff_delay)
            
            # Run recovery function
            if check.recovery_func:
                await check.recovery_func()
            
            logger.info(f"Recovery completed for {name}")
            
        except Exception as e:
            logger.error(f"Recovery failed for {name}: {e}")
            check.status = HealthStatus.CRITICAL
    
    async def _update_system_health(self):
        """Update overall system health"""
        total = len(self.health_checks)
        healthy = sum(1 for c in self.health_checks.values() if c.status == HealthStatus.HEALTHY)
        warning = sum(1 for c in self.health_checks.values() if c.status == HealthStatus.WARNING)
        critical = sum(1 for c in self.health_checks.values() if c.status == HealthStatus.CRITICAL)
        failed = sum(1 for c in self.health_checks.values() if c.status == HealthStatus.FAILED)
        
        self.system_health.total_checks = total
        self.system_health.healthy_checks = healthy
        self.system_health.warning_checks = warning
        self.system_health.critical_checks = critical
        self.system_health.last_update = datetime.now()
        
        # Update issues list
        self.system_health.issues = []
        for name, check in self.health_checks.items():
            if check.status != HealthStatus.HEALTHY:
                self.system_health.issues.append(f"{name}: {check.status.value} ({check.last_error})")
        
        # Determine overall status
        if failed > 0:
            self.system_health.status = HealthStatus.FAILED
        elif critical > 0:
            self.system_health.status = HealthStatus.CRITICAL
        elif warning > 0:
            self.system_health.status = HealthStatus.WARNING
        else:
            self.system_health.status = HealthStatus.HEALTHY
        
        # Log significant changes
        if self.system_health.health_score < 70:
            logger.warning(f"System health degraded: {self.system_health.health_score:.1f}%")
    
    async def _send_alert(self, check_name: str, check: HealthCheck):
        """Send health alert"""
        alert_data = {
            'type': 'health_alert',
            'check_name': check_name,
            'status': check.status.value,
            'error': check.last_error,
            'consecutive_failures': check.consecutive_failures,
            'timestamp': datetime.now().isoformat()
        }
        
        for callback in self.alert_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(alert_data)
                else:
                    callback(alert_data)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")
    
    # Default health check implementations
    async def _check_tavily_api(self) -> bool:
        """Check Tavily API connectivity"""
        try:
            from backend.config import settings
            if not settings.tavily_api_key:
                return False
            
            async with aiohttp.ClientSession() as session:
                headers = {'Authorization': f'Bearer {settings.tavily_api_key}'}
                async with session.get('https://api.tavily.com', headers=headers, timeout=10) as response:
                    return response.status < 500
        except Exception:
            return False
    
    async def _check_cache_system(self) -> bool:
        """Check cache system health"""
        try:
            from backend.scraping.advanced_cache import get_cache
            cache = get_cache()
            stats = await cache.get_cache_stats()
            return 'error' not in stats
        except Exception:
            return False
    
    async def _check_proxy_pool(self) -> bool:
        """Check proxy pool health"""
        try:
            from backend.scraping.proxy_pool import SimpleProxyPool
            pool = SimpleProxyPool()
            return len(pool.proxies) > 0
        except Exception:
            return False
    
    async def _check_rate_limiter(self) -> bool:
        """Check rate limiter health"""
        try:
            from backend.scraping.adaptive_rate_limiter import get_rate_limiter
            limiter = get_rate_limiter()
            return True  # Rate limiter should always be available
        except Exception:
            return False
    
    async def _check_memory_usage(self) -> bool:
        """Check memory usage"""
        try:
            import psutil
            memory_percent = psutil.virtual_memory().percent
            return memory_percent < 90
        except Exception:
            return True  # Assume healthy if we can't check
    
    # Recovery implementations
    async def _recover_api_connection(self):
        """Recover API connection"""
        logger.info("Attempting API connection recovery")
        # Could implement connection reset, re-authentication, etc.
    
    async def _recover_cache_system(self):
        """Recover cache system"""
        logger.info("Attempting cache system recovery")
        try:
            from backend.scraping.advanced_cache import get_cache
            cache = get_cache()
            await cache.clear()
        except Exception as e:
            logger.error(f"Cache recovery failed: {e}")
    
    async def _recover_proxy_pool(self):
        """Recover proxy pool"""
        logger.info("Attempting proxy pool recovery")
        # Could implement proxy pool reset, reload proxies, etc.
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get comprehensive health summary"""
        return {
            'system_health': {
                'status': self.system_health.status.value,
                'health_score': self.system_health.health_score,
                'total_checks': self.system_health.total_checks,
                'healthy_checks': self.system_health.healthy_checks,
                'warning_checks': self.system_health.warning_checks,
                'critical_checks': self.system_health.critical_checks,
                'last_update': self.system_health.last_update.isoformat(),
                'issues': self.system_health.issues
            },
            'individual_checks': {
                name: {
                    'status': check.status.value,
                    'last_check': check.last_check.isoformat() if check.last_check else None,
                    'consecutive_failures': check.consecutive_failures,
                    'last_error': check.last_error,
                    'recovery_attempts': check.recovery_attempts
                }
                for name, check in self.health_checks.items()
            }
        }


# Global health monitor instance
_global_health_monitor: Optional[ScrapingHealthMonitor] = None


def get_health_monitor() -> ScrapingHealthMonitor:
    """Get global health monitor instance"""
    global _global_health_monitor
    if _global_health_monitor is None:
        _global_health_monitor = ScrapingHealthMonitor()
    return _global_health_monitor


async def start_health_monitoring():
    """Start health monitoring"""
    monitor = get_health_monitor()
    await monitor.start_monitoring()


async def stop_health_monitoring():
    """Stop health monitoring"""
    monitor = get_health_monitor()
    await monitor.stop_monitoring()
