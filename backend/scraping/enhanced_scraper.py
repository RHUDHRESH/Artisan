"""
Enhanced WebScraperService integration with all advanced features
Integrates distributed caching, content extraction, proxy management, and monitoring
"""
import asyncio
import aiohttp
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from loguru import logger

# Import all advanced components
from backend.scraping.advanced_cache import get_cache, AdvancedScrapingCache
from backend.scraping.content_extractor import get_content_extractor, extract_content_advanced
from backend.scraping.proxy_pool import SimpleProxyPool, ProxyConfig, ProxyType
from backend.scraping.cloudflare_bypass import get_anti_detection_manager, bypass_protection
from backend.scraping.adaptive_rate_limiter import get_smart_rate_limiter, rate_limited_request
from backend.scraping.health_monitor import get_health_monitor, start_health_monitoring
from backend.scraping.dashboard import get_dashboard, start_dashboard
from backend.scraping.scraper_monitor import get_monitor, record_scraping_metrics
from backend.config import settings


class EnhancedWebScraperService:
    """Enhanced web scraper with all advanced features integrated"""
    
    def __init__(self, cache_type: str = "hybrid", enable_monitoring: bool = True):
        # Initialize advanced components
        self.cache = get_cache(cache_type)
        self.content_extractor = get_content_extractor()
        self.anti_detection = get_anti_detection_manager()
        self.rate_limiter = get_smart_rate_limiter()
        self.health_monitor = get_health_monitor()
        self.dashboard = get_dashboard()
        self.monitor = get_monitor()
        
        # Proxy pool
        self.proxy_pool = SimpleProxyPool()
        self._setup_proxies()
        
        # Session management
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Monitoring and analytics
        self.enable_monitoring = enable_monitoring
        
        logger.info("Enhanced WebScraperService initialized with all advanced features")
    
    def _setup_proxies(self):
        """Setup proxy pool from environment or config"""
        # Load proxies from environment
        added = self.proxy_pool.load_proxies_from_env()
        if added == 0:
            logger.info("No proxies found in environment, running without proxies")
    
    async def initialize(self):
        """Initialize the scraper service"""
        # Create HTTP session
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout)
        
        # Start monitoring if enabled
        if self.enable_monitoring:
            await start_health_monitoring()
            await start_dashboard()
        
        logger.info("Enhanced WebScraperService initialization complete")
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
        
        await self.cache.close()
        logger.info("Enhanced WebScraperService cleanup complete")
    
    async def search(self, query: str, region: str = "in", num_results: int = 10,
                    sources: List[str] = None, deep_search: bool = False) -> Dict[str, Any]:
        """Enhanced search with all advanced features"""
        start_time = datetime.now()
        domain = "search_api"
        
        try:
            # Check cache first
            cache_key = f"search:{query}:{region}:{num_results}"
            cached_results = await self.cache.get_search_results(query, region, num_results, sources or [], deep_search)
            
            if cached_results:
                logger.info(f"Search cache hit for query: {query}")
                record_scraping_metrics(True, 0.1, "cache", cache_hit=True)
                return cached_results
            
            # Use rate-limited request
            result = await rate_limited_request(
                domain=domain,
                request_func=self._perform_search,
                query=query,
                region=region,
                num_results=num_results,
                sources=sources,
                deep_search=deep_search
            )
            
            # Cache the results
            if result:
                await self.cache.set_search_results(query, region, num_results, sources or [], deep_search, result, ttl=1800)
            
            # Record metrics
            response_time = (datetime.now() - start_time).total_seconds()
            record_scraping_metrics(bool(result), response_time, "tavily")
            
            return result or {"results": [], "error": "Search failed"}
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            response_time = (datetime.now() - start_time).total_seconds()
            record_scraping_metrics(False, response_time, "tavily", error_type=str(e))
            return {"results": [], "error": str(e)}
    
    async def _perform_search(self, query: str, region: str, num_results: int,
                            sources: List[str], deep_search: bool) -> Optional[Dict[str, Any]]:
        """Perform actual search using Tavily API"""
        if not settings.tavily_api_key:
            logger.error("Tavily API key not configured")
            return None
        
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": settings.tavily_api_key,
            "query": query,
            "search_depth": "advanced" if deep_search else "basic",
            "include_answer": True,
            "include_raw_content": True,
            "max_results": num_results,
            "include_domains": sources if sources else None
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        try:
            async with self.session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._format_search_results(data)
                else:
                    logger.error(f"Tavily API error: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Tavily request error: {e}")
            return None
    
    def _format_search_results(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format search results"""
        results = []
        
        for item in data.get("results", []):
            result = {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "snippet": item.get("content", "")[:200],
                "published_date": item.get("published_date"),
                "score": item.get("score", 0.0)
            }
            results.append(result)
        
        return {
            "results": results,
            "answer": data.get("answer", ""),
            "total": len(results)
        }
    
    async def scrape_page(self, url: str, use_playwright: bool = False) -> Dict[str, Any]:
        """Enhanced page scraping with all advanced features"""
        start_time = datetime.now()
        domain = url.split('/')[2] if '/' in url else 'unknown'
        
        try:
            # Check cache first
            cached_content = await self.cache.get_page_content(url, use_playwright)
            if cached_content:
                logger.info(f"Page cache hit for: {url}")
                record_scraping_metrics(True, 0.1, "cache", cache_hit=True)
                return {"content": cached_content, "cached": True}
            
            # Use anti-detection bypass
            content = await bypass_protection(url, self.session)
            
            if not content:
                # Fallback to regular request
                content = await self._regular_scrape(url)
            
            if content:
                # Extract structured content
                extracted_data = await extract_content_advanced(content, url)
                
                # Cache the content
                await self.cache.set_page_content(url, content, use_playwright, ttl=3600)
                
                # Cache extracted data
                if extracted_data:
                    await self.cache.set_extracted_data(url, "main", extracted_data, ttl=7200)
                
                # Record metrics
                response_time = (datetime.now() - start_time).total_seconds()
                record_scraping_metrics(True, response_time, domain)
                
                return {
                    "content": content,
                    "extracted_data": extracted_data,
                    "cached": False
                }
            else:
                logger.error(f"Failed to scrape: {url}")
                response_time = (datetime.now() - start_time).total_seconds()
                record_scraping_metrics(False, response_time, domain, error_type="scrape_failed")
                return {"content": "", "error": "Failed to scrape page"}
                
        except Exception as e:
            logger.error(f"Scrape error for {url}: {e}")
            response_time = (datetime.now() - start_time).total_seconds()
            record_scraping_metrics(False, response_time, domain, error_type=str(e))
            return {"content": "", "error": str(e)}
    
    async def _regular_scrape(self, url: str) -> Optional[str]:
        """Regular scraping fallback"""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.warning(f"HTTP {response.status} for {url}")
                    return None
        except Exception as e:
            logger.error(f"Regular scrape error for {url}: {e}")
            return None
    
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        return self.dashboard.get_dashboard_data()
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get health monitoring status"""
        return self.health_monitor.get_health_summary()
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return self.monitor.get_metrics_summary()
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return await self.cache.get_cache_stats()
    
    def get_proxy_stats(self) -> Dict[str, Any]:
        """Get proxy pool statistics"""
        if not self.proxy_pool.proxies:
            return {"total_proxies": 0, "healthy_proxies": 0}
        
        healthy = sum(1 for p in self.proxy_pool.proxies if p.is_healthy)
        return {
            "total_proxies": len(self.proxy_pool.proxies),
            "healthy_proxies": healthy,
            "health_rate": (healthy / len(self.proxy_pool.proxies) * 100) if self.proxy_pool.proxies else 0
        }


# Global enhanced scraper instance
_global_enhanced_scraper: Optional[EnhancedWebScraperService] = None


def get_enhanced_scraper(cache_type: str = "hybrid", enable_monitoring: bool = True) -> EnhancedWebScraperService:
    """Get global enhanced scraper instance"""
    global _global_enhanced_scraper
    if _global_enhanced_scraper is None:
        _global_enhanced_scraper = EnhancedWebScraperService(cache_type, enable_monitoring)
    return _global_enhanced_scraper


async def initialize_enhanced_scraper():
    """Initialize the enhanced scraper"""
    scraper = get_enhanced_scraper()
    await scraper.initialize()


async def cleanup_enhanced_scraper():
    """Cleanup the enhanced scraper"""
    scraper = get_enhanced_scraper()
    await scraper.cleanup()


# Convenience functions for backward compatibility
async def enhanced_search(query: str, **kwargs) -> Dict[str, Any]:
    """Enhanced search function"""
    scraper = get_enhanced_scraper()
    return await scraper.search(query, **kwargs)


async def enhanced_scrape_page(url: str, **kwargs) -> Dict[str, Any]:
    """Enhanced page scraping function"""
    scraper = get_enhanced_scraper()
    return await scraper.scrape_page(url, **kwargs)
