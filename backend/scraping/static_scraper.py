"""
Static Scraper - BeautifulSoup-based scraper for static HTML content
"""
from typing import Optional, List
import aiohttp
from bs4 import BeautifulSoup
from loguru import logger


class StaticScraper:
    """
    BeautifulSoup-based scraper for static content
    Fast and lightweight for non-JavaScript pages
    """
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def scrape(self, url: str, timeout: int = 15) -> Optional[str]:
        """
        Scrape a static webpage using BeautifulSoup
        
        Args:
            url: URL to scrape
            timeout: Request timeout in seconds
        
        Returns:
            Page text content or None
        """
        logger.info(f"Scraping static content: {url}")
        
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        try:
            async with self.session.get(url, headers=headers, timeout=timeout) as response:
                if response.status != 200:
                    logger.warning(f"HTTP {response.status} for {url}")
                    return None
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style", "nav", "footer", "header"]):
                    script.decompose()
                
                # Get text
                text = soup.get_text()
                
                # Clean up
                cleaned_text = self._clean_text(text)
                return cleaned_text[:10000]  # Limit to 10k chars
        
        except Exception as e:
            logger.error(f"Scraping error for {url}: {e}")
            return None
    
    def _clean_text(self, text: str) -> str:
        """Clean scraped text"""
        if not text:
            return ""
        
        # Split into lines and remove empty ones
        lines = (line.strip() for line in text.splitlines())
        # Split long lines and remove extra spaces
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # Join non-empty chunks
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
    
    async def extract_links(self, url: str) -> List[str]:
        """
        Extract all links from a page
        
        Returns:
            List of absolute URLs
        """
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        try:
            async with self.session.get(url, timeout=15) as response:
                if response.status != 200:
                    return []
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                links = []
                for a_tag in soup.find_all('a', href=True):
                    href = a_tag['href']
                    # Convert relative URLs to absolute
                    if href.startswith('/'):
                        from urllib.parse import urljoin
                        href = urljoin(url, href)
                    links.append(href)
                
                return links
        
        except Exception as e:
            logger.error(f"Error extracting links from {url}: {e}")
            return []
    
    async def close(self):
        """Close the session"""
        if self.session:
            await self.session.close()
            self.session = None

