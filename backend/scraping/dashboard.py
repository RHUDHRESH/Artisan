"""
Scraping dashboard and analytics system
Provides real-time monitoring and analytics for web scraping operations
"""
import asyncio
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from collections import defaultdict, deque
import time
from loguru import logger


@dataclass
class ScrapingMetrics:
    """Real-time scraping metrics"""
    timestamp: datetime
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    average_response_time: float = 0.0
    requests_per_minute: float = 0.0
    active_proxies: int = 0
    banned_proxies: int = 0
    rate_limit_hits: int = 0
    bot_detection_hits: int = 0
    
    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100
    
    @property
    def cache_hit_rate(self) -> float:
        total_cache = self.cache_hits + self.cache_misses
        if total_cache == 0:
            return 0.0
        return (self.cache_hits / total_cache) * 100


@dataclass
class DomainMetrics:
    """Domain-specific metrics"""
    domain: str
    requests: int = 0
    successes: int = 0
    failures: int = 0
    avg_response_time: float = 0.0
    last_request: Optional[datetime] = None
    current_delay: float = 1.0
    status: str = "active"
    
    @property
    def success_rate(self) -> float:
        if self.requests == 0:
            return 0.0
        return (self.successes / self.requests) * 100


class ScrapingAnalytics:
    """Analytics engine for scraping operations"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.metrics_history: deque = deque(maxlen=max_history)
        self.domain_metrics: Dict[str, DomainMetrics] = {}
        self.error_patterns: Dict[str, int] = defaultdict(int)
        self.hourly_stats: Dict[str, ScrapingMetrics] = {}
        self.daily_stats: Dict[str, ScrapingMetrics] = {}
        
        # Real-time counters
        self.current_requests = 0
        self.start_time = datetime.now()
    
    def record_request(self, domain: str, success: bool, response_time: float, 
                     cache_hit: bool = False, error_type: str = None):
        """Record a scraping request"""
        now = datetime.now()
        
        # Update current metrics
        self.current_requests += 1
        
        # Update domain metrics
        if domain not in self.domain_metrics:
            self.domain_metrics[domain] = DomainMetrics(domain=domain)
        
        domain_metric = self.domain_metrics[domain]
        domain_metric.requests += 1
        domain_metric.last_request = now
        
        if success:
            domain_metric.successes += 1
            # Update average response time
            if domain_metric.avg_response_time == 0:
                domain_metric.avg_response_time = response_time
            else:
                domain_metric.avg_response_time = (
                    domain_metric.avg_response_time * 0.8 + response_time * 0.2
                )
        else:
            domain_metric.failures += 1
            if error_type:
                self.error_patterns[error_type] += 1
        
        # Create current snapshot
        current_metrics = self._create_current_metrics()
        self.metrics_history.append(current_metrics)
        
        # Update time-based stats
        self._update_hourly_stats(current_metrics, now)
        self._update_daily_stats(current_metrics, now)
    
    def _create_current_metrics(self) -> ScrapingMetrics:
        """Create current metrics snapshot"""
        total_requests = sum(dm.requests for dm in self.domain_metrics.values())
        successful_requests = sum(dm.successes for dm in self.domain_metrics.values())
        failed_requests = sum(dm.failures for dm in self.domain_metrics.values())
        
        # Calculate requests per minute
        elapsed = (datetime.now() - self.start_time).total_seconds() / 60
        requests_per_minute = total_requests / elapsed if elapsed > 0 else 0
        
        return ScrapingMetrics(
            timestamp=datetime.now(),
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            requests_per_minute=requests_per_minute
        )
    
    def _update_hourly_stats(self, metrics: ScrapingMetrics, now: datetime):
        """Update hourly statistics"""
        hour_key = now.strftime("%Y-%m-%d %H:00")
        if hour_key not in self.hourly_stats:
            self.hourly_stats[hour_key] = metrics
        else:
            # Aggregate metrics
            existing = self.hourly_stats[hour_key]
            existing.total_requests += metrics.total_requests
            existing.successful_requests += metrics.successful_requests
            existing.failed_requests += metrics.failed_requests
    
    def _update_daily_stats(self, metrics: ScrapingMetrics, now: datetime):
        """Update daily statistics"""
        day_key = now.strftime("%Y-%m-%d")
        if day_key not in self.daily_stats:
            self.daily_stats[day_key] = metrics
        else:
            # Aggregate metrics
            existing = self.daily_stats[day_key]
            existing.total_requests += metrics.total_requests
            existing.successful_requests += metrics.successful_requests
            existing.failed_requests += metrics.failed_requests
    
    def get_real_time_dashboard(self) -> Dict[str, Any]:
        """Get real-time dashboard data"""
        current = self._create_current_metrics()
        
        # Get top domains by requests
        top_domains = sorted(
            self.domain_metrics.values(),
            key=lambda x: x.requests,
            reverse=True
        )[:10]
        
        # Get recent error patterns
        recent_errors = dict(sorted(
            self.error_patterns.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5])
        
        return {
            'timestamp': current.timestamp.isoformat(),
            'uptime': str(datetime.now() - self.start_time),
            'current_metrics': asdict(current),
            'top_domains': [asdict(dm) for dm in top_domains],
            'error_patterns': recent_errors,
            'total_domains': len(self.domain_metrics),
            'active_requests': self.current_requests
        }
    
    def get_performance_report(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance report for specified hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # Filter metrics by time
        recent_metrics = [
            m for m in self.metrics_history 
            if m.timestamp >= cutoff_time
        ]
        
        if not recent_metrics:
            return {'error': 'No data available for specified period'}
        
        # Calculate aggregates
        total_requests = sum(m.total_requests for m in recent_metrics)
        successful_requests = sum(m.successful_requests for m in recent_metrics)
        avg_response_time = sum(m.average_response_time for m in recent_metrics) / len(recent_metrics)
        
        # Performance trends
        success_rates = [m.success_rate for m in recent_metrics]
        response_times = [m.average_response_time for m in recent_metrics]
        
        return {
            'period_hours': hours,
            'total_requests': total_requests,
            'successful_requests': successful_requests,
            'overall_success_rate': (successful_requests / total_requests * 100) if total_requests > 0 else 0,
            'average_response_time': avg_response_time,
            'performance_trends': {
                'success_rate_trend': 'improving' if len(success_rates) > 1 and success_rates[-1] > success_rates[0] else 'declining',
                'response_time_trend': 'improving' if len(response_times) > 1 and response_times[-1] < response_times[0] else 'declining'
            },
            'domain_performance': [
                {
                    'domain': dm.domain,
                    'requests': dm.requests,
                    'success_rate': dm.success_rate,
                    'avg_response_time': dm.avg_response_time
                }
                for dm in sorted(self.domain_metrics.values(), key=lambda x: x.requests, reverse=True)[:10]
            ]
        }
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get health summary"""
        current = self._create_current_metrics()
        
        # Health indicators
        health_score = 100.0
        
        # Success rate impact
        if current.success_rate < 90:
            health_score -= (90 - current.success_rate) * 0.5
        
        # Response time impact
        if current.average_response_time > 5:
            health_score -= min(20, (current.average_response_time - 5) * 2)
        
        # Error rate impact
        error_rate = (current.failed_requests / current.total_requests * 100) if current.total_requests > 0 else 0
        if error_rate > 10:
            health_score -= min(30, (error_rate - 10) * 1.5)
        
        health_score = max(0, health_score)
        
        # Determine status
        if health_score >= 90:
            status = "excellent"
        elif health_score >= 75:
            status = "good"
        elif health_score >= 60:
            status = "fair"
        elif health_score >= 40:
            status = "poor"
        else:
            status = "critical"
        
        return {
            'health_score': health_score,
            'status': status,
            'indicators': {
                'success_rate': current.success_rate,
                'average_response_time': current.average_response_time,
                'error_rate': error_rate,
                'total_requests': current.total_requests
            },
            'recommendations': self._get_health_recommendations(health_score, current)
        }
    
    def _get_health_recommendations(self, score: float, metrics: ScrapingMetrics) -> List[str]:
        """Get health recommendations based on score and metrics"""
        recommendations = []
        
        if score < 60:
            recommendations.append("System health is poor - immediate attention required")
        
        if metrics.success_rate < 85:
            recommendations.append("Success rate is low - check for blocked domains or proxy issues")
        
        if metrics.average_response_time > 5:
            recommendations.append("Response times are high - consider optimizing requests or using faster proxies")
        
        if metrics.cache_hit_rate < 30:
            recommendations.append("Cache hit rate is low - consider increasing cache TTL or cache size")
        
        if len(self.error_patterns) > 5:
            recommendations.append("Multiple error patterns detected - review error handling")
        
        if not recommendations:
            recommendations.append("System is performing well")
        
        return recommendations


