"""
Artisan Hub - FastAPI Application Entry Point
Minimal mode optimized for Render free tier deployment
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
import os

# Lightweight logging
from loguru import logger

# Comprehensive API documentation
app = FastAPI(
    title="Artisan Hub API",
    description="""
# Artisan Hub - AI-Powered Platform for Artisans

## Overview

Artisan Hub is an AI-powered ecosystem designed to empower local craftspeople and artisans
with intelligent tools for supplier discovery, market research, business management, and more.

## Deployment Mode

**Current Mode**: Minimal (optimized for free tier)
- To enable full AI/ML features, set `ENABLE_HEAVY_FEATURES=true` and deploy on 1GB+ instance

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
- **Multi-Provider**: GROQ (primary) with OpenRouter + Gemini fallbacks (cloud-only)
- **Streaming Responses**: Real-time response streaming for better UX

### 📊 Business Intelligence
- **Market Research**: Automated competitive analysis and market insights
- **Analytics**: Track business metrics and supplier performance
- **Reporting**: Generate comprehensive business reports

## Authentication

Currently in development. API keys will be required for production use.

## Support

For issues, questions, or feature requests:
- GitHub: https://github.com/RHUDHRESH/Artisan

## Version History

- **1.0.0** (Current): Initial production release with multi-agent orchestration
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={
        "name": "Artisan Hub Support",
        "url": "https://github.com/RHUDHRESH/Artisan",
        "email": "support@artisanhub.com"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    }
)

# Setup logging
logger.info(f"Starting Artisan Hub API v1.0.0")
logger.info(f"Environment: {settings.environment}")

# Force enable heavy features for now (temporary)
import os
os.environ['ENABLE_HEAVY_FEATURES'] = 'true'
settings.enable_heavy_features = True

logger.info(f"Heavy features enabled: {settings.enable_heavy_features}")

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
        "status": "running",
        "mode": "full" if settings.enable_heavy_features else "minimal",
        "features_enabled": settings.enable_heavy_features
    }


@app.get("/health")
async def health_check():
    """Health check endpoint - lightweight version"""
    from backend.models import HealthResponse
    
    health_status = {
        "status": "healthy",
        "message": "API is running",
        "mode": "full" if settings.enable_heavy_features else "minimal"
    }
    
    # Only check LLM if heavy features enabled
    if settings.enable_heavy_features:
        try:
            from backend.core.ollama_client import OllamaClient
            llm_client = OllamaClient()
            provider_statuses = await llm_client.provider_statuses()
            llm_ok = any(provider_statuses.values())
            health_status["llm_connected"] = llm_ok
            health_status["providers"] = provider_statuses
            if not llm_ok:
                health_status["status"] = "degraded"
                health_status["message"] = "API running but LLM provider unreachable"
        except Exception as e:
            logger.warning(f"LLM health check failed: {e}")
            health_status["llm_connected"] = False
            health_status["status"] = "degraded"
    else:
        health_status["llm_connected"] = None
        health_status["message"] = "Minimal mode - LLM features disabled"
    
    return HealthResponse(**health_status)


# Conditionally load heavy features
if settings.enable_heavy_features:
    logger.info("Loading heavy features (monitoring, agents, orchestration)...")
    
    try:
        # Initialize monitoring
        from backend.core.monitoring import (
            MonitoringMiddleware,
            setup_logging as setup_monitoring_logging,
            set_app_info
        )
        
        setup_monitoring_logging(
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
        logger.info("✓ Monitoring enabled")
        
    except ImportError as e:
        logger.warning(f"Could not load monitoring: {e}")
    
    try:
        # Include full routers
        from backend.api.routes import chat, agents, maps, search, context, settings as settings_router, orchestration, monitoring
        from fastapi import WebSocket
        
        app.include_router(chat.router)
        app.include_router(agents.router)
        app.include_router(maps.router)
        app.include_router(search.router)
        app.include_router(context.router)
        app.include_router(settings_router.router)
        app.include_router(orchestration.router)
        app.include_router(monitoring.router)
        logger.info("✓ All API routes loaded")
        
        @app.websocket("/ws")
        async def websocket_route(websocket: WebSocket):
            """WebSocket endpoint"""
            from backend.api.websocket import websocket_endpoint
            await websocket_endpoint(websocket)
        
        logger.info("✓ WebSocket endpoint enabled")
        
    except ImportError as e:
        logger.error(f"Could not load API routes: {e}")
        logger.warning("Running in degraded mode - only basic endpoints available")
    
    try:
        # Flight check endpoint
        from backend.core.flight_check import FlightCheck
        
        @app.get("/health/flight-check")
        async def flight_check():
            """Comprehensive dependency and readiness report."""
            checker = FlightCheck()
            return await checker.run()
        
        logger.info("✓ Flight check endpoint enabled")
        
    except ImportError as e:
        logger.warning(f"Could not load flight check: {e}")

else:
    logger.info("Running in MINIMAL mode - heavy features disabled")
    logger.info("To enable full features, set ENABLE_HEAVY_FEATURES=true")
    
    # Minimal chat endpoint using just GROQ
    try:
        from fastapi import APIRouter
        from pydantic import BaseModel
        
        minimal_router = APIRouter(prefix="/api", tags=["minimal"])
        
        class ChatRequest(BaseModel):
            message: str
            
        class ChatResponse(BaseModel):
            response: str
            mode: str = "minimal"
        
        @minimal_router.post("/chat", response_model=ChatResponse)
        async def minimal_chat(request: ChatRequest):
            """Minimal chat endpoint using GROQ API directly"""
            if not settings.groq_api_key:
                return ChatResponse(
                    response="GROQ API key not configured. Please set GROQ_API_KEY environment variable.",
                    mode="minimal"
                )
            
            try:
                from groq import Groq
                client = Groq(api_key=settings.groq_api_key)
                
                completion = client.chat.completions.create(
                    model="mixtral-8x7b-32768",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant for artisans and craftspeople."},
                        {"role": "user", "content": request.message}
                    ],
                    temperature=0.7,
                    max_tokens=1024,
                )
                
                return ChatResponse(
                    response=completion.choices[0].message.content,
                    mode="minimal"
                )
                
            except Exception as e:
                logger.error(f"Minimal chat error: {e}")
                return ChatResponse(
                    response=f"Error: {str(e)}",
                    mode="minimal"
                )
        
        app.include_router(minimal_router)
        logger.info("✓ Minimal chat endpoint enabled")
        
    except ImportError as e:
        logger.warning(f"Could not enable minimal chat: {e}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", settings.port))
    logger.info(f"Starting server on port {port}")
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.environment != "production",
        log_level=settings.log_level.lower()
    )
