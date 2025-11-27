"""
Settings API Routes - Manage application settings at runtime
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from loguru import logger

from backend.config import settings
from backend.core.llm_provider import LLMProvider, LLMManager

router = APIRouter(prefix="/settings", tags=["settings"])


class SettingsUpdate(BaseModel):
    """Settings update model"""
    llm_provider: Optional[str] = Field(None, description="LLM provider: groq, openrouter, gemini, or auto")
    groq_api_key: Optional[str] = Field(None, description="GROQ API key")
    openrouter_api_key: Optional[str] = Field(None, description="OpenRouter API key")
    gemini_api_key: Optional[str] = Field(None, description="Gemini API key")
    tavily_api_key: Optional[str] = Field(None, description="Tavily API key")
    cors_origins: Optional[str] = Field(None, description="CORS origins (comma-separated)")
    log_level: Optional[str] = Field(None, description="Log level: DEBUG, INFO, WARNING, ERROR")


class SettingsResponse(BaseModel):
    """Settings response model"""
    llm_provider: str
    groq_api_key_configured: bool
    openrouter_api_key_configured: bool
    gemini_api_key_configured: bool
    tavily_api_key_configured: bool
    cors_origins: str
    log_level: str
    backend_url: str


@router.get("", response_model=SettingsResponse)
async def get_settings():
    """Get current application settings"""
    try:
        return SettingsResponse(
            llm_provider=settings.llm_provider,
            groq_api_key_configured=bool(settings.groq_api_key and settings.groq_api_key != "your-groq-api-key-here"),
            openrouter_api_key_configured=bool(settings.openrouter_api_key),
            gemini_api_key_configured=bool(settings.gemini_api_key),
            tavily_api_key_configured=bool(settings.tavily_api_key),
            cors_origins=settings.cors_origins,
            log_level=settings.log_level,
            backend_url=settings.backend_url
        )
    except Exception as e:
        logger.error(f"Failed to get settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("", response_model=SettingsResponse)
async def update_settings(update: SettingsUpdate):
    """Update application settings"""
    try:
        # Update LLM provider
        if update.llm_provider:
            if update.llm_provider not in ["groq", "openrouter", "gemini", "auto"]:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid LLM provider. Must be one of: groq, openrouter, gemini, auto"
                )
            settings.llm_provider = update.llm_provider
            logger.info(f"Updated LLM provider to: {update.llm_provider}")

        # Update GROQ API key
        if update.groq_api_key:
            settings.groq_api_key = update.groq_api_key
            logger.info("Updated GROQ API key")

        if update.openrouter_api_key:
            settings.openrouter_api_key = update.openrouter_api_key
            logger.info("Updated OpenRouter API key")

        if update.gemini_api_key:
            settings.gemini_api_key = update.gemini_api_key
            logger.info("Updated Gemini API key")

        # Update Tavily API key
        if update.tavily_api_key:
            settings.tavily_api_key = update.tavily_api_key
            logger.info("Updated Tavily API key")

        # Update CORS origins
        if update.cors_origins:
            settings.cors_origins = update.cors_origins
            logger.info(f"Updated CORS origins to: {update.cors_origins}")
            logger.warning("⚠️ CORS changes require server restart to take effect")

        # Update log level
        if update.log_level:
            if update.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid log level"
                )
            settings.log_level = update.log_level
            logger.info(f"Updated log level to: {update.log_level}")

        return await get_settings()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/providers/health")
async def check_providers_health():
    """Check health of all LLM providers"""
    try:
        # Create LLM manager with current settings
        async with LLMManager(
            primary_provider=LLMProvider(settings.llm_provider),
            groq_api_key=settings.groq_api_key,
            openrouter_api_key=settings.openrouter_api_key,
            gemini_api_key=settings.gemini_api_key,
        ) as llm_manager:
            health_status = await llm_manager.health_check()

        return {
            "status": "success",
            "providers": health_status,
            "current_provider": settings.llm_provider
        }

    except Exception as e:
        logger.error(f"Failed to check providers health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/providers/test")
async def test_provider(provider: str):
    """Test a specific LLM provider"""
    try:
        if provider not in ["groq", "openrouter", "gemini"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid provider. Must be one of: groq, openrouter, gemini"
            )

        # Create LLM manager with specified provider
        async with LLMManager(
            primary_provider=LLMProvider(provider),
            groq_api_key=settings.groq_api_key,
            openrouter_api_key=settings.openrouter_api_key,
            gemini_api_key=settings.gemini_api_key,
        ) as llm_manager:
            # Try a simple test
            result = await llm_manager.fast_task(
                prompt="Say 'Hello from Artisan Hub!' and nothing else.",
                temperature=0.1
            )

        return {
            "status": "success",
            "provider": provider,
            "test_result": result[:200],
            "message": f"{provider.upper()} provider is working correctly"
        }

    except Exception as e:
        logger.error(f"Provider test failed for {provider}: {e}")
        return {
            "status": "error",
            "provider": provider,
            "error": str(e),
            "message": f"{provider.upper()} provider is not available"
        }


@router.get("/defaults")
async def get_default_settings():
    """Get default settings for reference"""
    return {
        "llm_provider": "groq",
        "cors_origins": "*",
        "log_level": "INFO",
        "backend_url": "http://localhost:8000",
        "groq_models": {
            "reasoning": "llama-3.3-70b-versatile",
            "fast": "llama-3.1-8b-instant"
        },
        "openrouter_models": {
            "reasoning": "openai/gpt-4o-mini",
            "fast": "openai/gpt-4o-mini",
            "embedding": "text-embedding-3-large"
        },
        "gemini_models": {
            "reasoning": "gemini-1.5-flash",
            "fast": "gemini-1.5-flash"
        }
    }
