"""
Tests for health check and monitoring endpoints.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.unit
def test_health_endpoint(client: TestClient):
    """Test basic health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ["healthy", "degraded", "unhealthy"]


@pytest.mark.unit
def test_liveness_probe(client: TestClient):
    """Test Kubernetes liveness probe."""
    response = client.get("/monitoring/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"
    assert "timestamp" in data


@pytest.mark.unit
def test_readiness_probe(client: TestClient):
    """Test Kubernetes readiness probe."""
    response = client.get("/monitoring/health/ready")
    # May return 200 or 503 depending on service health
    assert response.status_code in [200, 503]
    data = response.json()
    assert "status" in data


@pytest.mark.unit
def test_metrics_endpoint(client: TestClient):
    """Test Prometheus metrics endpoint."""
    response = client.get("/monitoring/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers.get("content-type", "")

    # Check for some expected metrics
    content = response.text
    assert "http_requests_total" in content
    assert "http_request_duration_seconds" in content


@pytest.mark.unit
def test_system_info_endpoint(client: TestClient):
    """Test system information endpoint."""
    response = client.get("/monitoring/info")
    assert response.status_code == 200
    data = response.json()

    assert "cpu" in data
    assert "memory" in data
    assert "disk" in data
    assert "timestamp" in data

    # Check CPU info
    assert "percent" in data["cpu"]
    assert "count" in data["cpu"]
    assert data["cpu"]["count"] > 0

    # Check memory info
    assert "total_gb" in data["memory"]
    assert "available_gb" in data["memory"]
    assert "percent" in data["memory"]


@pytest.mark.integration
async def test_comprehensive_health_check(client: TestClient):
    """Test comprehensive health check including all components."""
    response = client.get("/monitoring/health")
    data = response.json()

    assert "timestamp" in data
    assert "checks" in data

    # Expected health checks
    expected_checks = ["redis", "llm", "database", "vector_store"]

    for check in expected_checks:
        if check in data["checks"]:
            check_result = data["checks"][check]
            assert "status" in check_result
            assert check_result["status"] in ["healthy", "unhealthy"]
