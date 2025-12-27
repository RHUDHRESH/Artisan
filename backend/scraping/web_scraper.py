"""
Web scraping service using Tavily API + Playwright + BeautifulSoup
CRITICAL REQUIREMENTS:
- MUST use real web search (Tavily)
- MUST scrape actual live data
- NO synthetic data
- NO database lookups
- Full audit logs required
"""
from typing import Any, Dict, List, Optional, Union
import aiohttp
import asyncio
import random
import time
import hashlib
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from loguru import logger
from backend.config import settings
from backend.constants import (
    TAVILY_API_TIMEOUT,
    SERPAPI_TIMEOUT,
    SCRAPING_TIMEOUT,
    PLAYWRIGHT_TIMEOUT,
    PLAYWRIGHT_WAIT_TIMEOUT,
    SCRAPER_SNIPPET_LENGTH,
    SCRAPER_PAGE_CONTENT_LIMIT,
    SCRAPER_USER_AGENT,
    REGION_MAPPING,
    MAX_CONCURRENT_SCRAPING_TASKS,
    MAX_CONCURRENT_API_CALLS,
    WORKER_TIMEOUT,
    CACHE_EXPIRY_SECONDS,
    CACHE_DIR
)
from datetime import datetime, timedelta
import json
import os
from dataclasses import dataclass
from enum import Enum
import urllib.parse
from functools import wraps

# Import WebSocket broadcaster (optional)
try:
    from backend.api.websocket import broadcast_search_results, manager
    HAS_WEBSOCKET = True
except ImportError:
    logger.debug("WebSocket module not available - real-time updates disabled")
    HAS_WEBSOCKET = False


# Enhanced scraping configuration
@dataclass
class ScrapingConfig:
    max_retries: int = 3
    retry_delay_base: float = 1.0
    retry_delay_max: float = 10.0
    rate_limit_delay: float = 0.5
    timeout_multiplier: float = 1.5
    max_concurrent_requests: int = MAX_CONCURRENT_SCRAPING_TASKS
    cache_enabled: bool = True
    proxy_rotation_enabled: bool = False
    user_agent_rotation_enabled: bool = True


class ScrapingError(Enum):
    TIMEOUT = "timeout"
    HTTP_ERROR = "http_error"
    CONNECTION_ERROR = "connection_error"
    RATE_LIMITED = "rate_limited"
    BLOCKED = "blocked"
    CONTENT_ERROR = "content_error"
    PARSE_ERROR = "parse_error"
    UNKNOWN = "unknown"


@dataclass
class ProxyConfig:
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    proxy_type: str = "http"  # http, https, socks5


# User agent rotation pool
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15"
]


# Proxy pool (placeholder - would be populated from config or service)
PROXY_POOL: List[ProxyConfig] = []


