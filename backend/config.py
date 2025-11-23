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
    VECTOR_STORE_DEFAULT_PATH,
    LOG_LEVEL_DEFAULT
)


class Settings(BaseSettings):
    """Application settings"""

    # LLM Provider Configuration
    llm_provider: str = "groq"  # Options: "groq" (primary), "ollama" (fallback)
    groq_api_key: Optional[str] = None

    # Ollama Configuration
    ollama_base_url: str = "http://localhost:11434"

    # Model Configuration
    embedding_model: str = EMBEDDING_MODEL_DEFAULT
    reasoning_model: str = REASONING_MODEL_DEFAULT
    fast_model: str = FAST_MODEL_DEFAULT

    # Tavily API Configuration
    tavily_api_key: Optional[str] = None

    # SerpAPI Configuration (deprecated - using Tavily now)
    serpapi_key: Optional[str] = None

    # ChromaDB Configuration
    chroma_db_path: str = VECTOR_STORE_DEFAULT_PATH

    # Logging
    log_level: str = LOG_LEVEL_DEFAULT

    # Firebase (optional)
    firebase_credentials_path: Optional[str] = None

    # Backend URL (for frontend)
    backend_url: str = "http://localhost:8000"

    # CORS Origins (comma-separated)
    cors_origins: str = "*"  # Default for development, should be configured for production
    
    class Config:
        env_file = ".env"
        case_sensitive = False


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
    "OLLAMA_BASE_URL": "ollama_base_url",
    "CHROMA_DB_PATH": "chroma_db_path",
    "LOG_LEVEL": "log_level",
    "EMBEDDING_MODEL": "embedding_model",
    "REASONING_MODEL": "reasoning_model",
    "FAST_MODEL": "fast_model",
    "BACKEND_URL": "backend_url",
    "CORS_ORIGINS": "cors_origins",
}

for env_var, setting_attr in env_overrides.items():
    env_value = os.getenv(env_var)
    if env_value:
        setattr(settings, setting_attr, env_value)
