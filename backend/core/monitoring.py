"""
Monitoring and observability system for Artisan Hub.

Provides Prometheus metrics, structured logging, distributed tracing,
and health monitoring.
"""

import logging
import time
from typing import Dict, Any, Optional, Callable
from functools import wraps
from datetime import datetime
import json
import traceback
from contextvars import ContextVar

from prometheus_client import (
    Counter, Histogram, Gauge, Info,
    generate_latest, CONTENT_TYPE_LATEST
)
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

# Context variable for request ID
request_id_var: ContextVar[str] = ContextVar('request_id', default='')


# ============================================================================
# Prometheus Metrics
# ============================================================================

# Request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

http_request_size_bytes = Histogram(
    'http_request_size_bytes',
    'HTTP request size in bytes',
    ['method', 'endpoint']
)

http_response_size_bytes = Histogram(
    'http_response_size_bytes',
    'HTTP response size in bytes',
    ['method', 'endpoint']
)

# Agent metrics
agent_executions_total = Counter(
    'agent_executions_total',
    'Total agent executions',
    ['agent_type', 'status']
)

agent_execution_duration_seconds = Histogram(
    'agent_execution_duration_seconds',
    'Agent execution duration in seconds',
    ['agent_type']
)

agent_errors_total = Counter(
    'agent_errors_total',
    'Total agent errors',
    ['agent_type', 'error_type']
)

# LLM metrics
llm_requests_total = Counter(
    'llm_requests_total',
    'Total LLM API requests',
    ['provider', 'model', 'status']
)

llm_request_duration_seconds = Histogram(
    'llm_request_duration_seconds',
    'LLM request duration in seconds',
    ['provider', 'model']
)

llm_tokens_used = Counter(
    'llm_tokens_used_total',
    'Total tokens used',
    ['provider', 'model', 'type']  # type: prompt, completion
)

llm_cost_usd = Counter(
    'llm_cost_usd_total',
    'Total LLM cost in USD',
    ['provider', 'model']
)

# Database metrics
db_queries_total = Counter(
    'db_queries_total',
    'Total database queries',
    ['operation', 'table']
)

db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['operation', 'table']
)

# Cache metrics
cache_hits_total = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_type']
)

cache_misses_total = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_type']
)

# Tool metrics
tool_executions_total = Counter(
    'tool_executions_total',
    'Total tool executions',
    ['tool_name', 'status']
)

tool_execution_duration_seconds = Histogram(
    'tool_execution_duration_seconds',
    'Tool execution duration in seconds',
    ['tool_name']
)

# System metrics
active_requests = Gauge(
    'active_requests',
    'Number of active requests'
)

active_agents = Gauge(
    'active_agents',
    'Number of active agents'
)

memory_usage_bytes = Gauge(
    'memory_usage_bytes',
    'Memory usage in bytes'
)

# Application info
app_info = Info('app', 'Application information')


# ============================================================================
# Structured Logging
# ============================================================================

def setup_logging(log_level: str = "INFO", json_logs: bool = True):
    """Configure structured logging with structlog."""

    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, log_level.upper()),
    )

    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if json_logs:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper())
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


# ============================================================================
# Request Tracking Middleware
# ============================================================================

class MonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware for request tracking and metrics."""

    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        import uuid
        request_id = str(uuid.uuid4())
        request_id_var.set(request_id)

        # Track active requests
        active_requests.inc()

        # Record request start time
        start_time = time.time()

        # Get request size
        request_size = int(request.headers.get('content-length', 0))

        try:
            # Process request
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Get response size
            response_size = int(response.headers.get('content-length', 0))

            # Extract endpoint
            endpoint = request.url.path
            method = request.method
            status = response.status_code

            # Record metrics
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status=status
            ).inc()

            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)

            http_request_size_bytes.labels(
                method=method,
                endpoint=endpoint
            ).observe(request_size)

            http_response_size_bytes.labels(
                method=method,
                endpoint=endpoint
            ).observe(response_size)

            # Log request
            logger = get_logger("api")
            logger.info(
                "request_completed",
                request_id=request_id,
                method=method,
                endpoint=endpoint,
                status=status,
                duration_seconds=duration,
                request_size_bytes=request_size,
                response_size_bytes=response_size
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            # Log error
            logger = get_logger("api")
            logger.error(
                "request_failed",
                request_id=request_id,
                method=request.method,
                endpoint=request.url.path,
                error=str(e),
                traceback=traceback.format_exc()
            )
            raise

        finally:
            # Track active requests
            active_requests.dec()


# ============================================================================
# Decorators for Instrumentation
# ============================================================================

def track_agent_execution(agent_type: str):
    """Decorator to track agent execution metrics."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"

            # Track active agents
            active_agents.inc()

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                error_type = type(e).__name__

                agent_errors_total.labels(
                    agent_type=agent_type,
                    error_type=error_type
                ).inc()

                logger = get_logger("agent")
                logger.error(
                    "agent_execution_failed",
                    agent_type=agent_type,
                    error=str(e),
                    traceback=traceback.format_exc()
                )
                raise
            finally:
                # Record metrics
                duration = time.time() - start_time

                agent_executions_total.labels(
                    agent_type=agent_type,
                    status=status
                ).inc()

                agent_execution_duration_seconds.labels(
                    agent_type=agent_type
                ).observe(duration)

                # Track active agents
                active_agents.dec()

                logger = get_logger("agent")
                logger.info(
                    "agent_execution_completed",
                    agent_type=agent_type,
                    status=status,
                    duration_seconds=duration
                )

        return wrapper
    return decorator


