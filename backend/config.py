"""
Configuration management for Artisan Hub
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Ollama Configuration
    ollama_base_url: str = "http://localhost:11434"
    
    # Model Configuration
    embedding_model: str = "nomic-embed-text:latest"
    reasoning_model: str = "gemma3:4b"
    fast_model: str = "gemma3:1b"
    
    # Tavily API Configuration
    tavily_api_key: Optional[str] = None
    
    # SerpAPI Configuration (deprecated - using Tavily now)
    serpapi_key: Optional[str] = None
    
    # ChromaDB Configuration
    chroma_db_path: str = "./data/chroma_db"
    
    # Logging
    log_level: str = "INFO"
    
    # Firebase (optional)
    firebase_credentials_path: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

# Override with environment variables if present
if os.getenv("TAVILY_API_KEY"):
    settings.tavily_api_key = os.getenv("TAVILY_API_KEY")
elif os.getenv("SERPAPI_KEY"):
    settings.serpapi_key = os.getenv("SERPAPI_KEY")
if os.getenv("OLLAMA_BASE_URL"):
    settings.ollama_base_url = os.getenv("OLLAMA_BASE_URL")
if os.getenv("CHROMA_DB_PATH"):
    settings.chroma_db_path = os.getenv("CHROMA_DB_PATH")

# Set Tavily key from provided value
if not settings.tavily_api_key:
    settings.tavily_api_key = "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"

# Override with environment variables if present
if os.getenv("TAVILY_API_KEY"):
    settings.tavily_api_key = os.getenv("TAVILY_API_KEY")
if os.getenv("SERPAPI_KEY"):
    settings.serpapi_key = os.getenv("SERPAPI_KEY")
if os.getenv("OLLAMA_BASE_URL"):
    settings.ollama_base_url = os.getenv("OLLAMA_BASE_URL")
if os.getenv("CHROMA_DB_PATH"):
    settings.chroma_db_path = os.getenv("CHROMA_DB_PATH")
if os.getenv("LOG_LEVEL"):
    settings.log_level = os.getenv("LOG_LEVEL")
if os.getenv("EMBEDDING_MODEL"):
    settings.embedding_model = os.getenv("EMBEDDING_MODEL")
if os.getenv("REASONING_MODEL"):
    settings.reasoning_model = os.getenv("REASONING_MODEL")
if os.getenv("FAST_MODEL"):
    settings.fast_model = os.getenv("FAST_MODEL")
