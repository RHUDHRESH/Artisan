"""
Tests for LLM provider system.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from backend.core.llm_provider import (
    GroqClient,
    OllamaClient,
    LLMManager,
    LLMProvider
)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_groq_client_initialization():
    """Test GROQ client initialization."""
    client = GroqClient(api_key="test-key")
    assert client.api_key == "test-key"
    assert client.default_model is not None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_ollama_client_initialization():
    """Test Ollama client initialization."""
    client = OllamaClient(base_url="http://localhost:11434")
    assert client.base_url == "http://localhost:11434"
    assert client.default_model is not None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_llm_manager_initialization():
    """Test LLM manager initialization."""
    manager = LLMManager(
        primary_provider=LLMProvider.GROQ,
        groq_api_key="test-key"
    )

    assert manager.primary_provider == LLMProvider.GROQ
    assert manager.groq_client is not None
    assert manager.ollama_client is not None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_groq_client_complete_mock():
    """Test GROQ client completion with mock."""
    with patch('groq.AsyncGroq') as mock_groq:
        # Setup mock
        mock_response = Mock()
        mock_response.choices = [
            Mock(message=Mock(content="Test response"))
        ]
        mock_response.usage = Mock(
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30
        )

        mock_groq_instance = AsyncMock()
        mock_groq_instance.chat.completions.create = AsyncMock(
            return_value=mock_response
        )
        mock_groq.return_value = mock_groq_instance

        # Test
        client = GroqClient(api_key="test-key")
        result = await client.complete(
            messages=[{"role": "user", "content": "Hello"}]
        )

        assert result == mock_response
        assert result.choices[0].message.content == "Test response"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_llm_manager_fallback():
    """Test LLM manager fallback mechanism."""
    with patch.object(GroqClient, 'complete', side_effect=Exception("GROQ unavailable")):
        with patch.object(OllamaClient, 'complete', return_value=Mock(choices=[Mock(message=Mock(content="Ollama response"))])):
            manager = LLMManager(
                primary_provider=LLMProvider.GROQ,
                groq_api_key="test-key"
            )

            result = await manager.complete(
                messages=[{"role": "user", "content": "Hello"}]
            )

            # Should fallback to Ollama
            assert result.choices[0].message.content == "Ollama response"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_groq_health_check_success():
    """Test GROQ health check success."""
    with patch('groq.AsyncGroq') as mock_groq:
        mock_groq_instance = AsyncMock()
        mock_groq_instance.models.list = AsyncMock(return_value=Mock())
        mock_groq.return_value = mock_groq_instance

        client = GroqClient(api_key="test-key")
        is_healthy = await client.health_check()

        assert is_healthy is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_groq_health_check_failure():
    """Test GROQ health check failure."""
    with patch('groq.AsyncGroq') as mock_groq:
        mock_groq_instance = AsyncMock()
        mock_groq_instance.models.list = AsyncMock(
            side_effect=Exception("Connection failed")
        )
        mock_groq.return_value = mock_groq_instance

        client = GroqClient(api_key="test-key")
        is_healthy = await client.health_check()

        assert is_healthy is False


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.slow
async def test_ollama_health_check_integration():
    """Test Ollama health check with real connection."""
    # This test requires Ollama to be running
    client = OllamaClient(base_url="http://localhost:11434")

    try:
        is_healthy = await client.health_check()
        # If Ollama is running, should be True
        # If not running, should be False
        assert isinstance(is_healthy, bool)
    except Exception:
        pytest.skip("Ollama not available for integration test")


@pytest.mark.unit
def test_llm_provider_enum():
    """Test LLM provider enumeration."""
    assert LLMProvider.GROQ.value == "groq"
    assert LLMProvider.OLLAMA.value == "ollama"

    # Test string conversion
    assert LLMProvider("groq") == LLMProvider.GROQ
    assert LLMProvider("ollama") == LLMProvider.OLLAMA
