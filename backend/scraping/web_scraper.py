"""
Web scraping service using Tavily API + Playwright + BeautifulSoup
CRITICAL REQUIREMENTS:
- MUST use real web search (Tavily)
- MUST scrape actual live data
- NO synthetic data
- NO database lookups
- Full audit logs required
"""
from typing import Dict, List, Optional
import aiohttp
import asyncio
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from loguru import logger
from backend.config import settings
from backend.constants import (
    TAVILY_API_TIMEOUT,
    SCRAPING_TIMEOUT,
    PLAYWRIGHT_TIMEOUT,
    PLAYWRIGHT_WAIT_TIMEOUT,
    SCRAPER_SNIPPET_LENGTH,
    SCRAPER_PAGE_CONTENT_LIMIT,
    SCRAPER_USER_AGENT,
    REGION_MAPPING
)
from datetime import datetime
import json

# Import WebSocket broadcaster (optional)
try:
    from backend.api.websocket import broadcast_search_results, manager
    HAS_WEBSOCKET = True
except ImportError:
    logger.debug("WebSocket module not available - real-time updates disabled")
    HAS_WEBSOCKET = False


class WebScraperService:
    """
    Web scraping service using Tavily API + Playwright + BeautifulSoup
    """
    
    def __init__(self):
        self.tavily_api_key = settings.tavily_api_key
        self.serpapi_key = settings.serpapi_key  # Fallback
        if not self.tavily_api_key and not self.serpapi_key:
            logger.warning("TAVILY_API_KEY not set - web search will be limited")
        
        self.session: Optional[aiohttp.ClientSession] = None
        self.search_logs: List[Dict] = []
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def search(
        self,
        query: str,
        region: str = "in",
        num_results: int = 10
    ) -> List[Dict]:
        """
        Search web using Tavily API
        
        Args:
            query: Search query
            region: Region code (in=India, us=USA, etc.) - used for context
            num_results: Number of results to return
        
        Returns:
            List of search results
        """
        # Prefer Tavily, fallback to SerpAPI if available
        if self.tavily_api_key:
            return await self._search_tavily(query, num_results)
        elif self.serpapi_key:
            return await self._search_serpapi(query, region, num_results)
        else:
            logger.error("Cannot search: No API key configured (need TAVILY_API_KEY or SERPAPI_KEY)")
            return []
    
    async def _search_tavily(
        self,
        query: str,
        num_results: int = 10
    ) -> List[Dict]:
        """Search using Tavily API"""
        logger.info(f"Searching with Tavily: '{query}' (n={num_results})")
        
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        try:
            url = "https://api.tavily.com/search"
            headers = {
                "Content-Type": "application/json"
            }
            payload = {
                "api_key": self.tavily_api_key,
                "query": query,
                "search_depth": "basic",
                "max_results": num_results,
                "include_answer": False,
                "include_raw_content": False
            }
            
            async with self.session.post(url, json=payload, headers=headers, timeout=TAVILY_API_TIMEOUT) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Tavily API error: {response.status} - {error_text}")
                    return []
                
                data = await response.json()
                
                # Extract results
                results = data.get("results", [])
                
                # Format results
                formatted_results = []
                for result in results:
                    formatted_results.append({
                        "title": result.get("title", ""),
                        "url": result.get("url", ""),
                        "snippet": result.get("content", "")[:SCRAPER_SNIPPET_LENGTH],
                        "position": len(formatted_results) + 1
                    })
                
                # Log search
                log_entry = {
                    "query": query,
                    "results_count": len(formatted_results),
                    "timestamp": self._get_timestamp(),
                    "provider": "tavily"
                }
                self.search_logs.append(log_entry)

                # Broadcast via WebSocket if available
                if HAS_WEBSOCKET:
                    try:
                        await manager.broadcast({
                            "type": "search_progress",
                            "query": query,
                            "url": f"Searching: {query}",
                            "status": "complete",
                            "results_count": len(formatted_results),
                            "timestamp": log_entry["timestamp"]
                        })
                    except (RuntimeError, AttributeError) as e:
                        logger.debug(f"WebSocket broadcast failed (non-critical): {type(e).__name__}: {e}")

                logger.success(f"Found {len(formatted_results)} results via Tavily")
                return formatted_results

        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as e:
            logger.error(f"Tavily search error: {type(e).__name__}: {e}")
            return []
    
    async def _search_serpapi(
        self,
        query: str,
        region: str = "in",
        num_results: int = 10
    ) -> List[Dict]:
        """Fallback: Search using SerpAPI"""
        logger.info(f"Searching with SerpAPI: '{query}' (region={region}, n={num_results})")
        
        url = "https://serpapi.com/search"
        params = {
            "q": query,
            "location": self._get_location_string(region),
            "hl": "en",
            "gl": region,
            "api_key": self.serpapi_key,
            "num": num_results
        }
        
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        try:
            async with self.session.get(url, params=params, timeout=TAVILY_API_TIMEOUT) as response:
                if response.status != 200:
                    logger.error(f"SerpAPI error: {response.status}")
                    return []
                
                data = await response.json()
                
                # Extract organic results
                results = data.get("organic_results", [])
                
                # Format results
                formatted_results = []
                for result in results:
                    formatted_results.append({
                        "title": result.get("title", ""),
                        "url": result.get("link", ""),
                        "snippet": result.get("snippet", ""),
                        "position": result.get("position", 0)
                    })
                
                # Log search
                log_entry = {
                    "query": query,
                    "region": region,
                    "results_count": len(formatted_results),
                    "timestamp": self._get_timestamp(),
                    "provider": "serpapi"
                }
                self.search_logs.append(log_entry)

                # Broadcast via WebSocket if available
                if HAS_WEBSOCKET:
                    try:
                        await manager.broadcast({
                            "type": "search_progress",
                            "query": query,
                            "url": f"Searching: {query}",
                            "status": "complete",
                            "results_count": len(formatted_results),
                            "timestamp": log_entry["timestamp"]
                        })
                    except (RuntimeError, AttributeError) as e:
                        logger.debug(f"WebSocket broadcast failed (non-critical): {type(e).__name__}: {e}")

                logger.success(f"Found {len(formatted_results)} results via SerpAPI")
                return formatted_results

        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.error(f"SerpAPI search error: {type(e).__name__}: {e}")
            return []
    
    async def scrape_page(self, url: str, use_playwright: bool = False) -> str:
        """
        Scrape a webpage and broadcast progress
        
        Args:
            url: URL to scrape
            use_playwright: Use Playwright for dynamic content (slower but handles JS)
        
        Returns:
            Page text content
        """
        # Broadcast scraping start
        if HAS_WEBSOCKET:
            try:
                manager.broadcast({
                    "type": "scraping_progress",
                    "url": url,
                    "status": "scraping",
                    "method": "playwright" if use_playwright else "beautifulsoup"
                })
            except (RuntimeError, AttributeError) as e:
                logger.debug(f"WebSocket broadcast failed (non-critical): {type(e).__name__}: {e}")
        logger.info(f"Scraping: {url} (playwright={use_playwright})")
        
        try:
            if use_playwright:
                return await self._scrape_with_playwright(url)
            else:
                return await self._scrape_with_beautifulsoup(url)
        except (aiohttp.ClientError, asyncio.TimeoutError, RuntimeError) as e:
            logger.error(f"Scraping error for {url}: {type(e).__name__}: {e}")
            return ""
    
    async def _scrape_with_beautifulsoup(self, url: str) -> str:
        """Scrape using BeautifulSoup (fast, static content)"""
        if not self.session:
            self.session = aiohttp.ClientSession()

        headers = {
            "User-Agent": SCRAPER_USER_AGENT
        }

        async with self.session.get(url, headers=headers, timeout=SCRAPING_TIMEOUT) as response:
            if response.status != 200:
                return ""
            
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text
            text = soup.get_text()
            
            # Clean up
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)

            return text[:SCRAPER_PAGE_CONTENT_LIMIT]
    
    async def _scrape_with_playwright(self, url: str) -> str:
        """Scrape using Playwright (slow, handles dynamic content)"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.goto(url, wait_until="networkidle", timeout=PLAYWRIGHT_TIMEOUT)

                # Wait for content to load
                await page.wait_for_timeout(PLAYWRIGHT_WAIT_TIMEOUT)

                # Get text content
                text = await page.evaluate("() => document.body.innerText")

                await browser.close()

                return text[:SCRAPER_PAGE_CONTENT_LIMIT]
            except (RuntimeError, asyncio.TimeoutError) as e:
                logger.error(f"Playwright navigation error for {url}: {type(e).__name__}: {e}")
                await browser.close()
                raise RuntimeError(f"Failed to scrape {url} with Playwright") from e
    
    def _get_location_string(self, region_code: str) -> str:
        """Get location string for SerpAPI"""
        return REGION_MAPPING.get(region_code, "India")
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        return datetime.now().isoformat()
    
    def get_search_logs(self) -> List[Dict]:
        """Get all search logs"""
        return self.search_logs


# Test the scraper
async def test_scraper():
    scraper = WebScraperService()
    
    # Test search
    print("Testing web search...")
    results = await scraper.search("pottery clay suppliers Jaipur India", region="in", num_results=3)
    
    for i, result in enumerate(results):
        print(f"\n--- Result {i+1} ---")
        print(f"Title: {result['title']}")
        print(f"URL: {result['url']}")
        print(f"Snippet: {result['snippet'][:100]}...")
    
    # Test scraping (if results found)
    if results:
        print("\n\nTesting page scraping...")
        url = results[0]['url']
        content = await scraper.scrape_page(url)
        print(f"Scraped {len(content)} characters from {url}")
        print(f"First 200 chars: {content[:200]}...")


if __name__ == "__main__":
    import asyncio
    
    # You need to set SERPAPI_KEY environment variable
    # Get free key from: https://serpapi.com/
    
    asyncio.run(test_scraper())
