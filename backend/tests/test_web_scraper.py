"""
Comprehensive test suite for enhanced web scraper
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import aiohttp
from backend.scraping.web_scraper import (
    WebScraperService, 
    ScrapingConfig, 
    RateLimiter, 
    SimpleCache,
    ScrapingError,
    ProxyConfig
)


class TestWebScraperService:
    """Test suite for WebScraperService"""
    
    @pytest.fixture
    def scraper_config(self):
        """Test configuration"""
        return ScrapingConfig(
            max_retries=2,
            rate_limit_delay=0.1,
            cache_enabled=True,
            user_agent_rotation_enabled=True
        )
    
    @pytest.fixture
    def scraper(self, scraper_config):
        """Create scraper instance for testing"""
        return WebScraperService(config=scraper_config)
    
    @pytest.fixture
    def mock_session(self):
        """Mock aiohttp session"""
        session = AsyncMock()
        return session
    
    def test_scraper_initialization(self, scraper_config):
        """Test scraper initialization"""
        scraper = WebScraperService(config=scraper_config)
        
        assert scraper.config == scraper_config
        assert scraper.rate_limiter.delay == 0.1
        assert scraper.cache is not None
        assert scraper.user_agent_index == 0
    
    @pytest.mark.asyncio
    async def test_search_with_cache_hit(self, scraper):
        """Test search with cache hit"""
        # Mock cache hit
        cached_results = [{"title": "Cached Result", "url": "https://example.com"}]
        scraper.cache.set = AsyncMock()
        scraper.cache.get = AsyncMock(return_value=cached_results)
        
        result = await scraper.search("test query", region="in", num_results=5)
        
        assert result == cached_results
        scraper.cache.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_tavily_success(self, scraper, mock_session):
        """Test successful Tavily search"""
        # Mock successful API response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "results": [
                {"title": "Test Result", "url": "https://test.com", "content": "Test content"}
            ]
        })
        
        mock_session.post.return_value.__aenter__.return_value = mock_response
        scraper.session = mock_session
        
        with patch('aiohttp.ClientSession') as session_class:
            session_class.return_value = mock_session
            
            result = await scraper.search("test query", region="in", num_results=5)
            
            assert len(result) == 1
            assert result[0]["title"] == "Test Result"
            assert result[0]["source"] == "tavily"
    
    @pytest.mark.asyncio
    async def test_search_tavily_error(self, scraper, mock_session):
        """Test Tavily API error handling"""
        # Mock API error response
        mock_response = AsyncMock()
        mock_response.status = 429
        mock_response.text = AsyncMock(return_value="Rate limit exceeded")
        
        mock_session.post.return_value.__aenter__.return_value = mock_response
        scraper.session = mock_session
        
        with patch('aiohttp.ClientSession') as session_class:
            session_class.return_value = mock_session
            
            result = await scraper.search("test query", region="in", num_results=5)
            
            assert isinstance(result, dict)
            assert result["error"] == "tavily_http_error"
    
    @pytest.mark.asyncio
    async def test_scrape_page_beautifulsoup_success(self, scraper, mock_session):
        """Test successful BeautifulSoup scraping"""
        # Mock successful HTTP response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.headers = {"content-type": "text/html"}
        mock_response.text = AsyncMock(return_value="<html><body><h1>Test Content</h1></body></html>")
        
        mock_session.get.return_value.__aenter__.return_value = mock_response
        scraper.session = mock_session
        
        with patch('aiohttp.ClientSession') as session_class:
            session_class.return_value = mock_session
            
            result = await scraper.scrape_page("https://example.com")
            
            assert "Test Content" in result
    
    @pytest.mark.asyncio
    async def test_scrape_page_bot_detection(self, scraper, mock_session):
        """Test bot detection handling"""
        # Mock bot detection response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.headers = {"content-type": "text/html"}
        mock_response.text = AsyncMock(return_value="<html><body>Access denied - Bot detection</body></html>")
        
        mock_session.get.return_value.__aenter__.return_value = mock_response
        scraper.session = mock_session
        
        with patch('aiohttp.ClientSession') as session_class:
            session_class.return_value = mock_session
            
            result = await scraper.scrape_page("https://example.com")
            
            assert result == ""
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, scraper):
        """Test rate limiting functionality"""
        start_time = asyncio.get_event_loop().time()
        
        # Make multiple requests
        tasks = [scraper.search(f"test query {i}", region="in", num_results=1) for i in range(3)]
        
        # Mock cache miss and search to test rate limiting
        scraper.cache.get = AsyncMock(return_value=None)
        scraper._search_tavily = AsyncMock(return_value=[])
        
        await asyncio.gather(*tasks)
        
        end_time = asyncio.get_event_loop().time()
        elapsed = end_time - start_time
        
        # Should take at least 0.2 seconds due to rate limiting (0.1s delay between requests)
        assert elapsed >= 0.2
    
    def test_user_agent_rotation(self, scraper):
        """Test user agent rotation"""
        agents = set()
        for _ in range(10):
            agent = scraper._get_random_user_agent()
            agents.add(agent)
        
        # Should have multiple different user agents
        assert len(agents) > 1
    
    def test_deduplicate_results(self, scraper):
        """Test result deduplication"""
        results = [
            {"url": "https://example.com", "title": "Test 1"},
            {"url": "https://example.com/", "title": "Test 2"},  # Same URL with trailing slash
            {"url": "https://another.com", "title": "Test 3"},
            {"url": "https://another.com?param=1", "title": "Test 4"},  # Same URL with params
        ]
        
        unique = scraper._deduplicate_search_results(results)
        
        # Should deduplicate to 2 unique URLs
        assert len(unique) == 2
    
    @pytest.mark.asyncio
    async def test_cache_operations(self, scraper):
        """Test cache set/get operations"""
        key = "test_key"
        data = {"test": "data"}
        
        # Test set and get
        await scraper.cache.set(key, data, ttl=60)
        result = await scraper.cache.get(key)
        
        assert result == data
        
        # Test cache miss
        result = await scraper.cache.get("nonexistent_key")
        assert result is None


class TestRateLimiter:
    """Test suite for RateLimiter"""
    
    @pytest.fixture
    def limiter(self):
        return RateLimiter(delay=0.1)
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, limiter):
        """Test rate limiting delays"""
        start_time = asyncio.get_event_loop().time()
        
        # Acquire twice
        await limiter.acquire()
        await limiter.acquire()
        
        end_time = asyncio.get_event_loop().time()
        elapsed = end_time - start_time
        
        # Should take at least 0.1 seconds
        assert elapsed >= 0.1


class TestSimpleCache:
    """Test suite for SimpleCache"""
    
    @pytest.fixture
    def cache(self):
        return SimpleCache(default_ttl=1)  # 1 second TTL
    
    @pytest.mark.asyncio
    async def test_cache_set_get(self, cache):
        """Test basic cache operations"""
        key = "test_key"
        data = {"test": "data"}
        
        await cache.set(key, data)
        result = await cache.get(key)
        
        assert result == data
    
    @pytest.mark.asyncio
    async def test_cache_expiration(self, cache):
        """Test cache expiration"""
        key = "test_key"
        data = {"test": "data"}
        
        await cache.set(key, data, ttl=0.1)  # Very short TTL
        
        # Should be available immediately
        result = await cache.get(key)
        assert result == data
        
        # Wait for expiration
        await asyncio.sleep(0.2)
        
        # Should be expired
        result = await cache.get(key)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_cache_clear_expired(self, cache):
        """Test clearing expired entries"""
        # Add multiple entries with different TTLs
        await cache.set("key1", "data1", ttl=0.1)
        await cache.set("key2", "data2", ttl=1.0)
        
        # Wait for first entry to expire
        await asyncio.sleep(0.2)
        
        # Clear expired entries
        cleared_count = await cache.clear_expired()
        
        assert cleared_count == 1
        
        # Check remaining entries
        result1 = await cache.get("key1")
        result2 = await cache.get("key2")
        
        assert result1 is None  # Expired
        assert result2 == "data2"  # Still valid


class TestScrapingConfig:
    """Test suite for ScrapingConfig"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = ScrapingConfig()
        
        assert config.max_retries == 3
        assert config.rate_limit_delay == 0.5
        assert config.cache_enabled is True
        assert config.user_agent_rotation_enabled is True
    
    def test_custom_config(self):
        """Test custom configuration values"""
        config = ScrapingConfig(
            max_retries=5,
            rate_limit_delay=1.0,
            cache_enabled=False
        )
        
        assert config.max_retries == 5
        assert config.rate_limit_delay == 1.0
        assert config.cache_enabled is False


# Integration tests
@pytest.mark.asyncio
async def test_full_search_workflow():
    """Test complete search workflow with mocked dependencies"""
    config = ScrapingConfig(max_retries=2, cache_enabled=True)
    scraper = WebScraperService(config)
    
    # Mock all external dependencies
    with patch('aiohttp.ClientSession') as mock_session_class:
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "results": [
                {"title": "Integration Test", "url": "https://test.com", "content": "Test content"}
            ]
        })
        
        mock_session.post.return_value.__aenter__.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        # Mock scraping
        scraper._scrape_with_beautifulsoup = AsyncMock(return_value="Scraped content")
        
        # Perform search
        results = await scraper.search("integration test", region="in", num_results=5)
        
        assert len(results) == 1
        assert results[0]["title"] == "Integration Test"
        assert results[0]["source"] == "tavily"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
