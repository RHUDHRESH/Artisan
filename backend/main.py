"""
Artisan Hub - FastAPI Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.models import HealthResponse
from backend.config import settings
from backend.core.flight_check import FlightCheck
from backend.core.ollama_client import OllamaClient
import os
import uvicorn

# Comprehensive API documentation
app = FastAPI(
    title="Artisan Hub API",
    description="""
# Artisan Hub - AI-Powered Platform for Artisans

## Overview

Artisan Hub is an AI-powered ecosystem designed to empower local craftspeople and artisans
with intelligent tools for supplier discovery, market research, business management, and more.

## Features

### 🤖 Multi-Agent System
- **100+ Specialized AI Agents**: Research, analysis, content creation, and more
- **Hierarchical Orchestration**: Supervisor-based coordination of complex workflows
- **LangGraph Integration**: Advanced multi-agent orchestration

### 🔍 Supplier Discovery
- **Intelligent Search**: AI-powered supplier matching based on your needs
- **Web Scraping**: Automated extraction of supplier information
- **Real-time Updates**: WebSocket-based progress notifications

### 💬 AI Chat Assistant
- **Context-Aware**: Understands your business context and history
- **Multi-Provider**: GROQ (primary) with Ollama fallback for reliability
- **Streaming Responses**: Real-time response streaming for better UX

### 📊 Business Intelligence
- **Market Research**: Automated competitive analysis and market insights
- **Analytics**: Track business metrics and supplier performance
- **Reporting**: Generate comprehensive business reports

### 🛠️ Tool Database
- **Extensible**: Register custom tools and capabilities
- **Analytics**: Track tool usage and performance
- **Version Control**: Manage tool versions and updates

## Authentication

Currently in development. API keys will be required for production use.

## Rate Limiting

- **Development**: No limits
- **Production**: 1000 requests/hour per IP

## Support

For issues, questions, or feature requests:
- GitHub: https://github.com/RHUDHRESH/Artisan
- Email: support@artisanhub.com (placeholder)

## Version History

- **1.0.0** (Current): Initial production release with multi-agent orchestration
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    terms_of_service="https://artisanhub.com/terms",
    contact={
        "name": "Artisan Hub Support",
        "url": "https://github.com/RHUDHRESH/Artisan",
        "email": "support@artisanhub.com"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    },
    openapi_tags=[
        {
            "name": "Health",
            "description": "Health check and monitoring endpoints"
        },
        {
            "name": "Chat",
            "description": "AI chat assistant endpoints"
        },
        {
            "name": "Agents",
            "description": "Multi-agent orchestration and management"
        },
        {
            "name": "Search",
            "description": "Supplier search and discovery"
        },
        {
            "name": "Maps",
            "description": "Geographic mapping and visualization"
        },
        {
            "name": "Context",
            "description": "Business context and profile management"
        },
        {
            "name": "Settings",
            "description": "Application settings and configuration"
        },
        {
            "name": "Orchestration",
            "description": "Advanced agent orchestration with LangGraph"
        },
        {
            "name": "Monitoring",
            "description": "Metrics, health checks, and observability"
        }
    ]
)

# Initialize monitoring
from backend.core.monitoring import (
    MonitoringMiddleware,
    setup_logging,
    set_app_info
)

setup_logging(
    log_level=settings.log_level,
    json_logs=settings.environment == "production"
)

set_app_info(
    version="1.0.0",
    environment=settings.environment,
    commit_sha=settings.commit_sha if hasattr(settings, 'commit_sha') else "unknown"
)

# Add monitoring middleware
app.add_middleware(MonitoringMiddleware)

# CORS Configuration - Use settings
cors_origins = settings.cors_origins.split(",") if settings.cors_origins != "*" else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Artisan Hub API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    llm_client = OllamaClient()
    try:
        llm_ok = await llm_client.health_check()
    except Exception:
        llm_ok = False

    return HealthResponse(
        status="healthy" if llm_ok else "degraded",
        message="Cloud LLM reachable" if llm_ok else "No cloud LLM provider reachable",
        ollama_connected=llm_ok
    )


@app.get("/health/flight-check")
async def flight_check():
    """
    Comprehensive dependency and readiness report.
    """
    checker = FlightCheck()
    return await checker.run()


# Include routers
from backend.api.routes import chat, agents, maps, search, context, settings, orchestration, monitoring
from fastapi import WebSocket

app.include_router(chat.router)
app.include_router(agents.router)
app.include_router(maps.router)
app.include_router(search.router)
app.include_router(context.router)
app.include_router(settings.router)
app.include_router(orchestration.router)
app.include_router(monitoring.router)

@app.websocket("/ws")
async def websocket_route(websocket: WebSocket):
    """WebSocket endpoint"""
    from backend.api.websocket import websocket_endpoint
    await websocket_endpoint(websocket)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.environment != "production",
        log_level=settings.log_level
    )
