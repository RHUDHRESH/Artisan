"""
Search Engine - SerpAPI wrapper for web search
"""
from typing import Any, Dict, List, Union
import aiohttp
import os
from loguru import logger
from datetime import datetime
# Try to import settings, fallback to os.getenv
try:
    from backend.config import settings
except ImportError:
    settings = None


SearchResult = Union[List[Dict[str, Any]], Dict[str, Any]]


class SearchEngine:
    """
    SerpAPI wrapper for web search operations
    Handles search queries with region-specific targeting
    """
    
    def __init__(self):
        if settings and hasattr(settings, 'serpapi_key'):
            self.api_key = settings.serpapi_key or os.getenv("SERPAPI_KEY")
        else:
            self.api_key = os.getenv("SERPAPI_KEY")
        if not self.api_key:
            logger.warning("SERPAPI_KEY not configured")
        
        self.session: aiohttp.ClientSession = None
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
        num_results: int = 10,
        language: str = "en"
    ) -> SearchResult:
        """
        Search the web using SerpAPI
        
        Args:
            query: Search query
            region: Region code (in=India, us=USA, etc.)
            num_results: Number of results to return
            language: Language code
        
        Returns:
            List of search results
        """
        if not self.api_key:
            message = "SERPAPI_KEY not configured. Add SERPAPI_KEY to .env and restart the backend."
            logger.error(message)
            return {
                "error": "missing_api_key",
                "message": message,
                "provider": "serpapi",
                "action_required": True,
            }
        
        logger.info(f"Searching: '{query}' (region={region}, n={num_results})")
        
        url = "https://serpapi.com/search"
        params = {
            "q": query,
            "location": self._get_location_string(region),
            "hl": language,
            "gl": region,
            "api_key": self.api_key,
            "num": num_results
        }
        
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        try:
            async with self.session.get(url, params=params, timeout=30) as response:
                if response.status != 200:
                    logger.error(f"SerpAPI error: {response.status}")
                    return {
                        "error": "serpapi_http_error",
                        "message": f"SerpAPI returned HTTP {response.status}",
                        "provider": "serpapi",
                        "action_required": False,
                        "details": {"status": response.status},
                    }

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
                        "date": result.get("date", "")
                    })

                # Log search
                self.search_logs.append({
                    "query": query,
                    "region": region,
                    "results_count": len(formatted_results),
                    "timestamp": datetime.now().isoformat()
                })

                logger.success(f"Found {len(formatted_results)} results")
                return formatted_results
        
        except Exception as e:
            logger.error(f"Search error: {e}")
            return {
                "error": "serpapi_client_error",
                "message": f"SerpAPI request failed: {type(e).__name__}",
                "provider": "serpapi",
                "action_required": False,
                "details": {"error": str(e)},
            }
    
    def _get_location_string(self, region_code: str) -> str:
        """Get location string for SerpAPI"""
        locations = {
            "in": "India",
            "us": "United States",
            "uk": "United Kingdom",
            "au": "Australia",
            "sg": "Singapore"
        }
        return locations.get(region_code, "India")
    
    def get_search_logs(self) -> List[Dict]:
        """Get all search logs"""
        return self.search_logs

