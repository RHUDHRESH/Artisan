"""
Cloudflare bypass and anti-bot detection system
Uses cloudscraper and advanced techniques to bypass protections
"""
import asyncio
import aiohttp
import cloudscraper
from typing import Dict, Optional, Any, List
from bs4 import BeautifulSoup
from loguru import logger
import time
import random
from fake_useragent import UserAgent


class CloudflareBypass:
    """Advanced Cloudflare and bot detection bypass"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'mobile': False,
                'desktop': True
            }
        )
        
        # Anti-detection headers
        self.base_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
    
    def get_random_headers(self) -> Dict[str, str]:
        """Generate random headers to appear more human"""
        headers = self.base_headers.copy()
        headers['User-Agent'] = self.ua.random
        
        # Add random variations
        if random.random() > 0.5:
            headers['Sec-GPC'] = '1'
        
        return headers
    
    async def bypass_with_cloudscraper(self, url: str, **kwargs) -> Optional[str]:
        """Use cloudscraper to bypass Cloudflare"""
        try:
            headers = kwargs.get('headers', {})
            headers.update(self.get_random_headers())
            
            # Run cloudscraper in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: self.scraper.get(url, headers=headers, **kwargs)
            )
            
            if response.status_code == 200:
                return response.text
            else:
                logger.warning(f"Cloudscraper failed with status {response.status_code}")
                return None
                
        except Exception as e:
            logger.debug(f"Cloudscraper error: {e}")
            return None
    
    async def bypass_with_aiohttp(self, url: str, session: aiohttp.ClientSession, **kwargs) -> Optional[str]:
        """Try to bypass with aiohttp using stealth techniques"""
        try:
            headers = kwargs.get('headers', {})
            headers.update(self.get_random_headers())
            
            # Add stealth parameters
            kwargs.update({
                'headers': headers,
                'timeout': aiohttp.ClientTimeout(total=30),
                'allow_redirects': True
            })
            
            async with session.get(url, **kwargs) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    # Check if we hit Cloudflare protection
                    if self._is_cloudflare_page(content):
                        logger.warning("Hit Cloudflare protection with aiohttp")
                        return None
                    
                    return content
                else:
                    logger.warning(f"Aiohttp request failed with status {response.status}")
                    return None
                    
        except Exception as e:
            logger.debug(f"Aiohttp bypass error: {e}")
            return None
    
    def _is_cloudflare_page(self, content: str) -> bool:
        """Check if page is Cloudflare protection page"""
        cloudflare_indicators = [
            'cloudflare',
            'ray id',
            'checking your browser',
            'enable javascript',
            'ddos protection',
            'security check'
        ]
        
        content_lower = content.lower()
        return any(indicator in content_lower for indicator in cloudflare_indicators)
    
    async def try_multiple_methods(self, url: str, session: aiohttp.ClientSession = None, **kwargs) -> Optional[str]:
        """Try multiple bypass methods in order"""
        methods = [
            ('cloudscraper', self.bypass_with_cloudscraper),
            ('aiohttp', self.bypass_with_aiohttp)
        ]
        
        for method_name, method_func in methods:
            try:
                logger.debug(f"Trying bypass method: {method_name}")
                
                if method_name == 'aiohttp' and session:
                    result = await method_func(url, session, **kwargs)
                else:
                    result = await method_func(url, **kwargs)
                
                if result:
                    logger.info(f"Successfully bypassed using {method_name}")
                    return result
                    
            except Exception as e:
                logger.debug(f"Method {method_name} failed: {e}")
                continue
        
        logger.warning("All bypass methods failed")
        return None


class AntiDetectionManager:
    """Manages anti-detection techniques and strategies"""
    
    def __init__(self):
        self.cloudflare_bypass = CloudflareBypass()
        self.request_patterns = {}
        self.last_request_time = {}
    
    async def make_stealth_request(self, url: str, session: aiohttp.ClientSession = None, **kwargs) -> Optional[str]:
        """Make a stealth request with anti-detection measures"""
        # Add delay to appear more human
        await self._add_human_delay()
        
        # Try Cloudflare bypass first
        result = await self.cloudflare_bypass.try_multiple_methods(url, session, **kwargs)
        
        if result:
            self._update_request_patterns(url, success=True)
            return result
        else:
            self._update_request_patterns(url, success=False)
            return None
    
    async def _add_human_delay(self):
        """Add random delay to appear more human"""
        delay = random.uniform(1, 3)
        await asyncio.sleep(delay)
    
    def _update_request_patterns(self, url: str, success: bool):
        """Track request patterns for optimization"""
        domain = url.split('/')[2] if '/' in url else url
        
        if domain not in self.request_patterns:
            self.request_patterns[domain] = {'success': 0, 'fail': 0}
        
        if success:
            self.request_patterns[domain]['success'] += 1
        else:
            self.request_patterns[domain]['fail'] += 1
        
        self.last_request_time[domain] = time.time()
    
    def get_domain_stats(self, domain: str) -> Dict[str, Any]:
        """Get statistics for a specific domain"""
        patterns = self.request_patterns.get(domain, {'success': 0, 'fail': 0})
        total = patterns['success'] + patterns['fail']
        
        return {
            'success_rate': (patterns['success'] / total * 100) if total > 0 else 0,
            'total_requests': total,
            'last_request': self.last_request_time.get(domain)
        }


# Global instances
_global_bypass: Optional[CloudflareBypass] = None
_global_anti_detection: Optional[AntiDetectionManager] = None


def get_cloudflare_bypass() -> CloudflareBypass:
    """Get global Cloudflare bypass instance"""
    global _global_bypass
    if _global_bypass is None:
        _global_bypass = CloudflareBypass()
    return _global_bypass


def get_anti_detection_manager() -> AntiDetectionManager:
    """Get global anti-detection manager"""
    global _global_anti_detection
    if _global_anti_detection is None:
        _global_anti_detection = AntiDetectionManager()
    return _global_anti_detection


async def bypass_protection(url: str, session: aiohttp.ClientSession = None, **kwargs) -> Optional[str]:
    """Convenience function to bypass protections"""
    manager = get_anti_detection_manager()
    return await manager.make_stealth_request(url, session, **kwargs)