class ScrapingDashboard:
    """Main dashboard class"""
    
    def __init__(self):
        self.analytics = ScrapingAnalytics()
        self.is_running = False
        self.update_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start dashboard"""
        if self.is_running:
            return
        
        self.is_running = True
        self.update_task = asyncio.create_task(self._update_loop())
        logger.info("Started scraping dashboard")
    
    async def stop(self):
        """Stop dashboard"""
        self.is_running = False
        if self.update_task:
            self.update_task.cancel()
            try:
                await self.update_task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped scraping dashboard")
    
    async def _update_loop(self):
        """Background update loop"""
        while self.is_running:
            try:
                # Update metrics from various sources
                await self._collect_metrics()
                await asyncio.sleep(30)  # Update every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Dashboard update error: {e}")
                await asyncio.sleep(60)
    
    async def _collect_metrics(self):
        """Collect metrics from various sources"""
        try:
            # Collect from monitor
            from backend.scraping.scraper_monitor import get_monitor
            monitor = get_monitor()
            metrics = monitor.get_metrics_summary()
            
            # Update analytics with monitor data
            # This would need to be adapted based on actual monitor data structure
            
        except Exception as e:
            logger.debug(f"Failed to collect monitor metrics: {e}")
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get complete dashboard data"""
        return {
            'real_time': self.analytics.get_real_time_dashboard(),
            'performance_24h': self.analytics.get_performance_report(24),
            'performance_7d': self.analytics.get_performance_report(24 * 7),
            'health': self.analytics.get_health_summary(),
            'timestamp': datetime.now().isoformat()
        }
    
    def export_data(self, format: str = "json") -> str:
        """Export dashboard data"""
        data = self.get_dashboard_data()
        
        if format.lower() == "json":
            return json.dumps(data, indent=2, default=str)
        else:
            raise ValueError(f"Unsupported format: {format}")


# Global dashboard instance
_global_dashboard: Optional[ScrapingDashboard] = None


def get_dashboard() -> ScrapingDashboard:
    """Get global dashboard instance"""
    global _global_dashboard
    if _global_dashboard is None:
        _global_dashboard = ScrapingDashboard()
    return _global_dashboard


async def start_dashboard():
    """Start the dashboard"""
    dashboard = get_dashboard()
    await dashboard.start()


async def stop_dashboard():
    """Stop the dashboard"""
    dashboard = get_dashboard()
    await dashboard.stop()


def get_dashboard_data() -> Dict[str, Any]:
    """Get dashboard data"""
    dashboard = get_dashboard()
    return dashboard.get_dashboard_data()
