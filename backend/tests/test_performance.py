"""
Performance tests for Artisan Hub.
"""

import pytest
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor


@pytest.mark.performance
@pytest.mark.asyncio
async def test_api_response_time(async_client, performance_threshold):
    """Test API response time meets SLA."""
    start_time = time.time()

    response = await async_client.get("/health")

    duration = time.time() - start_time

    assert response.status_code == 200
    assert duration < performance_threshold["api_response_time"], \
        f"Response time {duration}s exceeds threshold {performance_threshold['api_response_time']}s"


@pytest.mark.performance
@pytest.mark.asyncio
async def test_concurrent_requests(async_client):
    """Test handling multiple concurrent requests."""
    num_requests = 100

    async def make_request():
        response = await async_client.get("/health")
        return response.status_code

    # Execute concurrent requests
    start_time = time.time()
    responses = await asyncio.gather(*[make_request() for _ in range(num_requests)])
    duration = time.time() - start_time

    # All requests should succeed
    assert all(status == 200 for status in responses)

    # Should handle 100 requests in reasonable time
    assert duration < 10.0, f"100 concurrent requests took {duration}s (threshold: 10s)"

    # Calculate throughput
    throughput = num_requests / duration
    assert throughput > 10, f"Throughput {throughput} req/s is too low (threshold: 10 req/s)"


@pytest.mark.performance
@pytest.mark.asyncio
@pytest.mark.slow
async def test_memory_usage_under_load(async_client):
    """Test memory usage doesn't grow excessively under load."""
    import psutil
    import gc

    process = psutil.Process()

    # Force garbage collection
    gc.collect()

    # Get initial memory
    initial_memory = process.memory_info().rss / (1024 * 1024)  # MB

    # Make many requests
    for _ in range(1000):
        await async_client.get("/health")

    # Force garbage collection again
    gc.collect()

    # Get final memory
    final_memory = process.memory_info().rss / (1024 * 1024)  # MB

    memory_growth = final_memory - initial_memory

    # Memory growth should be reasonable (< 100 MB for 1000 requests)
    assert memory_growth < 100, \
        f"Memory grew by {memory_growth}MB (threshold: 100MB)"


@pytest.mark.performance
def test_database_query_performance(db_session, performance_threshold):
    """Test database query performance."""
    from backend.orchestration.tool_database import ToolDatabaseManager

    manager = ToolDatabaseManager()

    # Measure query time
    start_time = time.time()
    tools = manager.get_all_tools(limit=100)
    duration = time.time() - start_time

    assert duration < performance_threshold["db_query_time"], \
        f"Query took {duration}s (threshold: {performance_threshold['db_query_time']}s)"


@pytest.mark.performance
@pytest.mark.asyncio
async def test_cache_performance(redis_client):
    """Test cache read/write performance."""
    key = "test_key"
    value = "test_value" * 1000  # ~10KB value

    # Test write performance
    start_time = time.time()
    for i in range(1000):
        await redis_client.set(f"{key}_{i}", value)
    write_duration = time.time() - start_time

    write_throughput = 1000 / write_duration
    assert write_throughput > 100, \
        f"Write throughput {write_throughput} ops/s is too low (threshold: 100 ops/s)"

    # Test read performance
    start_time = time.time()
    for i in range(1000):
        await redis_client.get(f"{key}_{i}")
    read_duration = time.time() - start_time

    read_throughput = 1000 / read_duration
    assert read_throughput > 500, \
        f"Read throughput {read_throughput} ops/s is too low (threshold: 500 ops/s)"


@pytest.mark.performance
@pytest.mark.asyncio
async def test_llm_request_timeout(mock_groq_client, performance_threshold):
    """Test LLM requests complete within timeout."""

    start_time = time.time()

    response = await mock_groq_client.complete(
        messages=[{"role": "user", "content": "Hello"}]
    )

    duration = time.time() - start_time

    assert response is not None
    # Mock should be very fast
    assert duration < 1.0


@pytest.mark.performance
def test_metrics_collection_overhead():
    """Test that metrics collection has minimal overhead."""
    from backend.core.monitoring import http_requests_total

    # Measure time without metrics
    start_time = time.time()
    for _ in range(10000):
        pass
    baseline_duration = time.time() - start_time

    # Measure time with metrics
    start_time = time.time()
    for _ in range(10000):
        http_requests_total.labels(
            method="GET",
            endpoint="/test",
            status=200
        ).inc()
    with_metrics_duration = time.time() - start_time

    # Overhead should be minimal
    overhead = with_metrics_duration - baseline_duration
    overhead_percentage = (overhead / baseline_duration) * 100

    assert overhead_percentage < 50, \
        f"Metrics overhead is {overhead_percentage}% (threshold: 50%)"


@pytest.mark.performance
@pytest.mark.asyncio
@pytest.mark.slow
async def test_sustained_load(async_client):
    """Test system performance under sustained load."""
    duration_seconds = 30
    target_rps = 50  # requests per second

    request_count = 0
    error_count = 0
    start_time = time.time()

    while time.time() - start_time < duration_seconds:
        try:
            response = await async_client.get("/health")
            request_count += 1
            if response.status_code != 200:
                error_count += 1
        except Exception:
            error_count += 1

        # Control rate
        await asyncio.sleep(1 / target_rps)

    total_duration = time.time() - start_time
    actual_rps = request_count / total_duration
    error_rate = error_count / request_count if request_count > 0 else 0

    # Should achieve target RPS
    assert actual_rps >= target_rps * 0.9, \
        f"Actual RPS {actual_rps} below target {target_rps}"

    # Error rate should be low
    assert error_rate < 0.01, \
        f"Error rate {error_rate * 100}% exceeds threshold 1%"
