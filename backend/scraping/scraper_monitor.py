"""
Performance monitoring and metrics for web scraper
"""
import time
import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import json
import os


@dataclass
class ScrapingMetrics:
    """Metrics for scraping operations"""
    
    # Request metrics
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    
    # Performance metrics
    average_response_time: float = 0.0
    slowest_request: float = 0.0
    fastest_request: float = float('inf')
    
    # Error metrics
    timeout_errors: int = 0
    http_errors: int = 0
    connection_errors: int = 0
    bot_detection_blocks: int = 0
    
    # Provider metrics
    provider_stats: Dict[str, Dict[str, int]] = field(default_factory=dict)
    
    # Rate limiting metrics
    rate_limit_hits: int = 0
    concurrent_request_limit_hits: int = 0
    
    # Timestamps
    start_time: datetime = field(default_factory=datetime.now)
    last_request_time: Optional[datetime] = None
    
    # Response time history (for recent performance)
    recent_response_times: deque = field(default_factory=lambda: deque(maxlen=100))
    
    def update_request_metrics(self, success: bool, response_time: float, 
                             provider: str, error_type: Optional[str] = None,
                             cache_hit: bool = False) -> None:
        """Update metrics after a request"""
        self.total_requests += 1
        self.last_request_time = datetime.now()
        
        if cache_hit:
            self.cache_hits += 1
            return
        
        self.cache_misses += 1
        
        if success:
            self.successful_requests += 1
            
            # Update response time metrics
            self.recent_response_times.append(response_time)
            self.average_response_time = sum(self.recent_response_times) / len(self.recent_response_times)
            self.slowest_request = max(self.slowest_request, response_time)
            self.fastest_request = min(self.fastest_request, response_time)
            
            # Update provider stats
            if provider not in self.provider_stats:
                self.provider_stats[provider] = {"success": 0, "error": 0}
            self.provider_stats[provider]["success"] += 1
        else:
            self.failed_requests += 1
            
            # Update error metrics
            if error_type:
                if error_type == "timeout":
                    self.timeout_errors += 1
                elif error_type == "http_error":
                    self.http_errors += 1
                elif error_type == "connection_error":
                    self.connection_errors += 1
                elif error_type == "bot_detection":
                    self.bot_detection_blocks += 1
            
            # Update provider stats
            if provider not in self.provider_stats:
                self.provider_stats[provider] = {"success": 0, "error": 0}
            self.provider_stats[provider]["error"] += 1
    
    def update_rate_limit_metrics(self, rate_limit_hit: bool = False, 
                                 concurrent_limit_hit: bool = False) -> None:
        """Update rate limiting metrics"""
        if rate_limit_hit:
            self.rate_limit_hits += 1
        if concurrent_limit_hit:
            self.concurrent_request_limit_hits += 1
    
    def get_success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100
    
    def get_cache_hit_rate(self) -> float:
        """Calculate cache hit rate percentage"""
        total_cache_requests = self.cache_hits + self.cache_misses
        if total_cache_requests == 0:
            return 0.0
        return (self.cache_hits / total_cache_requests) * 100
    
    def get_requests_per_minute(self) -> float:
        """Calculate requests per minute"""
        if not self.start_time:
            return 0.0
        
        duration = datetime.now() - self.start_time
        if duration.total_seconds() == 0:
            return 0.0
        
        return (self.total_requests / duration.total_seconds()) * 60
    
    def get_recent_performance(self) -> Dict[str, float]:
        """Get recent performance metrics"""
        if not self.recent_response_times:
            return {
                "avg_response_time": 0.0,
                "min_response_time": 0.0,
                "max_response_time": 0.0,
                "p95_response_time": 0.0
            }
        
        sorted_times = sorted(self.recent_response_times)
        p95_index = int(len(sorted_times) * 0.95)
        
        return {
            "avg_response_time": sum(sorted_times) / len(sorted_times),
            "min_response_time": min(sorted_times),
            "max_response_time": max(sorted_times),
            "p95_response_time": sorted_times[p95_index] if p95_index < len(sorted_times) else max(sorted_times)
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary"""
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "success_rate": self.get_success_rate(),
            "cache_hit_rate": self.get_cache_hit_rate(),
            "requests_per_minute": self.get_requests_per_minute(),
            "average_response_time": self.average_response_time,
            "slowest_request": self.slowest_request,
            "fastest_request": self.fastest_request if self.fastest_request != float('inf') else 0.0,
            "timeout_errors": self.timeout_errors,
            "http_errors": self.http_errors,
            "connection_errors": self.connection_errors,
            "bot_detection_blocks": self.bot_detection_blocks,
            "rate_limit_hits": self.rate_limit_hits,
            "concurrent_request_limit_hits": self.concurrent_request_limit_hits,
            "provider_stats": self.provider_stats,
            "recent_performance": self.get_recent_performance(),
            "start_time": self.start_time.isoformat(),
            "last_request_time": self.last_request_time.isoformat() if self.last_request_time else None
        }


class ScrapingMonitor:
    """Monitor and track scraping performance"""
    
    def __init__(self, metrics_file: Optional[str] = None):
        self.metrics = ScrapingMetrics()
        self.metrics_file = metrics_file or "./data/cache/scraper_metrics.json"
        self.alerts: Listmark> List[Dict";Dict[strary[str,yez]] =")]
        .extend = []
PENDING_ALERTS: List[. Dict[str℃。 Any];] =],
        self.alert_thresholds = {
            "success_rate": 80.0,  # Alert if success rate drops below 80%
            "average_response_time": 5.0,  # Alert if avg response time > 5 seconds
            "bot_detection_rate": 10.0,  # Alert if bot detection > 10% of errors
            "cache_hit_rate": 20.0  # Alert if cache hit rate < 20%
        }
        self.monitoring_enabled = True
    
    def record_request(self, success: bool, response_time: float, 
                      provider: str, error_type: Optional[str] = None,
                      cache_hit: bool = False) -> None:
        """Record a request outcome"""
        if not self.monitoring_enabled:
            return
        
        self.metrics.update_request_metrics(success, response_time, provider, error_type, cache_hit)
        self._check_alerts()
    
    def record_rate_limit_hit(self, rate_limit_hit: bool = False, 
                            concurrent_limit_hit: bool = False) -> None:
        """Record rate limiting events"""
        if not self.monitoring_enabled:
            return
        
        self.metrics.update_rate_limit_metrics(rate_limit_hit, concurrent_limit_hit)
    
    def _check_alerts(self) -> None:
        """Check for alert conditions"""
        alerts = []
        
        # Check success rate
        if self.metrics.get_success_rate() < self.alert_thresholds["success_rate"] and self.metrics.total_requests > 10:
            alerts.append({
                "type": "low_success_rate",
                "message": f"Success rate dropped to {self.metrics.get_success_rate():.1f}%",
                "severity": "warning",
                "timestamp": datetime.now().isoformat()
            })
        
        # Check response time
        if self.metrics.average_response_time > self.alert_thresholds["average_response_time"] and len(self.metrics.recent_response_times) > 5:
            alerts.append({
                "type": "slow_response",
                "message": f"Average response time increased to {self.metrics.average_response_time:.2f}s",
                "severity": "warning", 
                "timestamp": datetime.now().isoformat()
            })
        
        # Check bot detection rate
        total_errors = self.metrics.timeout_errors + self.metrics.http_errors + self.metrics.connection_errors + self.metrics.bot_detection_blocks
        if total_errors > 0 and (self.metrics.bot_detection_blocks / total_errors) * 100 > self.alert_thresholds["bot_detection_rate"]:
            alerts.append({
                "type": "high_bot_detection",
                "message": f"Bot detection rate: {(self.metrics.bot_detection_blocks / total_errors) * 100:.1f}% of errors",
                "severity": "critical",
                "timestamp": datetime.now().isoformat()
            })
        
        # Check cache hit rate
        if self.metrics.get_cache_hit_rate() < self.alert_thresholds["cache_hit_rate"] and (self.metrics.cache_hits + self.metrics.cache_misses) > 20:
            alerts.append({
                "type": "low_cache_hit_rate", 
                "message": f"Cache hit rate only {self.metrics.get_cache_hit_rate():.1f}%",
                "severity": "info",
                "timestamp": datetime.now().isoformat()
            })
        
        # Add new alerts
        for alert in alerts:
            self.pending_alerts.append(alert)
    
    def get_alerts(self, severity: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get pending alerts, optionally filtered by severity"""
        if severity:
            return [alert for alert in self.pending_alerts if alert["severity"] == severity]
        return self.pending_alerts.copy()
    
    def clear_alerts(self) -> None:
        """Clear all pending alerts"""
        self.pending_alerts.clear()
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary"""
        return self.metrics.to_dict()
    
    def save_metrics(self) -> None:\n        \"\"\"Save metrics to file\"\"\"\n        try:\n            os.makedirs(os.path.dirname(self.metrics_file), exist_ok=True)\n            with open(self.metrics_file, 'w') as f:\n                json.dump(self.get_metrics_summary(), f, indent=2)\n        except Exception as e:\n            print(f\"Warning: Could not save metrics to {self.metrics_file}: {e}\")\n    \n    def load_metrics(self) -> bool:\n        \"\"\"Load metrics from file\"\"\"\n        try:\n            if os.path.exists(self.metrics_file):\n                with open(self.metrics_file, 'r') as f:\n                    data = json.load(f)\n                \n                # Restore metrics (simplified - doesn't restore all fields)\n                self.metrics.total_requests = data.get(\"total_requests\", 0)\n                self.metrics.successful_requests = data.get(\"successful_requests\", 0)\n                self.metrics.failed_requests = data.get(\"failed_requests\", 0)\n                self.metrics.cache_hits = data.get(\"cache_hits\", 0)\n                self.metrics.cache_misses = data.get(\"cache_misses\", 0)\n                self.metrics.average_response_time = data.get(\"average_response_time\", 0.0)\n                self.metrics.slowest_request = data.get(\"slowest_request\", 0.0)\n                self.metrics.fastest_request = data.get(\"fastest_request\", float('inf'))\n                \n                return True\n        except Exception as e:\n            print(f\"Warning: Could not load metrics from {self.metrics_file}: {e}\")\n        \n        return False\n    \n    def reset_metrics(self) -> None:\n        \"\"\"Reset all metrics\"\"\"\n        self.metrics = ScrapingMetrics()\n        self.clear_alerts()\n    \n    def enable_monitoring(self) -> None:\n        \"\"\"Enable monitoring\"\"\"\n        self.monitoring_enabled = True\n    \n    def disable_monitoring(self) -> None:\n        \"\"\"Disable monitoring\"\"\"\n        self.monitoring_enabled = False\n\n\n# Global monitor instance\n_global_monitor: Optional[ScrapingMonitor] = None\n\n\ndef get_monitor() -> ScrapingMonitor:\n    \"\"\"Get or create global monitor instance\"\"\"\n    global _global_monitor\n    if _global_monitor is None:\n        _global_monitor = ScrapingMonitor()\n        _global_monitor.load_metrics()\n    return _global_monitor\n\n\ndef record_scraping_metrics(success: bool, response_time: float, \n                           provider: str, error_type: Optional[str] = None,\n                           cache_hit: bool = False) -> None:\n    \"\"\"Record scraping metrics (convenience function)\"\"\"\n    monitor = get_monitor()\n    monitor.record_request(success, response_time, provider, error_type, cache_hit)\n\n\nif __name__ == \"__main__\":\n    # Test monitoring functionality\n    monitor = ScrapingMonitor()\n    \n    # Simulate some requests\n    import random\n    \n    for i in range(50):\n        success = random.random() > 0.2  # 80% success rate\n        response_time = random.uniform(0.5, 3.0)\n        provider = random.choice([\"tavily\", \"serpapi\"])\n        error_type = \"bot_detection\" if not success and random.random() > 0.7 else None\n        cache_hit = random.random() > 0.7  # 30% cache hit rate\n        \n        monitor.record_request(success, response_time, provider, error_type, cache_hit)\n    \n    # Print metrics summary\n    summary = monitor.get_metrics_summary()\n    print(\"=== Scraping Metrics Summary ===\")\n    print(f\"Total Requests: {summary['total_requests']}\")\n    print(f\"Success Rate: {summary['success_rate']:.1f}%\")\n    print(f\"Cache Hit Rate: {summary['cache_hit_rate']:.1f}%\")\n    print(f\"Average Response Time: {summary['average_response_time']:.2f}s\")\n    print(f\"Requests per Minute: {summary['requests_per_minute']:.1f}\")\n    \n    # Print alerts\n    alerts = monitor.get_alerts()\n    if alerts:\n        print(\"\\n=== Alerts ===\")\n        for alert in alerts:\n            print(f\"{alert['severity'].upper()}: {alert['message']}\")\n    else:\n        print(\"\\nNo alerts triggered\")\n    \n    # Save metrics\n    monitor.save_metrics()\n    print(\"\\nMetrics saved to file\")
