"""
Unit tests for individual agents
"""
import pytest
import asyncio
from backend.agents.base_agent import BaseAgent
from backend.agents.profile_analyst import ProfileAnalystAgent
from backend.core.cloud_llm_client import CloudLLMClient
from backend.core.vector_store import ArtisanVectorStore


@pytest.mark.asyncio
class TestAgents:
    """Test individual agent functionality"""
    
    @pytest.fixture
    async def setup_agents(self):
        """Setup agents for testing"""
        ollama = CloudLLMClient()
        vector_store = ArtisanVectorStore()
        
        yield {
            'ollama': ollama,
            'vector_store': vector_store
        }
    
    async def test_base_agent_logging(self, setup_agents):
        """Test base agent logging functionality"""
        components = setup_agents
        
        # Create a concrete agent instance
        agent = ProfileAnalystAgent(
            components['ollama'],
            components['vector_store']
        )
        
        # Test logging
        agent.log_execution("test_step", {"data": "test"})
        logs = agent.get_logs()
        
        assert len(logs) == 1, "Should have one log entry"
        assert logs[0]['step'] == "test_step", "Log step should match"
        assert 'timestamp' in logs[0], "Log should have timestamp"
        
        # Test clear logs
        agent.clear_logs()
        assert len(agent.get_logs()) == 0, "Logs should be cleared"
        
        print("✓ Base Agent Logging: PASS")
    
    async def test_profile_analyst_extraction(self, setup_agents):
        """Test profile analyst extraction capabilities"""
        components = setup_agents
        
        agent = ProfileAnalystAgent(
            components['ollama'],
            components['vector_store']
        )
        
        test_cases = [
            {
                "input": "I make pottery in Delhi",
                "expected_craft": "pottery"
            },
            {
                "input": "I weave traditional sarees in Varanasi",
                "expected_craft": "weaving"
            },
            {
                "input": "I do metalwork, creating brass items in Moradabad",
                "expected_craft": "metalwork"
            }
        ]
        
        for case in test_cases:
            result = await agent.analyze({
                'input_text': case['input'],
                'user_id': 'test_user'
            })
            
            # Verify craft type extraction
            craft_type = result.get('craft_type', '').lower()
            assert case['expected_craft'] in craft_type or craft_type in case['expected_craft'], \
                f"Should extract {case['expected_craft']} from: {case['input']}"
        
        print("✓ Profile Analyst Extraction: PASS")
    
    async def test_profile_analyst_needs_inference(self, setup_agents):
        """Test that profile analyst infers needs correctly"""
        components = setup_agents
        
        agent = ProfileAnalystAgent(
            components['ollama'],
            components['vector_store']
        )
        
        result = await agent.analyze({
            'input_text': "I'm a potter making clay pots. I need a kiln and clay.",
            'user_id': 'test_user'
        })
        
        inferred_needs = result.get('inferred_needs', {})
        
        assert 'tools' in inferred_needs, "Should infer tools"
        assert 'supplies' in inferred_needs, "Should infer supplies"
        assert len(inferred_needs.get('tools', [])) > 0, "Should have at least one tool"
        assert len(inferred_needs.get('supplies', [])) > 0, "Should have at least one supply"
        
        print("✓ Profile Analyst Needs Inference: PASS")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

