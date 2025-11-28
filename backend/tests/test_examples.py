"""
Example test cases with sample data
These can be used as templates for creating more tests
"""
import pytest
import asyncio
from backend.agents.profile_analyst import ProfileAnalystAgent
from backend.core.cloud_llm_client import CloudLLMClient
from backend.core.vector_store import ArtisanVectorStore


@pytest.mark.asyncio
class TestExamples:
    """Example test cases"""
    
    @pytest.fixture
    async def setup(self):
        llm = CloudLLMClient()
        vector_store = ArtisanVectorStore()
        yield {'llm': llm, 'vector_store': vector_store}
    
    async def test_potter_example(self, setup):
        """Example: Blue pottery artisan from Jaipur"""
        agent = ProfileAnalystAgent(
            setup['llm'],
            setup['vector_store']
        )
        
        result = await agent.analyze({
            'input_text': """I'm Raj, I make traditional blue pottery in Jaipur. 
            Been doing this for 10 years, learned from my father. 
            We specialize in decorative plates and vases with intricate floral patterns.""",
            'user_id': 'example_potter_001'
        })
        
        assert result['craft_type'] == 'pottery'
        assert 'jaipur' in result['location']['city'].lower()
        print(f"\n✓ Potter Example: {result['craft_type']} in {result['location']['city']}")
    
    async def test_weaver_example(self, setup):
        """Example: Banarasi silk weaver"""
        agent = ProfileAnalystAgent(
            setup['llm'],
            setup['vector_store']
        )
        
        result = await agent.analyze({
            'input_text': """I'm Priya, I weave traditional Banarasi silk sarees in Varanasi.
            Learned from my grandmother. We create intricate zari work.""",
            'user_id': 'example_weaver_001'
        })
        
        assert 'weav' in result['craft_type'].lower()
        print(f"\n✓ Weaver Example: {result['craft_type']} in {result['location']['city']}")
    
    async def test_metalworker_example(self, setup):
        """Example: Brass metalworker from Moradabad"""
        agent = ProfileAnalystAgent(
            setup['llm'],
            setup['vector_store']
        )
        
        result = await agent.analyze({
            'input_text': """I'm Ahmed, I do metalwork creating brass items in Moradabad.
            We make decorative items, utensils, and showpieces.""",
            'user_id': 'example_metalworker_001'
        })
        
        assert 'metal' in result['craft_type'].lower()
        print(f"\n✓ Metalworker Example: {result['craft_type']} in {result['location']['city']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

