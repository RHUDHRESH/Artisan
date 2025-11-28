"""
Cloud LLM provider manager (Groq → OpenRouter → Gemini).
Removes any dependency on local runtimes while keeping the previous interface.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional

from backend.config import settings
from backend.core.cloud_llm_client import CloudLLMClient


class LLMProvider(str, Enum):
    """Supported hosted LLM providers."""

    GROQ = "groq"
    OPENROUTER = "openrouter"
    GEMINI = "gemini"
    AUTO = "auto"


class LLMManager:
    """
    Thin wrapper that keeps the old `LLMManager` name but routes everything
    through the cloud-only client. It can still be used as a context manager.
    """

    def __init__(
        self,
        primary_provider: Optional[LLMProvider | str] = None,
        groq_api_key: Optional[str] = None,
        openrouter_api_key: Optional[str] = None,
        gemini_api_key: Optional[str] = None,
    ):
        preferred = (
            primary_provider.value if isinstance(primary_provider, LLMProvider) else primary_provider
        ) or settings.llm_provider
        self.primary_provider = (preferred or "groq").lower()

        self.client = CloudLLMClient(
            llm_provider=self.primary_provider,
            groq_api_key=groq_api_key or settings.groq_api_key,
            openrouter_api_key=openrouter_api_key or settings.openrouter_api_key,
            gemini_api_key=gemini_api_key or settings.gemini_api_key,
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return False

    def __getattr__(self, item: str) -> Any:
        # Proxy any missing attributes to the underlying client
        return getattr(self.client, item)

    async def reasoning_task(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
    ) -> str:
        return await self.client.reasoning_task(prompt=prompt, system=system, temperature=temperature)

    async def fast_task(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.3,
    ) -> str:
        return await self.client.fast_task(prompt=prompt, system=system, temperature=temperature)

    async def embed(self, text: str) -> Any:
        return await self.client.embed(text)

    async def health_check(self) -> Dict[str, Any]:
        statuses = await self.client.provider_statuses()
        active = next((p for p, ok in statuses.items() if ok), None)
        return {
            "providers": statuses,
            "active_provider": active,
            "configured_provider": self.primary_provider,
            "healthy": any(statuses.values()),
        }


# Re-export for backwards compatibility
HostedLLMClient = CloudLLMClient
OllamaClient = CloudLLMClient
