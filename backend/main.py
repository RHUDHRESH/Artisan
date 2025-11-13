"""
Artisan Hub - FastAPI Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.models import HealthResponse
from backend.config import settings
import requests
import uvicorn

app = FastAPI(
    title="Artisan Hub API",
    description="AI-Powered Ecosystem for Local Craftspeople",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
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
    try:
        # Check Ollama connection
        response = requests.get(
            f"{settings.ollama_base_url}/api/tags",
            timeout=5
        )
        ollama_ok = response.status_code == 200
    except:
        ollama_ok = False
    
    return HealthResponse(
        status="healthy" if ollama_ok else "degraded",
        message="Ollama connected" if ollama_ok else "Ollama not connected",
        ollama_connected=ollama_ok
    )


@app.get("/health/flight-check")
async def flight_check():
    """
    Comprehensive flight check - verifies all backend dependencies
    Returns detailed status of Ollama, ChromaDB, SerpAPI, and other services
    """
    from datetime import datetime
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "overall_status": "unknown",
        "checks": {},
        "errors": []
    }
    
    # Wrap entire function in try-except to catch any unexpected errors
    try:
        # Check 1: Ollama
        ollama_check = {
            "status": "unknown",
            "message": "",
            "details": {}
        }
        try:
            response = requests.get(
                f"{settings.ollama_base_url}/api/tags",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                models = [m.get("name", "") for m in data.get("models", [])]
                available_models = [m for m in models if any(req in m for req in ["gemma3:4b", "gemma3:1b", "gemma3"])]
                
                ollama_check["status"] = "healthy" if available_models else "degraded"
                ollama_check["message"] = f"Ollama connected. Found {len(available_models)} Gemma3 models"
                ollama_check["details"] = {
                    "base_url": settings.ollama_base_url,
                    "available_models": available_models,
                    "all_models": models[:5]  # First 5 models
                }
            else:
                ollama_check["status"] = "unhealthy"
                ollama_check["message"] = f"Ollama returned status {response.status_code}"
                ollama_check["details"] = {"error": f"HTTP {response.status_code}"}
        except requests.exceptions.ConnectionError:
            ollama_check["status"] = "unhealthy"
            ollama_check["message"] = f"Cannot connect to Ollama at {settings.ollama_base_url}"
            ollama_check["details"] = {"error": "Connection refused - is Ollama running?", "url": settings.ollama_base_url}
        except Exception as e:
            ollama_check["status"] = "unhealthy"
            ollama_check["message"] = f"Ollama check failed: {str(e)}"
            ollama_check["details"] = {"error": str(e), "error_type": type(e).__name__}
        
        results["checks"]["ollama"] = ollama_check
        
        # Check 2: Test Ollama model generation (quick test)
        ollama_test = {
            "status": "unknown",
            "message": "",
            "details": {}
        }
        try:
            from backend.core.ollama_client import OllamaClient
            
            # Simple synchronous test to avoid asyncio conflicts
            async def simple_test():
                try:
                    async with OllamaClient() as client:
                        # Quick test with fast model
                        result = await client.fast_task("Say OK")
                        return True, result[:50]
                except Exception as e:
                    return False, str(e)
            
            # Use asyncio.create_task to avoid event loop conflicts
            import asyncio
            task = asyncio.create_task(simple_test())
            test_result = await task
            
            if test_result[0]:
                ollama_test["status"] = "healthy"
                ollama_test["message"] = "Ollama model generation working"
                ollama_test["details"] = {"test_response": test_result[1]}
            else:
                ollama_test["status"] = "unhealthy"
                ollama_test["message"] = f"Ollama generation failed: {test_result[1]}"
                ollama_test["details"] = {"error": test_result[1]}
        except Exception as e:
            ollama_test["status"] = "unhealthy"
            ollama_test["message"] = f"Ollama test error: {str(e)}"
            ollama_test["details"] = {"error": str(e), "error_type": type(e).__name__}
        
        results["checks"]["ollama_generation"] = ollama_test
        
        # Check 3: ChromaDB - auto-initialize
        chroma_check = {
            "status": "unknown",
            "message": "",
            "details": {}
        }
        try:
            from backend.core.vector_store import ArtisanVectorStore
            import os
            # Ensure data directory exists
            os.makedirs(settings.chroma_db_path, exist_ok=True)
            
            # Simple test to verify ChromaDB works
            vector_store = ArtisanVectorStore()
            collection = vector_store.get_collection()
            collection_count = collection.count() if collection else 0
            
            chroma_check["status"] = "healthy"
            chroma_check["message"] = f"ChromaDB accessible with {collection_count} documents"
            chroma_check["details"] = {
                "db_path": settings.chroma_db_path,
                "collection_name": vector_store.collection_name,
                "collections": list(vector_store.collections.keys()),
                "document_count": collection_count
            }
        except Exception as e:
            chroma_check["status"] = "unhealthy"
            chroma_check["message"] = f"ChromaDB error: {str(e)}"
            chroma_check["details"] = {"error": str(e), "error_type": type(e).__name__}
        
        results["checks"]["chromadb"] = chroma_check
        
        # Check 4: Tavily API (preferred) and SerpAPI (fallback)
        tavily_check = {
            "status": "unknown",
            "message": "",
            "details": {}
        }
        if settings.tavily_api_key:
            tavily_check["status"] = "healthy"
            tavily_check["message"] = "Tavily API key configured"
            tavily_check["details"] = {
                "key_set": True,
                "key_preview": f"{settings.tavily_api_key[:8]}..." if len(settings.tavily_api_key) > 8 else "***",
                "provider": "tavily"
            }
        elif settings.serpapi_key:
            tavily_check["status"] = "warning"
            tavily_check["message"] = "Using SerpAPI (Tavily preferred)"
            tavily_check["details"] = {
                "key_set": True,
                "provider": "serpapi",
                "note": "Consider switching to Tavily API"
            }
        else:
            tavily_check["status"] = "unhealthy"
            tavily_check["message"] = "No search API key configured"
            tavily_check["details"] = {
                "key_set": False,
                "note": "Set TAVILY_API_KEY environment variable for web search"
            }
        
        results["checks"]["tavily"] = tavily_check
        results["checks"]["serpapi"] = tavily_check  # For backward compatibility
        
        # Check 5: WebSocket connections
        websocket_check = {
            "status": "unknown",
            "message": "",
            "details": {}
        }
        try:
            from backend.api.websocket import manager
            active_connections = len(manager.active_connections)
            websocket_check["status"] = "healthy"
            websocket_check["message"] = f"WebSocket manager active ({active_connections} connections)"
            websocket_check["details"] = {
                "active_connections": active_connections
            }
        except Exception as e:
            websocket_check["status"] = "unhealthy"
            websocket_check["message"] = f"WebSocket error: {str(e)}"
            websocket_check["details"] = {"error": str(e), "error_type": type(e).__name__}
        
        results["checks"]["websocket"] = websocket_check
        
        # Determine overall status
        all_statuses = [check["status"] for check in results["checks"].values()]
        if all(s == "healthy" for s in all_statuses):
            results["overall_status"] = "healthy"
        elif any(s == "unhealthy" for s in all_statuses):
            results["overall_status"] = "degraded"
        elif any(s in ["warning", "degraded"] for s in all_statuses):
            results["overall_status"] = "warning"
        else:
            results["overall_status"] = "unknown"
        
        # Add error details if any checks failed
        for check_name, check in results["checks"].items():
            if check["status"] in ["unhealthy", "error"]:
                results["errors"].append({
                    "component": check_name,
                    "status": check["status"],
                    "message": check["message"],
                    "details": check.get("details", {})
                })
    
    except Exception as e:
        # Catch any unexpected errors in the flight check itself
        # Still populate checks with unknown status if we didn't get them
        if not results.get("checks"):
            results["checks"] = {
                "ollama": {
                    "status": "unknown",
                    "message": "Check failed due to error",
                    "details": {"error": str(e)}
                },
                "ollama_generation": {
                    "status": "unknown",
                    "message": "Check failed due to error",
                    "details": {"error": str(e)}
                },
                "chromadb": {
                    "status": "unknown",
                    "message": "Check failed due to error",
                    "details": {"error": str(e)}
                },
                "serpapi": {
                    "status": "unknown",
                    "message": "Check failed due to error",
                    "details": {"error": str(e)}
                },
                "websocket": {
                    "status": "unknown",
                    "message": "Check failed due to error",
                    "details": {"error": str(e)}
                }
            }
        
        results["overall_status"] = "error"
        results["errors"].append({
            "component": "flight_check",
            "status": "error",
            "message": f"Flight check failed: {str(e)}",
            "details": {"error_type": type(e).__name__, "error": str(e)}
        })
        try:
            from loguru import logger
            logger.error(f"Flight check error: {e}", exc_info=True)
        except ImportError:
            print(f"Flight check error: {e}")
    
    # Ensure checks object always exists
    if not results.get("checks"):
        results["checks"] = {}
    
    return results


# Include routers
from backend.api.routes import chat, agents, maps, search, context
from fastapi import WebSocket

app.include_router(chat.router)
app.include_router(agents.router)
app.include_router(maps.router)
app.include_router(search.router)
app.include_router(context.router)

@app.websocket("/ws")
async def websocket_route(websocket: WebSocket):
    """WebSocket endpoint"""
    from backend.api.websocket import websocket_endpoint
    await websocket_endpoint(websocket)


if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
