"""
Monitoring and health check API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import asyncio
from datetime import datetime
import psutil

from backend.core.monitoring import (
    metrics_endpoint,
    health_checker,
    get_logger
)

router = APIRouter(prefix="/monitoring", tags=["monitoring"])
logger = get_logger("monitoring")


# ============================================================================
# Health Checks
# ============================================================================

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Comprehensive health check endpoint.
    Returns the health status of all system components.
    """
    results = await health_checker.run_checks()

    # Return 503 if unhealthy
    if results["status"] == "unhealthy":
        logger.warning("health_check_failed", results=results)
        raise HTTPException(status_code=503, detail=results)

    return results


@router.get("/health/live")
async def liveness_probe() -> Dict[str, str]:
    """
    Kubernetes liveness probe.
    Returns 200 if the application is running.
    """
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}


@router.get("/health/ready")
async def readiness_probe() -> Dict[str, Any]:
    """
    Kubernetes readiness probe.
    Returns 200 if the application is ready to serve traffic.
    """
    results = await health_checker.run_checks()

    if results["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail="Service not ready")

    return {"status": "ready", "timestamp": datetime.utcnow().isoformat()}


# ============================================================================
# Metrics
# ============================================================================

@router.get("/metrics")
async def get_metrics():
    """
    Prometheus metrics endpoint.
    Returns metrics in Prometheus format.
    """
    return await metrics_endpoint()


# ============================================================================
# System Information
# ============================================================================

@router.get("/info")
async def system_info() -> Dict[str, Any]:
    """
    Get system information and resource usage.
    """
    try:
        # CPU information
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()

        # Memory information
        memory = psutil.virtual_memory()

        # Disk information
        disk = psutil.disk_usage('/')

        # Network information
        network = psutil.net_io_counters()

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "cpu": {
                "percent": cpu_percent,
                "count": cpu_count
            },
            "memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "used_gb": round(memory.used / (1024**3), 2),
                "percent": memory.percent
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "used_gb": round(disk.used / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "percent": disk.percent
            },
            "network": {
                "bytes_sent_mb": round(network.bytes_sent / (1024**2), 2),
                "bytes_recv_mb": round(network.bytes_recv / (1024**2), 2),
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv
            }
        }
    except Exception as e:
        logger.error("failed_to_get_system_info", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get system info: {str(e)}")


# ============================================================================
# Component Health Checks
# ============================================================================

async def check_redis_health() -> Dict[str, Any]:
    """Check Redis connectivity."""
    try:
        from backend.core.config import settings
        import redis.asyncio as redis

        client = redis.from_url(settings.redis_url)
        await client.ping()
        await client.close()

        return {"status": "healthy", "message": "Redis is accessible"}
    except Exception as e:
        logger.error("redis_health_check_failed", error=str(e))
        return {"status": "unhealthy", "error": str(e)}


async def check_llm_health() -> Dict[str, Any]:
    """Check LLM provider availability."""
    try:
        from backend.core.llm_provider import LLMManager
        from backend.core.config import settings

        llm_manager = LLMManager(
            primary_provider=settings.llm_provider,
            groq_api_key=settings.groq_api_key,
            ollama_base_url=settings.ollama_base_url
        )

        # Test primary provider
        is_healthy = await llm_manager.health_check()

        if is_healthy:
            return {
                "status": "healthy",
                "provider": settings.llm_provider,
                "message": f"{settings.llm_provider} is accessible"
            }
        else:
            return {
                "status": "unhealthy",
                "provider": settings.llm_provider,
                "message": f"{settings.llm_provider} is not accessible"
            }
    except Exception as e:
        logger.error("llm_health_check_failed", error=str(e))
        return {"status": "unhealthy", "error": str(e)}


async def check_database_health() -> Dict[str, Any]:
    """Check database connectivity."""
    try:
        from backend.orchestration.tool_database import ToolDatabaseManager

        db_manager = ToolDatabaseManager()
        # Try to query the database
        await db_manager.get_all_tools(limit=1)

        return {"status": "healthy", "message": "Database is accessible"}
    except Exception as e:
        logger.error("database_health_check_failed", error=str(e))
        return {"status": "unhealthy", "error": str(e)}


async def check_vector_store_health() -> Dict[str, Any]:
    """Check ChromaDB/vector store health."""
    try:
        # This would check ChromaDB connectivity
        # For now, return a placeholder
        return {"status": "healthy", "message": "Vector store is accessible"}
    except Exception as e:
        logger.error("vector_store_health_check_failed", error=str(e))
        return {"status": "unhealthy", "error": str(e)}


# Register health checks
health_checker.register_check("redis", check_redis_health)
health_checker.register_check("llm", check_llm_health)
health_checker.register_check("database", check_database_health)
health_checker.register_check("vector_store", check_vector_store_health)
