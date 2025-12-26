"""
Configuration management for Artisan Hub
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os
from backend.constants import (
    EMBEDDING_MODEL_DEFAULT,
    REASONING_MODEL_DEFAULT,
    FAST_MODEL_DEFAULT,
    LOG_LEVEL_DEFAULT
)


class Settings(BaseSettings):
    """Application settings"""

    # LLM Provider Configuration - FREE TRIAL OPTIMIZED! 💰
    llm_provider: str = "openai"  # Default to cheapest OpenAI model, fallback to Groq
    groq_api_key: Optional[str] = None

    # Cloud LLM Configuration - Cost-optimized free trials
    openrouter_api_key: Optional[str] = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_reasoning_model: str = "microsoft/wizardlm-2-8x22b"  # CHEAP but good quality
    openrouter_fast_model: str = "microsoft/wizardlm-2-8x22b"  # CHEAP fast model
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-1.5-flash"  # Use basic flash, not 002 (more expensive)
    openai_api_key: Optional[str] = None
    openai_reasoning_model: str = "gpt-4o-mini"
    openai_fast_model: str = "gpt-4o-mini"


    # Model Configuration - COST-EFFECTIVE free trial setup
    embedding_model: str = "openai/text-embedding-3-small"
    reasoning_model: str = "llama-3.1-70b-versatile"  # Groq's best cheap model
    fast_model: str = "llama-3.1-8b-instant"  # Groq's fast cheap model

    # Cost optimization settings
    enable_expensive_models: bool = False  # Set to True ONLY when you have credits
    max_tokens_per_request: int = 2000  # Limit expensive API calls

    # Tavily API Configuration
    tavily_api_key: Optional[str] = None

    # SerpAPI Configuration (deprecated - using Tavily now)
    serpapi_key: Optional[str] = None

    # Logging
    log_level: str = LOG_LEVEL_DEFAULT

    # Environment metadata
    environment: str = "development"
    commit_sha: str = "unknown"
    
    # Feature flags
    enable_heavy_features: bool = False  # Set to True to load AI/ML stack (needs 1GB+ RAM)
    port: int = 8000  # Server port, overridden by PORT env var

    # Firebase (optional)
    firebase_credentials_path: Optional[str] = None

    # Supabase (optional)
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None
    supabase_jwt_secret: Optional[str] = None

    # Redis configuration
    redis_url: str = "redis://localhost:6379"

    # Backend URL (for frontend)
    backend_url: str = "http://localhost:8000"

    # CORS Origins (comma-separated)
    # Default "*" allows all origins - ONLY for development
    # For production, set to your actual domains: "https://app.vercel.app,https://yourdomain.com"
    cors_origins: str = "*"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"


# Global settings instance
settings = Settings()

# Environment variable overrides (single pass, no duplication)
# Note: Pydantic Settings already loads from .env, but we explicitly
# override for clarity and additional environment variables
env_overrides = {
    "LLM_PROVIDER": "llm_provider",
    "GROQ_API_KEY": "groq_api_key",
    "TAVILY_API_KEY": "tavily_api_key",
    "SERPAPI_KEY": "serpapi_key",
    "OPENROUTER_API_KEY": "openrouter_api_key",
    "OPENROUTER_BASE_URL": "openrouter_base_url",
    "OPENROUTER_REASONING_MODEL": "openrouter_reasoning_model",
    "OPENROUTER_FAST_MODEL": "openrouter_fast_model",
    "GEMINI_API_KEY": "gemini_api_key",
    "GEMINI_MODEL": "gemini_model",
    "OPENAI_API_KEY": "openai_api_key",
    "OPENAI_REASONING_MODEL": "openai_reasoning_model",
    "OPENAI_FAST_MODEL": "openai_fast_model",
    "LOG_LEVEL": "log_level",
    "EMBEDDING_MODEL": "embedding_model",
    "REASONING_MODEL": "reasoning_model",
    "FAST_MODEL": "fast_model",
    "BACKEND_URL": "backend_url",
    "CORS_ORIGINS": "cors_origins",
    "ENVIRONMENT": "environment",
    "COMMIT_SHA": "commit_sha",
    "SUPABASE_URL": "supabase_url",
    "SUPABASE_KEY": "supabase_key",
    "SUPABASE_JWT_SECRET": "supabase_jwt_secret",
    "REDIS_URL": "redis_url",
    "ENABLE_HEAVY_FEATURES": "enable_heavy_features",
    "PORT": "port",
}

for env_var, setting_attr in env_overrides.items():
    env_value = os.getenv(env_var)
    if env_value:
        setattr(settings, setting_attr, env_value)
