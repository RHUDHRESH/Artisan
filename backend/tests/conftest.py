"""
Pytest configuration and fixtures for Artisan Hub tests.
"""

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient
from fastapi.testclient import TestClient
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from backend.main import app
from backend.orchestration.tool_database import Base


# ============================================================================
# Event Loop Configuration
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Test Client Fixtures
# ============================================================================

@pytest.fixture
def client() -> Generator:
    """Create a synchronous test client."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
async def async_client() -> AsyncGenerator:
    """Create an asynchronous test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture(scope="session")
async def test_db_engine():
    """Create a test database engine."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def db_session(test_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session = sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        yield session
        await session.rollback()


# ============================================================================
# Redis Fixtures
# ============================================================================

@pytest.fixture
async def redis_client() -> AsyncGenerator:
    """Create a test Redis client."""
    client = redis.from_url("redis://localhost:6379/1")  # Use DB 1 for tests

    yield client

    # Cleanup
    await client.flushdb()
    await client.close()


# ============================================================================
# Mock LLM Provider Fixtures
# ============================================================================

@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing."""
    class MockResponse:
        def __init__(self):
            self.choices = [
                type('obj', (object,), {
                    'message': type('obj', (object,), {
                        'content': 'This is a mock LLM response.'
                    })()
                })()
            ]
            self.usage = type('obj', (object,), {
                'prompt_tokens': 10,
                'completion_tokens': 20,
                'total_tokens': 30
            })()

    return MockResponse()


@pytest.fixture
def mock_groq_client(monkeypatch, mock_llm_response):
    """Mock GROQ client for testing."""
    async def mock_chat_completion(*args, **kwargs):
        return mock_llm_response

    # Mock the actual GROQ client
    class MockGroqClient:
        async def health_check(self):
            return True

        async def complete(self, *args, **kwargs):
            return mock_llm_response

    return MockGroqClient()


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def sample_supplier_data():
    """Sample supplier data for testing."""
    return {
        "name": "Test Supplier Co.",
        "email": "contact@testsupplier.com",
        "phone": "+1-555-0123",
        "website": "https://testsupplier.com",
        "address": "123 Test Street, Test City, TC 12345",
        "products": ["widgets", "gadgets", "tools"],
        "min_order_value": 1000.00,
        "shipping_regions": ["North America", "Europe"]
    }


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "id": "test-user-123",
        "email": "testuser@example.com",
        "name": "Test User",
        "business_name": "Test Artisan Business",
        "business_type": "pottery"
    }


@pytest.fixture
def sample_search_query():
    """Sample search query for testing."""
    return {
        "query": "ceramic suppliers near me",
        "filters": {
            "min_order_value": {"max": 5000},
            "shipping_regions": ["North America"]
        },
        "limit": 10
    }


@pytest.fixture
def sample_agent_spec():
    """Sample agent specification for testing."""
    return {
        "name": "test_researcher",
        "role": "research",
        "capabilities": ["web_search", "data_analysis"],
        "description": "Test research agent",
        "system_message": "You are a test research agent.",
        "temperature": 0.7,
        "max_tokens": 1000
    }


@pytest.fixture
def sample_tool_data():
    """Sample tool data for testing."""
    return {
        "name": "test_calculator",
        "description": "A test calculator tool",
        "category": "math",
        "parameters": {
            "type": "object",
            "properties": {
                "operation": {"type": "string"},
                "a": {"type": "number"},
                "b": {"type": "number"}
            },
            "required": ["operation", "a", "b"]
        }
    }


# ============================================================================
# Environment Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Set up test environment variables."""
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("GROQ_API_KEY", "test-api-key-123")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/1")
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")


# ============================================================================
# Cleanup Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
async def cleanup_between_tests():
    """Cleanup between tests."""
    yield
    # Any cleanup needed between tests
    pass


# ============================================================================
# Performance Testing Fixtures
# ============================================================================

@pytest.fixture
def performance_threshold():
    """Performance thresholds for testing."""
    return {
        "api_response_time": 1.0,  # seconds
        "agent_execution_time": 30.0,  # seconds
        "llm_request_time": 10.0,  # seconds
        "db_query_time": 0.5,  # seconds
    }


# ============================================================================
# Markers
# ============================================================================

def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )
