"""
Regression tests for web search readiness and agent error propagation.
"""
import pytest

from backend.config import settings
from backend.core.flight_check import FlightCheck
from backend.scraping.web_scraper import WebScraperService
from backend.agents.supply_hunter import SupplyHunterAgent


class _DummyLLM:
    async def reasoning_task(self, _: str) -> str:
        return "{}"


class _DummyVectorStore:
    """Minimal stub to satisfy BaseAgent requirements."""


@pytest.fixture(autouse=True)
def restore_search_keys():
    """Reset Tavily/SerpAPI keys after each test to avoid cross-test bleed."""
    original_tavily = settings.tavily_api_key
    original_serp = settings.serpapi_key
    try:
        yield
    finally:
        settings.tavily_api_key = original_tavily
        settings.serpapi_key = original_serp


@pytest.mark.asyncio
async def test_flight_check_marks_web_search_blocking_without_keys():
    """Flight check should mark web_search unhealthy + blocking when no API key is set."""
    settings.tavily_api_key = ""
    settings.serpapi_key = ""

    checker = FlightCheck()
    await checker._check_web_search()

    check = checker.results["checks"]["web_search"]
    assert check["status"] == "unhealthy"
    assert check["details"]["blocking"] is True
    assert any(item["component"] == "web_search" for item in checker.results["action_items"])


@pytest.mark.asyncio
async def test_flight_check_marks_web_search_healthy_with_tavily_key():
    """Flight check should report healthy when Tavily key exists."""
    settings.tavily_api_key = "tvly-test-key"
    settings.serpapi_key = ""

    checker = FlightCheck()
    await checker._check_web_search()

    check = checker.results["checks"]["web_search"]
    assert check["status"] == "healthy"
    assert check["details"]["blocking"] is False


@pytest.mark.asyncio
async def test_web_scraper_returns_missing_key_error_dict():
    """WebScraperService.search returns structured error when no key is configured."""
    settings.tavily_api_key = ""
    settings.serpapi_key = ""
    scraper = WebScraperService()
    try:
        result = await scraper.search("pottery suppliers Jaipur", region="in", num_results=3)
        assert isinstance(result, dict)
        assert result["error"] == "missing_api_key"
        assert result["action_required"] is True
    finally:
        if scraper.session:
            await scraper.session.close()


@pytest.mark.asyncio
async def test_supply_hunter_propagates_missing_key_error():
    """Supply Hunter should stop early and return the same missing_api_key error."""
    settings.tavily_api_key = ""
    settings.serpapi_key = ""
    scraper = WebScraperService()
    try:
        agent = SupplyHunterAgent(_DummyLLM(), _DummyVectorStore(), scraper)
        result = await agent.analyze(
            {
                "craft_type": "pottery",
                "supplies_needed": ["clay"],
                "location": {"city": "Jaipur", "state": "Rajasthan"},
            }
        )

        assert result["total_suppliers_found"] == 0
        assert result["error"]["error"] == "missing_api_key"
        assert result["error"]["action_required"] is True
    finally:
        if scraper.session:
            await scraper.session.close()
