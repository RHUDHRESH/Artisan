"""
Complete System Integration Tests
Tests the full workflow with all agents
Matching next.md specification
"""
import pytest
import asyncio
from core.ollama_client import OllamaClient
from core.vector_store import ArtisanVectorStore
from agents.profile_analyst import ProfileAnalystAgent
from agents.supply_hunter import SupplyHunterAgent
from agents.growth_marketer import GrowthMarketerAgent
from agents.event_scout import EventScoutAgent
from scraping.web_scraper import WebScraperService


@pytest.mark.asyncio
class TestCompleteSystem:
    """End-to-end system tests"""
    
    @pytest.fixture
    async def setup_system(self):
        """Setup all components"""
        ollama = OllamaClient()
        vector_store = ArtisanVectorStore("./data/test_chroma")
        scraper = WebScraperService()
        
        yield {
            'ollama': ollama,
            'vector_store': vector_store,
            'scraper': scraper
        }
    
    async def test_ollama_connection(self, setup_system):
        """Test Ollama is accessible"""
        components = setup_system
        
        # Test embeddings
        embedding = await components['ollama'].embed("test")
        assert len(embedding) > 0, "Embedding should have dimension > 0"
        
        # Test 4B model
        response = await components['ollama'].reasoning_task("Say hello")
        assert len(response) > 0, "4B model should respond"
        
        # Test 1B model
        response = await components['ollama'].fast_task("Say yes")
        assert len(response) > 0, "1B model should respond"
        
        print("✓ Ollama connection: PASS")
    
    async def test_vector_store(self, setup_system):
        """Test vector store operations"""
        components = setup_system
        
        store = components['vector_store']
        
        # Test adding document
        doc_id = await store.add_document(
            "craft_knowledge",
            "Test craft knowledge about pottery",
            {"test": True}
        )
        assert doc_id, "Should return document ID"
        
        # Test querying
        results = await store.query(
            "craft_knowledge",
            "pottery",
            n_results=1
        )
        assert len(results) > 0, "Should return at least one result"
        
        print("✓ Vector Store: PASS")
    
    async def test_profile_analyst(self, setup_system):
        """Test Profile Analyst Agent"""
        components = setup_system
        
        agent = ProfileAnalystAgent(
            components['ollama'],
            components['vector_store']
        )
        
        input_text = """I'm Raj Kumar, I make traditional blue pottery in Jaipur.
        I've been doing this for 15 years, learned from my father.
        We specialize in decorative plates, vases, and tiles with intricate floral patterns."""
        
        result = await agent.analyze({
            'input_text': input_text,
            'user_id': 'test_potter_001'
        })
        
        # Verify profile extraction
        assert result['craft_type'], "Should extract craft type"
        assert result.get('location'), "Should extract location"
        assert result.get('inferred_needs'), "Should infer needs"
        assert 'tools' in result.get('inferred_needs', {}), "Should infer tools"
        
        print("✓ Profile Analyst: PASS")
    
    async def test_supply_hunter(self, setup_system):
        """Test Supply Hunter Agent"""
        components = setup_system
        
        agent = SupplyHunterAgent(
            components['ollama'],
            components['vector_store'],
            components['scraper']
        )
        
        # Note: This test may take longer due to web scraping
        result = await agent.analyze({
            'craft_type': 'pottery',
            'supplies_needed': ['clay'],
            'location': {'city': 'Jaipur', 'state': 'Rajasthan', 'country': 'India'},
            'user_id': 'test_user_001'
        })
        
        assert 'suppliers' in result, "Should return suppliers list"
        assert 'total_suppliers_found' in result, "Should return count"
        assert isinstance(result['suppliers'], list), "Suppliers should be a list"
        
        print(f"✓ Supply Hunter: Found {result['total_suppliers_found']} suppliers")
    
    async def test_growth_marketer(self, setup_system):
        """Test Growth Marketer Agent"""
        components = setup_system
        
        agent = GrowthMarketerAgent(
            components['ollama'],
            components['vector_store'],
            components['scraper']
        )
        
        result = await agent.analyze({
            'craft_type': 'pottery',
            'specialization': 'blue pottery',
            'current_products': ['plates', 'vases'],
            'location': {'city': 'Jaipur', 'state': 'Rajasthan'}
        })
        
        assert 'trends' in result, "Should return trends"
        assert 'product_innovations' in result, "Should return innovations"
        assert 'pricing_insights' in result, "Should return pricing insights"
        assert isinstance(result['trends'], list), "Trends should be a list"
        
        print(f"✓ Growth Marketer: Found {len(result['trends'])} trends")
    
    async def test_event_scout(self, setup_system):
        """Test Event Scout Agent"""
        components = setup_system
        from services.maps_service import MapsService
        
        maps = MapsService()
        agent = EventScoutAgent(
            components['ollama'],
            components['vector_store'],
            components['scraper'],
            maps
        )
        
        result = await agent.analyze({
            'craft_type': 'pottery',
            'location': {
                'city': 'Jaipur',
                'state': 'Rajasthan',
                'country': 'India'
            },
            'travel_radius_km': 100
        })
        
        assert 'upcoming_events' in result, "Should return events"
        assert 'government_schemes' in result, "Should return schemes"
        assert isinstance(result['upcoming_events'], list), "Events should be a list"
        
        print(f"✓ Event Scout: Found {result['total_events_found']} events")
    
    async def test_potter_workflow(self, setup_system):
        """Test complete workflow for a potter - matching next.md"""
        components = setup_system
        
        # Step 1: Profile Analysis
        profile_agent = ProfileAnalystAgent(
            components['ollama'],
            components['vector_store']
        )
        
        input_text = """I'm Raj Kumar, I make traditional blue pottery in Jaipur.
        I've been doing this for 15 years, learned from my father.
        We specialize in decorative plates, vases, and tiles with intricate floral patterns."""
        
        profile_result = await profile_agent.analyze({
            'input_text': input_text,
            'user_id': 'test_potter_001'
        })
        
        # Verify profile extraction
        assert profile_result['craft_type'] == 'pottery'
        assert 'jaipur' in profile_result['location']['city'].lower()
        assert len(profile_result['inferred_needs']['tools']) > 0
        
        print("✓ Profile Analysis: PASS")
        
        # Step 2: Supply Hunting
        supply_agent = SupplyHunterAgent(
            components['ollama'],
            components['vector_store'],
            components['scraper']
        )
        
        supply_result = await supply_agent.analyze({
            'craft_type': profile_result['craft_type'],
            'supplies_needed': profile_result['inferred_needs']['supplies'],
            'location': profile_result['location']
        })
        
        # Verify suppliers found
        assert supply_result['total_suppliers_found'] > 0
        assert supply_result['india_suppliers'] > 0
        
        print(f"✓ Supply Hunter: Found {supply_result['total_suppliers_found']} suppliers")
        
        # Step 3: Growth Marketing
        growth_agent = GrowthMarketerAgent(
            components['ollama'],
            components['vector_store'],
            components['scraper']
        )
        
        growth_result = await growth_agent.analyze({
            'craft_type': profile_result['craft_type'],
            'specialization': profile_result['specialization'],
            'current_products': profile_result['typical_products'],
            'location': profile_result['location']
        })
        
        # Verify growth insights
        assert len(growth_result['product_innovations']) > 0
        assert 'pricing_insights' in growth_result
        
        print(f"✓ Growth Marketer: {len(growth_result['product_innovations'])} innovations found")
        
        print("\n✓✓✓ COMPLETE WORKFLOW TEST: PASSED ✓✓✓")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

