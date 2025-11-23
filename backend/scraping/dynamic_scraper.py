"""
Dynamic Scraper - Playwright-based scraper for JavaScript-rendered content
"""
from typing import Dict, Optional
from playwright.async_api import async_playwright
from loguru import logger


class DynamicScraper:
    """
    Playwright-based scraper for dynamic content
    Handles JavaScript-rendered pages
    """
    
    async def scrape(self, url: str, timeout: int = 30000) -> Optional[str]:
        """
        Scrape a dynamic webpage using Playwright
        
        Args:
            url: URL to scrape
            timeout: Timeout in milliseconds
        
        Returns:
            Page text content or None
        """
        logger.info(f"Scraping dynamic content: {url}")
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                try:
                    # Navigate to page
                    await page.goto(url, wait_until="networkidle", timeout=timeout)
                    
                    # Wait for content to load
                    await page.wait_for_timeout(2000)
                    
                    # Get text content
                    text = await page.evaluate("() => document.body.innerText")
                    
                    await browser.close()
                    
                    # Clean and limit text
                    cleaned_text = self._clean_text(text)
                    return cleaned_text[:10000]  # Limit to 10k chars
                
                except Exception as e:
                    logger.error(f"Error scraping {url}: {e}")
                    await browser.close()
                    return None
        
        except Exception as e:
            logger.error(f"Playwright error for {url}: {e}")
            return None
    
    def _clean_text(self, text: str) -> str:
        """Clean scraped text"""
        if not text:
            return ""
        
        # Remove extra whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
    
    async def scrape_with_screenshot(self, url: str, screenshot_path: Optional[str] = None) -> Dict:
        """
        Scrape page and optionally take screenshot
        
        Returns:
            Dictionary with text and screenshot path
        """
        logger.info(f"Scraping with screenshot: {url}")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(2000)
                
                text = await page.evaluate("() => document.body.innerText")
                
                screenshot = None
                if screenshot_path:
                    await page.screenshot(path=screenshot_path)
                    screenshot = screenshot_path
                
                await browser.close()
                
                return {
                    "text": self._clean_text(text)[:10000],
                    "screenshot": screenshot
                }
            
            except Exception as e:
                await browser.close()
                raise e

