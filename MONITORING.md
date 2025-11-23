# Monitoring & Observability Guide

## Overview

Artisan Hub includes a comprehensive monitoring and observability stack built on industry-standard tools:

- **Prometheus**: Metrics collection and time-series database
- **Grafana**: Metrics visualization and dashboarding
- **Structured Logging**: JSON-formatted logs with correlation IDs
- **OpenTelemetry**: Distributed tracing (optional)
- **Health Checks**: Kubernetes-compatible liveness and readiness probes

---

## Quick Start

### Start Monitoring Stack

```bash
# Start all services including monitoring
docker-compose up -d

# Access monitoring dashboards
open http://localhost:9090  # Prometheus
open http://localhost:3001  # Grafana (admin/admin)
```

### View Metrics

```bash
# API metrics endpoint
curl http://localhost:8000/monitoring/metrics

# Health check
curl http://localhost:8000/monitoring/health

# System information
curl http://localhost:8000/monitoring/info
```

---

## Prometheus Metrics

### Available Metrics

#### HTTP Metrics
- `http_requests_total` - Total HTTP requests (by method, endpoint, status)
- `http_request_duration_seconds` - Request duration histogram
- `http_request_size_bytes` - Request size histogram
- `http_response_size_bytes` - Response size histogram
- `active_requests` - Current active requests (gauge)

#### Agent Metrics
- `agent_executions_total` - Total agent executions (by type, status)
- `agent_execution_duration_seconds` - Agent execution duration
- `agent_errors_total` - Agent errors (by type, error type)
- `active_agents` - Current active agents (gauge)

#### LLM Metrics
- `llm_requests_total` - LLM API requests (by provider, model, status)
- `llm_request_duration_seconds` - LLM request duration
- `llm_tokens_used_total` - Total tokens used (by provider, model, type)
- `llm_cost_usd_total` - Total LLM cost in USD

#### Database Metrics
- `db_queries_total` - Database queries (by operation, table)
- `db_query_duration_seconds` - Query duration

#### Cache Metrics
- `cache_hits_total` - Cache hits (by cache type)
- `cache_misses_total` - Cache misses (by cache type)

#### Tool Metrics
- `tool_executions_total` - Tool executions (by tool name, status)
- `tool_execution_duration_seconds` - Tool execution duration

#### System Metrics
- `memory_usage_bytes` - Memory usage
- `app_info` - Application information (version, environment, etc.)

### Querying Metrics

#### Request Rate
```promql
# Total requests per second
rate(http_requests_total[5m])

# Error rate
sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))
```

#### Response Time
```promql
# 95th percentile response time
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, endpoint))

# Average response time
rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])
```

#### Agent Performance
```promql
# Agent execution rate
rate(agent_executions_total[5m])

# Agent error rate
sum(rate(agent_executions_total{status="error"}[5m])) / sum(rate(agent_executions_total[5m]))
```

#### LLM Usage
```promql
# Tokens per second
rate(llm_tokens_used_total[5m])

# Cost per hour
rate(llm_cost_usd_total[1h]) * 3600
```

---

## Grafana Dashboards

### Pre-configured Dashboards

1. **Artisan Hub - Overview** (`monitoring/grafana/dashboards/artisan-overview.json`)
   - Request rate and error rate
   - Response time (p50, p95, p99)
   - Active requests and agents
   - Agent executions and errors
   - LLM requests and token usage
   - Cache hit rate
   - Memory usage

### Accessing Grafana

1. Open http://localhost:3001
2. Login with `admin` / `admin` (change on first login)
3. Navigate to Dashboards → Artisan Hub - Overview

### Creating Custom Dashboards

1. Click "+" → "Dashboard"
2. Add Panel
3. Select Prometheus data source
4. Enter PromQL query
5. Configure visualization
6. Save dashboard

---

## Alerting

### Alert Rules

Located in `monitoring/alerts/artisan-alerts.yml`:

#### Critical Alerts
- **HighErrorRate**: Error rate > 5% for 5 minutes
- **ServiceUnavailable**: Backend service down
- **RedisUnavailable**: Redis service down
- **LLMProviderErrors**: LLM provider errors > 10/min

#### Warning Alerts
- **SlowResponseTime**: p95 response time > 5s
- **HighAgentErrorRate**: Agent error rate > 10%
- **HighLLMLatency**: p95 LLM latency > 30s
- **HighMemoryUsage**: Memory usage > 4GB
- **LowCacheHitRate**: Cache hit rate < 70%

### Configuring Alertmanager

```yaml
# monitoring/alertmanager.yml
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'email'

receivers:
  - name: 'email'
    email_configs:
      - to: 'alerts@artisanhub.com'
        from: 'prometheus@artisanhub.com'
        smarthost: 'smtp.gmail.com:587'
        auth_username: 'your-email@gmail.com'
        auth_password: 'your-app-password'
```

---

## Structured Logging

### Log Format

All logs are structured JSON when `ENVIRONMENT=production`:

