"""
Lightweight checks for the cloud-only LLM manager.
"""

import pytest

from backend.core.llm_provider import LLMManager, LLMProvider


@pytest.mark.unit
def test_llm_provider_enum_values():
    """Ensure enum values match configured providers."""
    assert LLMProvider.GROQ.value == "groq"
    assert LLMProvider.OPENROUTER.value == "openrouter"
    assert LLMProvider.GEMINI.value == "gemini"
    assert LLMProvider.AUTO.value == "auto"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_llm_manager_health_shape():
    """Health check returns structured provider data."""
    manager = LLMManager(primary_provider=LLMProvider.GROQ)
    status = await manager.health_check()
    assert "providers" in status
    assert isinstance(status.get("providers"), dict)
    assert "healthy" in status
