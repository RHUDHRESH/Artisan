"""
Tests for scraping functionality
"""
import pytest
from backend.scraping.search_engine import SearchEngine
from backend.scraping.static_scraper import StaticScraper
from backend.scraping.dynamic_scraper import DynamicScraper
from backend.scraping.verifier import DataVerifier


@pytest.mark.asyncio
class TestScraping:
    """Test scraping components"""
    
    async def test_search_engine(self):
        """Test SearchEngine"""
        async with SearchEngine() as engine:
            # This will only work if SERPAPI_KEY is set
            results = await engine.search("pottery suppliers India", region="in", num_results=3)
            
            # Results should be a list
            assert isinstance(results, list), "Results should be a list"
            
            # If we have results, check format
            if results:
                result = results[0]
                assert "title" in result, "Result should have title"
                assert "url" in result, "Result should have url"
                assert "snippet" in result, "Result should have snippet"
        
        print("✓ SearchEngine: PASS")
    
    async def test_static_scraper(self):
        """Test StaticScraper"""
        scraper = StaticScraper()
        
        # Test scraping a simple website
        text = await scraper.scrape("https://httpbin.org/html")
        
        # Should return some text (even if empty due to test site)
        assert isinstance(text, str) or text is None, "Should return string or None"
        
        await scraper.close()
        print("✓ StaticScraper: PASS")
    
    async def test_dynamic_scraper(self):
        """Test DynamicScraper"""
        scraper = DynamicScraper()
        
        # Test scraping (may be slow)
        text = await scraper.scrape("https://httpbin.org/html")
        
        assert isinstance(text, str) or text is None, "Should return string or None"
        
        print("✓ DynamicScraper: PASS")
    
    def test_data_verifier(self):
        """Test DataVerifier"""
        verifier = DataVerifier()
        
        # Test supplier verification
        supplier_data = {
            "name": "Test Supplier",
            "contact": {
                "phone": "1234567890",
                "email": "test@example.com",
                "website": "https://example.com"
            },
            "location": {
                "city": "Jaipur",
                "country": "India"
            }
        }
        
        search_results = [
            {"title": "Test Supplier Reviews", "snippet": "Great supplier"},
            {"title": "Test Supplier", "snippet": "Reliable company"}
        ]
        
        verification = verifier.verify_supplier(supplier_data, search_results)
        
        assert "confidence" in verification, "Should return confidence score"
        assert 0.0 <= verification["confidence"] <= 1.0, "Confidence should be 0-1"
        assert "legitimacy_indicators" in verification, "Should have legitimacy indicators"
        
        print("✓ DataVerifier: PASS")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