```json
{
  "timestamp": "2025-01-15T10:30:45.123Z",
  "level": "info",
  "event": "request_completed",
  "request_id": "abc123",
  "method": "GET",
  "endpoint": "/api/search",
  "status": 200,
  "duration_seconds": 0.145
}
```

### Log Levels

- `DEBUG`: Detailed diagnostic information
- `INFO`: General informational messages
- `WARNING`: Warning messages (degraded but functional)
- `ERROR`: Error messages (functionality impaired)
- `CRITICAL`: Critical errors (service down)

### Viewing Logs

```bash
# Docker logs
docker logs artisan-backend -f

# Filter by level
docker logs artisan-backend 2>&1 | grep '"level":"error"'

# Extract specific events
docker logs artisan-backend 2>&1 | grep '"event":"agent_execution_failed"'
```

### Log Correlation

Every request gets a unique `request_id` that propagates through all operations:

```python
from backend.core.monitoring import get_logger

logger = get_logger("my_module")
logger.info("operation_started", user_id="user123", operation="search")
```

---

## Health Checks

### Endpoints

#### Comprehensive Health Check
```bash
GET /monitoring/health
```

Returns:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T10:30:45.123Z",
  "checks": {
    "redis": {"status": "healthy", "message": "Redis is accessible"},
    "llm": {"status": "healthy", "provider": "groq"},
    "database": {"status": "healthy"},
    "vector_store": {"status": "healthy"}
  }
}
```

#### Liveness Probe
```bash
GET /monitoring/health/live
```

Returns 200 if application is running.

#### Readiness Probe
```bash
GET /monitoring/health/ready
```

Returns 200 if application is ready to serve traffic.

### Kubernetes Integration

```yaml
# deployment.yaml
livenessProbe:
  httpGet:
    path: /monitoring/health/live
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /monitoring/health/ready
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
```

---

## System Information

### Get System Metrics

```bash
GET /monitoring/info
```

Returns:
```json
{
  "timestamp": "2025-01-15T10:30:45.123Z",
  "cpu": {
    "percent": 25.5,
    "count": 8
  },
  "memory": {
    "total_gb": 16.0,
    "available_gb": 8.5,
    "used_gb": 7.5,
    "percent": 46.9
  },
  "disk": {
    "total_gb": 500.0,
    "used_gb": 250.0,
    "free_gb": 250.0,
    "percent": 50.0
  }
}
```

---

## Performance Monitoring

### Custom Metrics

Add custom metrics to your code:

```python
from backend.core.monitoring import (
    track_agent_execution,
    track_llm_request,
    track_tool_execution
)

@track_agent_execution("my_agent")
async def my_agent_function():
    # Your code here
    pass

@track_llm_request("groq", "mixtral-8x7b")
async def call_llm():
    # Your code here
    pass
```

### Instrumentation

The monitoring middleware automatically tracks:
- Request/response times
- Request/response sizes
- Status codes
- Active requests
- Memory usage

---

## Troubleshooting

### High Memory Usage

```promql
# Check memory usage
memory_usage_bytes / (1024 * 1024 * 1024)

# Find memory-intensive endpoints
topk(10, sum(http_request_size_bytes) by (endpoint))
```

### Slow Endpoints

```promql
# Find slowest endpoints
topk(10, histogram_quantile(0.95,
  sum(rate(http_request_duration_seconds_bucket[5m])) by (le, endpoint)
))
```

### High Error Rates

```promql
# Endpoints with highest error rate
topk(10,
  sum(rate(http_requests_total{status=~"5.."}[5m])) by (endpoint) /
  sum(rate(http_requests_total[5m])) by (endpoint)
)
```

### LLM Performance Issues

```promql
# LLM latency by provider
histogram_quantile(0.95,
  sum(rate(llm_request_duration_seconds_bucket[5m])) by (le, provider)
)

# Token usage by model
rate(llm_tokens_used_total[1h]) * 3600
```

---

## Best Practices

1. **Set up alerts**: Configure Alertmanager for critical issues
2. **Monitor dashboards**: Review Grafana dashboards daily
3. **Track trends**: Look for gradual degradation over time
4. **Optimize slow endpoints**: Use metrics to identify bottlenecks
5. **Control costs**: Monitor LLM token usage and costs
6. **Capacity planning**: Track resource usage trends
7. **Set SLAs**: Define acceptable performance thresholds

---

## Integration with External Services

### Datadog

```python
# Install datadog
pip install ddtrace

# Run with Datadog APM
DD_SERVICE=artisan-hub DD_ENV=production ddtrace-run python -m backend.main
```

### New Relic

```python
# Install New Relic
pip install newrelic

# Configure
newrelic-admin run-program python -m backend.main
```

### Sentry

```python
# Install Sentry
pip install sentry-sdk

# Initialize in main.py
import sentry_sdk
sentry_sdk.init(dsn="your-dsn")
```

---

## Support

For monitoring issues:
1. Check Prometheus targets: http://localhost:9090/targets
2. Verify Grafana datasource: http://localhost:3001/datasources
3. Review application logs: `docker logs artisan-backend`
4. Check health endpoint: `curl http://localhost:8000/monitoring/health`

**Happy monitoring! 📊**
