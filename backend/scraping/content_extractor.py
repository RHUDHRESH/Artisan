"""
Advanced content extraction using trafilatura and readability
Combines multiple extraction methods for best results
"""
import asyncio
import re
from typing import Dict, List, Optional, Any, Tuple
from bs4 import BeautifulSoup
from readability import Document
import trafilatura
from trafilatura.settings import use_config
from loguru import logger
import html
from urllib.parse import urljoin, urlparse
from datetime import datetime


class ContentExtractor:
    """Advanced content extraction combining multiple methods"""
    
    def __init__(self, fallback_enabled: bool = True):
        self.fallback_enabled = fallback_enabled
        self.trafilatura_config = use_config()
        self.trafilatura_config.set('DEFAULT', 'EXTRACTION_TIMEOUT', '10')
        
        # Content quality indicators
        self.min_content_length = 100
        self.min_title_length = 5
        self.max_title_length = 200
        
        # HTML patterns to clean
        self.clean_patterns = [
            r'<script[^>]*>.*?</script>',
            r'<style[^>]*>.*?</style>',
            r'<nav[^>]*>.*?</nav>',
            r'<footer[^>]*>.*?</footer>',
            r'<header[^>]*>.*?</header>',
            r'<aside[^>]*>.*?</aside>',
            r'<!--.*?-->',
            r'\s+',  # Multiple whitespace
        ]
    
    async def extract_content(self, html_content: str, url: str = None) -> Dict[str, Any]:
        """
        Extract content using multiple methods and return the best result
        
        Args:
            html_content: Raw HTML content
            url: Source URL for resolving relative links
            
        Returns:
            Dictionary with extracted content and metadata
        """
        extraction_results = {}
        
        # Method 1: Trafilatura (primary choice for structured content)
        try:
            trafilatura_result = await self._extract_with_trafilatura(html_content)
            extraction_results['trafilatura'] = trafilatura_result
        except Exception as e:
            logger.debug(f"Trafilatura extraction failed: {e}")
        
        # Method 2: Readability (good for article-style content)
        try:
            readability_result = await self._extract_with_readability(html_content)
            extraction_results['readability'] = readability_result
        except Exception as e:
            logger.debug(f"Readability extraction failed: {e}")
        
        # Method 3: BeautifulSoup fallback (basic extraction)
        if self.fallback_enabled:
            try:
                bs_result = await self._extract_with_beautifulsoup(html_content)
                extraction_results['beautifulsoup'] = bs_result
            except Exception as e:
                logger.debug(f"BeautifulSoup extraction failed: {e}")
        
        # Choose the best result
        best_result = self._choose_best_extraction(extraction_results, url)
        
        # Enhance with additional metadata
        if best_result:
            best_result = await self._enhance_content(best_result, html_content, url)
        
        return best_result or self._empty_result()
    
    async def _extract_with_trafilatura(self, html_content: str) -> Optional[Dict[str, Any]]:
        """Extract content using trafilatura"""
        try:
            # Use trafilatura for extraction
            extracted = trafilatura.extract(
                html_content,
                config=self.trafilatura_config,
                include_comments=False,
                include_tables=True,
                include_formatting=True,
                include_links=True,
                url=None
            )
            
            if extracted and len(extracted.strip()) >= self.min_content_length:
                # Extract metadata
                metadata = trafilatura.extract_metadata(
                    html_content,
                    config=self.trafilatura_config
                )
                
                return {
                    'content': extracted.strip(),
                    'title': metadata.title if metadata and metadata.title else '',
                    'author': metadata.author if metadata and metadata.author else '',
                    'date': metadata.date.isoformat() if metadata and metadata.date else None,
                    'language': metadata.language if metadata and metadata.language else '',
                    'source': 'trafilatura',
                    'word_count': len(extracted.split()),
                    'character_count': len(extracted),
                    'confidence': self._calculate_confidence(extracted, metadata)
                }
        except Exception as e:
            logger.debug(f"Trafilatura error: {e}")
        
        return None
    
    async def _extract_with_readability(self, html_content: str) -> Optional[Dict[str, Any]]:
        """Extract content using readability-lxml"""
        try:
            doc = Document(html_content)
            
            if doc.title() and len(doc.title()) >= self.min_title_length:
                content_html = doc.summary()
                
                # Convert to plain text
                soup = BeautifulSoup(content_html, 'html.parser')
                content_text = soup.get_text()
                
                # Clean up text
                content_text = self._clean_text(content_text)
                
                if len(content_text) >= self.min_content_length:
                    return {
                        'content': content_text,
                        'title': doc.title(),
                        'author': '',  # Readability doesn't extract author
                        'date': None,
                        'language': '',
                        'source': 'readability',
                        'word_count': len(content_text.split()),
                        'character_count': len(content_text),
                        'confidence': self._calculate_confidence(content_text, None)
                    }
        except Exception as e:
            logger.debug(f"Readability error: {e}")
        
        return None
    
    async def _extract_with_beautifulsoup(self, html_content: str) -> Optional[Dict[str, Any]]:
        """Extract content using BeautifulSoup (fallback method)"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract title
            title_tag = soup.find('title')
            title = title_tag.get_text().strip() if title_tag else ''
            
            # Try to find main content areas
            content_selectors = [
                'main',
                'article',
                '[role="main"]',
                '.content',
                '#content',
                '.post-content',
                '.entry-content',
                '.article-content'
            ]
            
            content_element = None
            for selector in content_selectors:
                element = soup.select_one(selector)
                if element:
                    content_element = element
                    break
            
            if not content_element:
                # Fallback to body content
                content_element = soup.find('body')
            
            if content_element:
                # Remove unwanted elements
                for unwanted in content_element.find_all(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                    unwanted.decompose()
                
                content_text = content_element.get_text()
                content_text = self._clean_text(content_text)
                
                if len(content_text) >= self.min_content_length:
                    return {
                        'content': content_text,
                        'title': title,
                        'author': '',
                        'date': None,
                        'language': '',
                        'source': 'beautifulsoup',
                        'word_count': len(content_text.split()),
                        'character_count': len(content_text),
                        'confidence': self._calculate_confidence(content_text, None) * 0.7  # Lower confidence for fallback
                    }
        except Exception as e:
            logger.debug(f"BeautifulSoup error: {e}")
        
        return None
    
    def _choose_best_extraction(self, results: Dict[str, Dict], url: str = None) -> Optional[Dict[str, Any]]:
        """Choose the best extraction result based on quality metrics"""
        if not results:
            return None
        
        # Score each result
        scored_results = []
        for method, result in results.items():
            if result:
                score = self._score_extraction(result, method)
                scored_results.append((score, result))
        
        if not scored_results:
            return None
        
        # Sort by score (highest first)
        scored_results.sort(key=lambda x: x[0], reverse=True)
        
        best_result = scored_results[0][1]
        best_result['extraction_method'] = scored_results[0][1].get('source', 'unknown')
        best_result['alternative_methods'] = [r[1].get('source') for r in scored_results[1:]]
        
        return best_result
    
    def _score_extraction(self, result: Dict, method: str) -> float:
        """Score extraction result based on quality metrics"""
        score = 0.0
        
        # Base confidence
        score += result.get('confidence', 0) * 0.4
        
        # Content length (prefer longer, but not too long)
        content_length = result.get('character_count', 0)
        if content_length >= 500 and content_length <= 10000:
            score += 0.3
        elif content_length >= 200:
            score += 0.2
        elif content_length >= 100:
            score += 0.1
        
        # Title quality
        title = result.get('title', '')
        if self.min_title_length <= len(title) <= self.max_title_length:
            score += 0.1
        
        # Method preference
        method_scores = {
            'trafilatura': 0.2,
            'readability': 0.15,
            'beautifulsoup': 0.05
        }
        score += method_scores.get(method, 0)
        
        # Additional metadata
        if result.get('author'):
            score += 0.05
        if result.get('date'):
            score += 0.05
        if result.get('language'):
            score += 0.05
        
        return min(score, 1.0)
    
    def _calculate_confidence(self, content: str, metadata) -> float:
        """Calculate confidence score for extracted content"""
        confidence = 0.5  # Base confidence
        
        # Content length factor
        if len(content) >= 1000:
            confidence += 0.2
        elif len(content) >= 500:
            confidence += 0.1
        elif len(content) >= 200:
            confidence += 0.05
        
        # Text quality factors
        sentences = content.split('.')
        if len(sentences) >= 5:
            confidence += 0.1
        
        # Check for meaningful content (not just navigation/links)
        words = content.split()
        if len(words) >= 50:
            confidence += 0.1
        
        # Metadata quality
        if metadata:
            if metadata.title:
                confidence += 0.05
            if metadata.author:
                confidence += 0.05
            if metadata.date:
                confidence += 0.05
        
        return min(confidence, 1.0)
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text"""
        # HTML decode
        text = html.unescape(text)
        
        # Apply cleaning patterns
        for pattern in self.clean_patterns:
            text = re.sub(pattern, ' ', text, flags=re.DOTALL | re.IGNORECASE)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    async def _enhance_content(self, result: Dict, html_content: str, url: str = None) -> Dict[str, Any]:
        """Enhance extracted content with additional metadata"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                result['meta_description'] = meta_desc['content'].strip()
            
            # Extract meta keywords
            meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
            if meta_keywords and meta_keywords.get('content'):
                result['meta_keywords'] = [k.strip() for k in meta_keywords['content'].split(',')]
            
            # Extract canonical URL
            canonical = soup.find('link', attrs={'rel': 'canonical'})
            if canonical and canonical.get('href'):
                result['canonical_url'] = canonical['href']
            elif url:
                result['canonical_url'] = url
            
            # Extract language from HTML
            html_tag = soup.find('html')
            if html_tag and html_tag.get('lang'):
                result['html_language'] = html_tag['lang']
            
            # Add extraction timestamp
            result['extracted_at'] = datetime.now().isoformat()
            
        except Exception as e:
            logger.debug(f"Content enhancement failed: {e}")
        
        return result
    
    def _empty_result(self) -> Dict[str, Any]:
        """Return empty extraction result"""
        return {
            'content': '',
            'title': '',
            'author': '',
            'date': None,
            'language': '',
            'source': 'none',
            'word_count': 0,
            'character_count': 0,
            'confidence': 0.0,
            'extraction_method': 'none',
            'extracted_at': datetime.now().isoformat()
        }


# Global extractor instance
_global_extractor: Optional[ContentExtractor] = None


def get_content_extractor() -> ContentExtractor:
    """Get global content extractor instance"""
    global _global_extractor
    if _global_extractor is None:
        _global_extractor = ContentExtractor()
    return _global_extractor


async def extract_content_advanced(html_content: str, url: str = None) -> Dict[str, Any]:
    """Convenience function for advanced content extraction"""
    extractor = get_content_extractor()
    return await extractor.extract_content(html_content, url)