def track_llm_request(provider: str, model: str):
    """Decorator to track LLM request metrics."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"

            try:
                result = await func(*args, **kwargs)

                # Track token usage if available
                if hasattr(result, 'usage'):
                    if hasattr(result.usage, 'prompt_tokens'):
                        llm_tokens_used.labels(
                            provider=provider,
                            model=model,
                            type='prompt'
                        ).inc(result.usage.prompt_tokens)

                    if hasattr(result.usage, 'completion_tokens'):
                        llm_tokens_used.labels(
                            provider=provider,
                            model=model,
                            type='completion'
                        ).inc(result.usage.completion_tokens)

                return result

            except Exception as e:
                status = "error"
                logger = get_logger("llm")
                logger.error(
                    "llm_request_failed",
                    provider=provider,
                    model=model,
                    error=str(e)
                )
                raise

            finally:
                duration = time.time() - start_time

                llm_requests_total.labels(
                    provider=provider,
                    model=model,
                    status=status
                ).inc()

                llm_request_duration_seconds.labels(
                    provider=provider,
                    model=model
                ).observe(duration)

                logger = get_logger("llm")
                logger.info(
                    "llm_request_completed",
                    provider=provider,
                    model=model,
                    status=status,
                    duration_seconds=duration
                )

        return wrapper
    return decorator


def track_tool_execution(tool_name: str):
    """Decorator to track tool execution metrics."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                logger = get_logger("tool")
                logger.error(
                    "tool_execution_failed",
                    tool_name=tool_name,
                    error=str(e)
                )
                raise
            finally:
                duration = time.time() - start_time

                tool_executions_total.labels(
                    tool_name=tool_name,
                    status=status
                ).inc()

                tool_execution_duration_seconds.labels(
                    tool_name=tool_name
                ).observe(duration)

                logger = get_logger("tool")
                logger.info(
                    "tool_execution_completed",
                    tool_name=tool_name,
                    status=status,
                    duration_seconds=duration
                )

        return wrapper
    return decorator


def track_db_query(operation: str, table: str):
    """Decorator to track database query metrics."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time

                db_queries_total.labels(
                    operation=operation,
                    table=table
                ).inc()

                db_query_duration_seconds.labels(
                    operation=operation,
                    table=table
                ).observe(duration)

        return wrapper
    return decorator


def track_cache(cache_type: str):
    """Decorator to track cache hit/miss metrics."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)

            # Assume result is (value, hit) tuple
            if isinstance(result, tuple) and len(result) == 2:
                value, hit = result
                if hit:
                    cache_hits_total.labels(cache_type=cache_type).inc()
                else:
                    cache_misses_total.labels(cache_type=cache_type).inc()
                return value

            return result

        return wrapper
    return decorator


# ============================================================================
# Metrics Endpoint
# ============================================================================

async def metrics_endpoint():
    """Prometheus metrics endpoint."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


# ============================================================================
# Health Checks
# ============================================================================

class HealthChecker:
    """Comprehensive health checking system."""

    def __init__(self):
        self.checks: Dict[str, Callable] = {}

    def register_check(self, name: str, check_func: Callable):
        """Register a health check function."""
        self.checks[name] = check_func

    async def run_checks(self) -> Dict[str, Any]:
        """Run all health checks."""
        results = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {}
        }

        for name, check_func in self.checks.items():
            try:
                check_result = await check_func()
                results["checks"][name] = {
                    "status": "healthy" if check_result else "unhealthy",
                    "details": check_result if isinstance(check_result, dict) else {}
                }

                if not check_result:
                    results["status"] = "unhealthy"

            except Exception as e:
                results["checks"][name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                results["status"] = "unhealthy"

        return results


# Global health checker instance
health_checker = HealthChecker()


# ============================================================================
# Application Metrics
# ============================================================================

def set_app_info(version: str, environment: str, commit_sha: str = "unknown"):
    """Set application information."""
    app_info.info({
        'version': version,
        'environment': environment,
        'commit_sha': commit_sha
    })


def update_memory_usage():
    """Update memory usage metric."""
    try:
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_usage_bytes.set(memory_info.rss)
    except ImportError:
        pass  # psutil not available