def retry_on_failure(max_retries: int = 3, delay_base: float = 1.0, exceptions: tuple = (Exception,)):
    """Decorator for retrying failed operations with exponential backoff"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_retries:
                        logger.error(f"Failed after {max_retries + 1} attempts: {func.__name__} - {str(e)}")
                        raise
                    
                    delay = min(delay_base * (2 ** attempt), delay_base * 10)
                    logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}. Retrying in {delay:.2f}s...")
                    await asyncio.sleep(delay)
            
            raise last_exception
        return wrapper
    return decorator


class RateLimiter:
    """Simple rate limiter for requests"""
    def __init__(self, delay: float = 0.5):
        self.delay = delay
        self.last_request_time = 0
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        async with self._lock:
            now = time.time()
            time_since_last = now - self.last_request_time
            if time_since_last < self.delay:
                await asyncio.sleep(self.delay - time_since_last)
            self.last_request_time = time.time()


class SimpleCache:
    """Simple in-memory cache with TTL"""
    def __init__(self, default_ttl: int = CACHE_EXPIRY_SECONDS):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
        self._lock = asyncio.Lock()
    
    def _generate_key(self, url: str, method: str = "GET", **kwargs) -> str:
        """Generate cache key from URL and parameters"""
        key_data = f"{url}:{method}:{json.dumps(kwargs, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def get(self, key: str) -> Optional[Any]:
        async with self._lock:
            if key in self.cache:
                entry = self.cache[key]
                if datetime.fromisoformat(entry["expires_at"]) > datetime.now():
                    return entry["data"]
                else:
                    del self.cache[key]
        return None
    
    async def set(self, key: str, data: Any, ttl: Optional[int] = None) -> None:
        async with self._lock:
            ttl = ttl or self.default_ttl
            expires_at = (datetime.now() + timedelta(seconds=ttl)).isoformat()
            self.cache[key] = {
                "data": data,
                "created_at": datetime.now().isoformat(),
                "expires_at": expires_at
            }
    
    async def clear_expired(self) -> int:
        async with self._lock:
            expired_keys = []
            now = datetime.now()
            for key, entry in self.cache.items():
                if datetime.fromisoformat(entry["expires_at"]) <= now:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.cache[key]
            
            return len(expired_keys)


SearchResult = Union[List[Dict[str, Any]], Dict[str, Any]]


class WebScraperService:
    """
    Enhanced web scraping service with robust error handling, rate limiting,
    proxy rotation, caching, and anti-bot detection bypass
    """
    
    def __init__(self, config: Optional[ScrapingConfig] = None):
        self.config = config or ScrapingConfig()
        self.tavily_api_key = settings.tavily_api_key
        self.serpapi_key = settings.serpapi_key  # Fallback
        
        if not self.tavily_api_key and not self.serpapi_key:
            logger.warning("TAVILY_API_KEY not set - web search will be limited")
        
        self.session: Optional[aiohttp.ClientSession] = None
        self.search_logs: List[Dict] = []
        self.rate_limiter = RateLimiter(self.config.rate_limit_delay)
        self.cache = SimpleCache()
        self.user_agent_index = 0
        self.proxy_index = 0
        self._concurrent_requests = 0
        self._request_lock = asyncio.Lock()
    
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
        num_results: int = 10,
        sources: List[str] = None,
        deep_search: bool = False
    ) -> SearchResult:
        """
        Enhanced search using multiple engines with failover, rate limiting, and caching

        Args:
            query: Search query
            region: Region code (in=India, us=USA, etc.)
            num_results: Number of results to return
            sources: List of search sources to try ['tavily', 'serpapi', 'local']
            deep_search: Whether to do exhaustive search across multiple queries

        Returns:
            Enhanced list of search results with metadata
        """
        # Check cache first
        cache_key = self.cache._generate_key(query, "SEARCH", region=region, num_results=num_results, sources=sources, deep_search=deep_search)
        if self.config.cache_enabled:
            cached_result = await self.cache.get(cache_key)
            if cached_result:
                logger.info(f"Cache hit for search: {query[:50]}...")
                return cached_result
        
        # Rate limiting
        await self.rate_limiter.acquire()
        
        # Concurrent request limiting
        async with self._request_lock:
            if self._concurrent_requests >= self.config.max_concurrent_requests:
                logger.warning(f"Max concurrent requests ({self.config.max_concurrent_requests}) reached, waiting...")
                await asyncio.sleep(1.0)
            self._concurrent_requests += 1
        
        try:
            all_results = []
            search_metadata = {
                "query": query,
                "region": region,
                "requested_results": num_results,
                "sources_tried": [],
                "total_results": 0,
                "timestamp": self._get_timestamp(),
                "cache_hit": False
            }

            # Default sources if not specified
            if sources is None:
                sources = ['tavily', 'serpapi', 'local'] if deep_search else ['tavily', 'serpapi']

            # Generate multiple query variations for deeper search
            queries = [query]
            if deep_search:
                queries.extend(self._generate_query_variations(query, region))

            logger.info(f"Enhanced search: {query} ({len(queries)} queries, sources: {sources})")

            for search_query in queries:
                for source in sources:
                    if source == 'tavily' and self.tavily_api_key:
                        results = await self._search_tavily(search_query, num_results)
                        if not isinstance(results, dict) or not results.get("error"):
                            search_metadata["sources_tried"].append(f"tavily:{search_query}")
                            if isinstance(results, list):
                                all_results.extend(results)

                    elif source == 'serpapi' and self.serpapi_key:
                        results = await self._search_serpapi(search_query, region, num_results)
                        if not isinstance(results, dict) or not results.get("error"):
                            search_metadata["sources_tried"].append(f"serpapi:{search_query}")
                            if isinstance(results, list):
                                all_results.extend(results)

                    elif source == 'local':
                        results = await self._search_local_databases(search_query, region)
                        search_metadata["sources_tried"].append(f"local:{search_query}")
                        if isinstance(results, list):
                            all_results.extend(results)

                    # Stop if we have enough results
                    if len(all_results) >= num_results and not deep_search:
                        break
                if len(all_results) >= num_results and not deep_search:
                    break

            # Deduplicate and rank results
            unique_results = self._deduplicate_search_results(all_results)

            search_metadata["total_results"] = len(unique_results)
            search_metadata["effective_results"] = min(len(unique_results), num_results)

            # Limit results and add metadata
            final_results = unique_results[:num_results]
            for result in final_results:
                result["_search_metadata"] = search_metadata

            # Cache results
            if self.config.cache_enabled:
                await self.cache.set(cache_key, final_results, ttl=1800)  # 30 minutes cache

            logger.success(f"Enhanced search found {len(final_results)} results from {len(search_metadata['sources_tried'])} sources")
            return final_results
        
        finally:
            # Release concurrent request counter
            async with self._request_lock:
                self._concurrent_requests -= 1
    
    @retry_on_failure(max_retries=3, delay_base=1.0, exceptions=(aiohttp.ClientError, asyncio.TimeoutError, ValueError))
    async def _search_tavily(
        self,
        query: str,
        num_results: int = 10
    ) -> SearchResult:
        """Search using Tavily API with retry mechanism"""
        logger.info(f"Searching with Tavily: '{query}' (n={num_results})")
        
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        # Rate limiting
        await self.rate_limiter.acquire()
        
        url = "https://api.tavily.com/search"
        headers = {
            "Content-Type": "application/json",
            "User-Agent": self._get_random_user_agent()
        }
        payload = {
            "api_key": self.tavily_api_key,
            "query": query,
            "search_depth": "basic",
            "max_results": num_results,
            "include_answer": False,
            "include_raw_content": False
        }
        
        timeout = aiohttp.ClientTimeout(total=TAVILY_API_TIMEOUT * self.config.timeout_multiplier)
        
        async with self.session.post(url, json=payload, headers=headers, timeout=timeout) as response:
            if response.status != 200:
                error_text = await response.text()
                logger.error(f"Tavily API error: {response.status} - {error_text}")
                failure = {
                    "error": "tavily_http_error",
                    "message": f"Tavily returned HTTP {response.status}",
                    "provider": "tavily",
                    "action_required": False,
                    "details": {"status": response.status, "body": error_text[:200]},
                }
                self._log_search_error(query, "tavily", failure)
                return failure

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
                    "position": len(formatted_results) + 1,
                    "source": "tavily",
                    "timestamp": self._get_timestamp()
                })

            # Log search
            self._log_search_success(query, "tavily", len(formatted_results))

            # Broadcast via WebSocket if available
            if HAS_WEBSOCKET:
                try:
                    await manager.broadcast({
                        "type": "search_progress",
                        "query": query,
                        "url": f"Searching: {query}",
                        "status": "complete",
                        "results_count": len(formatted_results),
                        "provider": "tavily",
                        "timestamp": self._get_timestamp()
                    })
                except (RuntimeError, AttributeError) as e:
                    logger.debug(f"WebSocket broadcast failed (non-critical): {type(e).__name__}: {e}")

            logger.success(f"Found {len(formatted_results)} results via Tavily")
            return formatted_results
    
    @retry_on_failure(max_retries=3, delay_base=1.0, exceptions=(aiohttp.ClientError, asyncio.TimeoutError))
    async def _search_serpapi(
        self,
        query: str,
        region: str = "in",
        num_results: int = 10
    ) -> SearchResult:
        """Fallback: Search using SerpAPI with retry mechanism"""
        logger.info(f"Searching with SerpAPI: '{query}' (region={region}, n={num_results})")
        
        # Rate limiting
        await self.rate_limiter.acquire()
        
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
        
        timeout = aiohttp.ClientTimeout(total=SERPAPI_TIMEOUT * self.config.timeout_multiplier)
        
        async with self.session.get(url, params=params, timeout=timeout) as response:
            if response.status != 200:
                logger.error(f"SerpAPI error: {response.status}")
                failure = {
                    "error": "serpapi_http_error",
                    "message": f"SerpAPI returned HTTP {response.status}",
                    "provider": "serpapi",
                    "action_required": False,
                    "details": {"status": response.status},
                }
                self._log_search_error(query, "serpapi", failure, region=region)
                return failure

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
                    "position": result.get("position", 0),
                    "source": "serpapi",
                    "timestamp": self._get_timestamp()
                })

            # Log search
            self._log_search_success(query, "serpapi", len(formatted_results), region=region)

            # Broadcast via WebSocket if available
            if HAS_WEBSOCKET:
                try:
                    await manager.broadcast({
                        "type": "search_progress",
                        "query": query,
                        "url": f"Searching: {query}",
                        "status": "complete",
                        "results_count": len(formatted_results),
                        "provider": "serpapi",
                        "timestamp": self._get_timestamp()
                    })
                except (RuntimeError, AttributeError) as e:
                    logger.debug(f"WebSocket broadcast failed (non-critical): {type(e).__name__}: {e}")

            logger.success(f"Found {len(formatted_results)} results via SerpAPI")
            return formatted_results
    
    async def scrape_page(self, url: str, use_playwright: bool = False, cache_ttl: int = 3600) -> str:
        """
        Enhanced page scraping with caching, rate limiting, and error handling
        
        Args:
            url: URL to scrape
            use_playwright: Use Playwright for dynamic content (slower but handles JS)
            cache_ttl: Cache time-to-live in seconds
        
        Returns:
            Page text content
        """
        # Check cache first
        cache_key = self.cache._generate_key(url, "SCRAPE", use_playwright=use_playwright)
        if self.config.cache_enabled:
            cached_content = await self.cache.get(cache_key)
            if cached_content:
                logger.info(f"Cache hit for scraping: {url[:50]}...")
                return cached_content
        
        # Rate limiting
        await self.rate_limiter.acquire()
        
        # Broadcast scraping start
        if HAS_WEBSOCKET:
            try:
                await manager.broadcast({
                    "type": "scraping_progress",
                    "url": url,
                    "status": "scraping",
                    "method": "playwright" if use_playwright else "beautifulsoup"
                })
            except (RuntimeError, AttributeError) as e:
                logger.debug(f"WebSocket broadcast failed (non-critical): {type(e).__name__}: {e}")
        
        logger.info(f"Scraping: {url} (playwright={use_playwright})")
        
        try:
            content = ""
            if use_playwright:
                content = await self._scrape_with_playwright(url)
            else:
                content = await self._scrape_with_beautifulsoup(url)
            
            # Cache the result
            if self.config.cache_enabled and content:
                await self.cache.set(cache_key, content, ttl=cache_ttl)
            
            return content
            
        except (aiohttp.ClientError, asyncio.TimeoutError, RuntimeError) as e:
            logger.error(f"Scraping error for {url}: {type(e).__name__}: {e}")
            return ""
    
    @retry_on_failure(max_retries=3, delay_base=1.0, exceptions=(aiohttp.ClientError, asyncio.TimeoutError))
    async def _scrape_with_beautifulsoup(self, url: str) -> str:
        """Enhanced BeautifulSoup scraping with anti-bot detection"""
        if not self.session:
            self.session = aiohttp.ClientSession()

        headers = {
            "User-Agent": self._get_random_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        
        timeout = aiohttp.ClientTimeout(total=SCRAPING_TIMEOUT * self.config.timeout_multiplier)
        
        async with self.session.get(url, headers=headers, timeout=timeout) as response:
            if response.status != 200:
                logger.warning(f"HTTP {response.status} for {url}")
                return ""
            
            # Check for bot detection indicators
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' not in content_type:
                logger.warning(f"Unexpected content type {content_type} for {url}")
                return ""
            
            html = await response.text()
            
            # Check for common bot detection pages
            bot_indicators = [
                'access denied', 'bot detection', 'captcha', 'security check',
                'cloudflare', 'incident', 'rate limit', 'too many requests'
            ]
            html_lower = html.lower()
            if any(indicator in html_lower for indicator in bot_indicators):
                logger.warning(f"Bot detection triggered for {url}")
                return ""
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                element.decompose()
            
            # Try to find main content areas
            main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=lambda x: x and ('content' in x.lower() or 'main' in x.lower()))
            
            if main_content:
                text = main_content.get_text()
            else:
                # Fallback to body text
                text = soup.get_text()
            
            # Enhanced text cleaning
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Remove excessive whitespace
            import re
            text = re.sub(r'\s+', ' ', text).strip()
            
            return text[:SCRAPER_PAGE_CONTENT_LIMIT]
    
    @retry_on_failure(max_retries=2, delay_base=2.0, exceptions=(RuntimeError, asyncio.TimeoutError))
    async def _scrape_with_playwright(self, url: str) -> str:
        """Enhanced Playwright scraping with stealth capabilities"""
        async with async_playwright() as p:
            # Launch with stealth options
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--single-process',
                    '--disable-gpu'
                ]
            )
            
            context = await browser.new_context(
                user_agent=self._get_random_user_agent(),
                viewport={'width': 1920, 'height': 1080},
                locale='en-US'
            )
            
            page = await context.new_page()
            
            try:
                # Set additional headers to look more human
                await page.set_extra_http_headers({
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache'
                })
                
                # Navigate with extended timeout
                await page.goto(url, wait_until="networkidle", timeout=PLAYWRIGHT_TIMEOUT * self.config.timeout_multiplier)
                
                # Wait a bit for dynamic content
                await page.wait_for_timeout(PLAYWRIGHT_WAIT_TIMEOUT)
                
                # Check for bot detection
                page_content = await page.content()
                bot_indicators = [
                    'access denied', 'bot detection', 'captcha', 'security check',
                    'cloudflare', 'incident', 'rate limit', 'too many requests',
                    'checking your browser', 'enable javascript'
                ]
                
                if any(indicator in page_content.lower() for indicator in bot_indicators):
                    logger.warning(f"Bot detection triggered for {url} (Playwright)")
                    await browser.close()
                    return ""
                
                # Try to get text content from main elements first
                try:
                    main_text = await page.evaluate('''() => {
                        const main = document.querySelector('main') || 
                                     document.querySelector('article') ||
                                     document.querySelector('[role="main"]') ||
                                     document.querySelector('.content') ||
                                     document.querySelector('#content');
                        return main ? main.innerText : document.body.innerText;
                    }''')
                except:
                    # Fallback to basic text extraction
                    main_text = await page.evaluate("() => document.body.innerText")
                
                await browser.close()
                
                # Clean up the text
                if main_text:
                    import re
                    text = re.sub(r'\s+', ' ', main_text).strip()
                    return text[:SCRAPER_PAGE_CONTENT_LIMIT]
                
                return ""
                
            except (RuntimeError, asyncio.TimeoutError) as e:
                logger.error(f"Playwright navigation error for {url}: {type(e).__name__}: {e}")
                await browser.close()
                raise RuntimeError(f"Failed to scrape {url} with Playwright") from e
    
    def _get_random_user_agent(self) -> str:
        """Get a random user agent from the pool"""
        if self.config.user_agent_rotation_enabled:
            agent = USER_AGENTS[self.user_agent_index % len(USER_AGENTS)]
            self.user_agent_index += 1
            return agent
        return SCRAPER_USER_AGENT
    
    def _get_proxy_config(self) -> Optional[ProxyConfig]:
        """Get next proxy from pool (placeholder for future implementation)"""
        if self.config.proxy_rotation_enabled and PROXY_POOL:
            proxy = PROXY_POOL[self.proxy_index % len(PROXY_POOL)]
            self.proxy_index += 1
            return proxy
        return None
    
    def _log_search_success(self, query: str, provider: str, results_count: int, **kwargs):
        """Log successful search"""
        log_entry = {
            "query": query,
            "results_count": results_count,
            "timestamp": self._get_timestamp(),
            "provider": provider,
            "status": "ok",
            **kwargs
        }
        self.search_logs.append(log_entry)
    
    def _log_search_error(self, query: str, provider: str, error_info: Dict, **kwargs):
        """Log search error"""
        log_entry = {
            "query": query,
            "results_count": 0,
            "timestamp": self._get_timestamp(),
            "provider": provider,
            "status": "error",
            "error": error_info.get("error"),
            "error_details": error_info,
            **kwargs
        }
        self.search_logs.append(log_entry)
    
    def _generate_query_variations(self, query: str, region: str) -> List[str]:
        """Generate multiple query variations for comprehensive search"""
        variations = []

        # Add region-specific variations
        region_names = {
            "in": ["India", "Indian", "Hindustan"],
            "us": ["USA", "United States", "American"],
            "uk": ["UK", "United Kingdom", "Britain"],
            "de": ["Germany", "German"],
            "jp": ["Japan", "Japanese"]
        }

        region_terms = region_names.get(region, [region.upper()])

        # Basic variations
        for term in region_terms[:2]:  # Limit to avoid too many
            variations.extend([
                f"{query} {term}",
                f"{query} in {term}",
                f"best {query} {term}",
                f"{query} suppliers {term}",
                f"buy {query} {term}"
            ])

        # Add industry-specific variations
        industry_terms = ["wholesale", "manufacturers", "distributors", "suppliers", "vendors"]
        for term in industry_terms[:3]:
            variations.append(f"{query} {term}")

        # Add platform variations for marketplaces
        platform_terms = ["Etsy", "Amazon", "Flipkart", "Shopify", "marketplace"]
        for platform in platform_terms[:2]:
            variations.append(f"{query} on {platform}")

        # Limit variations to avoid API limits
        return variations[:5]  # Return top 5 variations

    async def _search_local_databases(self, query: str, region: str) -> List[Dict]:
        """Search local knowledge base for relevant information"""
        local_results = []

        # This could be expanded to search local databases, caches, or pre-indexed content
        # For now, return empty - can be implemented later with actual local data
        # Could search: cached results, local business directories, pre-scraped data, etc.

        # Placeholder for future implementation
        logger.debug(f"Local database search not implemented yet for: {query}")
        return local_results

    def _deduplicate_search_results(self, results: List[Dict]) -> List[Dict]:
        """Remove duplicate search results based on URL similarity"""
        seen_urls = set()
        unique_results = []

        for result in results:
            url = result.get("url", "").lower().rstrip("/")

            # Normalize URL for deduplication
            if "http://" in url:
                url = url.replace("http://", "https://")
            if url.endswith("/"):
                url = url[:-1]

            # Remove common tracking parameters
            url = url.split('?')[0]
            url = url.split('#')[0]

            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)

        # Sort by relevance (position if available, else keep original order)
        unique_results.sort(key=lambda x: x.get("position", 999))

        return unique_results

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
