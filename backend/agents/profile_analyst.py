"""
Profile Analyst Agent - Infers artisan needs from organic conversation
"""
from typing import Dict
from backend.agents.base_agent import BaseAgent
from loguru import logger
import json


class ProfileAnalystAgent(BaseAgent):
    """
    Profile Analyst Agent
    
    Responsibilities:
    1. Parse unstructured user input (organic conversation)
    2. Identify craft type and specialization
    3. Infer tool requirements
    4. Determine workspace needs
    5. Extract location from context
    6. Identify supply categories
    7. Understand skill adjacencies
    8. Assess market positioning
    
    Uses: Gemma 3 4B (reasoning model) for deep understanding
    """
    
    def __init__(self, ollama_client, vector_store):
        super().__init__(
            name="Profile Analyst",
            description="Infers artisan needs from organic conversation",
            ollama_client=ollama_client,
            vector_store=vector_store
        )
    
    async def analyze(self, user_profile: Dict) -> Dict:
        """
        Analyze user profile and infer needs
        
        Input format:
        {
            "input_text": "I'm Raj, I make traditional blue pottery...",
            "raw_conversation": [...] (optional)
        }
        
        Output format:
        {
            "craft_type": "pottery",
            "specialization": "blue pottery",
            "location": {
                "city": "Jaipur",
                "state": "Rajasthan",
                "country": "India"
            },
            "inferred_needs": {
                "tools": ["pottery wheel", "kiln", "glazing tools"],
                "workspace": "kiln required, ventilation needed",
                "supplies": ["clay", "blue pigments", "glazes"],
                "skills": ["wheel throwing", "glazing", "firing"]
            },
            "skill_adjacencies": ["ceramic jewelry", "tile making"],
            "market_position": "traditional craft, premium segment",
            "confidence": 0.85
        }
        """
        self.log_execution("start", {"input": user_profile.get("input_text", "")[:100]})
        
        input_text = user_profile.get("input_text", "")
        
        # Step 1: Extract basic information
        extraction_prompt = f"""Analyze this artisan's introduction and extract structured information.

Input: "{input_text}"

Extract the following in JSON format:
{{
    "name": "artisan's name",
    "craft_type": "type of craft (pottery, weaving, metalwork, etc.)",
    "specialization": "specific style or technique",
    "location": {{"city": "city name", "state": "state", "country": "country"}},
    "experience_years": number or null,
    "learned_from": "how they learned the craft",
    "story_elements": ["key story points"]
}}

Return ONLY valid JSON, no other text."""

        extraction_result = await self.ollama.reasoning_task(extraction_prompt)
        
        self.log_execution("extraction", {"raw_result": extraction_result})
        
        # Parse JSON (handle potential parsing errors)
        try:
            # Clean up the response (remove markdown code blocks if present)
            if "```json" in extraction_result:
                extraction_result = extraction_result.split("```json")[1].split("```")[0]
            elif "```" in extraction_result:
                extraction_result = extraction_result.split("```")[1].split("```")[0]
            
            basic_info = json.loads(extraction_result.strip())
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}\nResponse: {extraction_result}")
            # Fallback to simpler extraction
            basic_info = await self._fallback_extraction(input_text)
        
        self.log_execution("parsed_info", basic_info)
        
        # Step 2: Infer needs based on craft type
        needs_prompt = f"""Based on this craft profile, infer the artisan's needs:

Craft Type: {basic_info.get('craft_type', 'unknown')}
Specialization: {basic_info.get('specialization', 'unknown')}

Provide in JSON format:
{{
    "tools": ["essential tools needed"],
    "workspace_requirements": "description of workspace needs",
    "raw_materials": ["materials needed regularly"],
    "skills_required": ["key skills for this craft"],
    "typical_products": ["products they likely make"],
    "market_segment": "market positioning (premium/mid/budget, traditional/modern)"
}}

Return ONLY valid JSON."""

        needs_result = await self.ollama.reasoning_task(needs_prompt)
        
        try:
            if "```json" in needs_result:
                needs_result = needs_result.split("```json")[1].split("```")[0]
            elif "```" in needs_result:
                needs_result = needs_result.split("```")[1].split("```")[0]
            needs_info = json.loads(needs_result.strip())
        except:
            needs_info = {"error": "Could not parse needs"}
        
        self.log_execution("inferred_needs", needs_info)
        
        # Step 3: Identify skill adjacencies (what else could they make/sell)
        adjacency_prompt = f"""Given this craft: {basic_info.get('craft_type')} ({basic_info.get('specialization')})

What are 3-5 adjacent products or markets they could explore? Consider:
- Related crafts using similar skills
- Modern adaptations of traditional items
- Complementary products
- Higher-margin applications

Return as JSON array: ["adjacency 1", "adjacency 2", ...]"""

        adjacency_result = await self.ollama.reasoning_task(adjacency_prompt)
        
        try:
            if "```json" in adjacency_result:
                adjacency_result = adjacency_result.split("```json")[1].split("```")[0]
            elif "```" in adjacency_result:
                adjacency_result = adjacency_result.split("```")[1].split("```")[0]
            adjacencies = json.loads(adjacency_result.strip())
        except:
            adjacencies = []
        
        self.log_execution("adjacencies", adjacencies)
        
        # Step 4: Store in vector database for future retrieval
        profile_document = f"""
        Artisan: {basic_info.get('name', 'Unknown')}
        Craft: {basic_info.get('craft_type')} - {basic_info.get('specialization')}
        Location: {basic_info.get('location', {}).get('city', 'Unknown')}
        Tools needed: {', '.join(needs_info.get('tools', []))}
        Materials: {', '.join(needs_info.get('raw_materials', []))}
        """
        
        await self.vector_store.add_document(
            collection_name="user_context",
            document=profile_document,
            metadata={
                "user_id": user_profile.get("user_id", "anonymous"),
                "craft_type": basic_info.get('craft_type', 'unknown'),
                "location": basic_info.get('location', {}).get('city', 'unknown')
            }
        )
        
        # Compile final response
        final_response = {
            "craft_type": basic_info.get('craft_type'),
            "specialization": basic_info.get('specialization'),
            "location": basic_info.get('location'),
            "experience_years": basic_info.get('experience_years'),
            "inferred_needs": {
                "tools": needs_info.get('tools', []),
                "workspace": needs_info.get('workspace_requirements', ''),
                "supplies": needs_info.get('raw_materials', []),
                "skills": needs_info.get('skills_required', [])
            },
            "typical_products": needs_info.get('typical_products', []),
            "skill_adjacencies": adjacencies,
            "market_position": needs_info.get('market_segment', ''),
            "confidence": 0.85,  # TODO: Implement confidence scoring
            "execution_logs": self.get_logs()
        }
        
        self.log_execution("complete", {"status": "success"})
        
        return final_response
    
    async def _fallback_extraction(self, text: str) -> Dict:
        """Fallback extraction if JSON parsing fails"""
        return {
            "name": "Unknown",
            "craft_type": "unknown",
            "specialization": "unknown",
            "location": {"city": "unknown", "state": "unknown", "country": "India"},
            "experience_years": None,
            "learned_from": "unknown",
            "story_elements": []
        }


# Test the Profile Analyst Agent
async def test_profile_analyst():
    from backend.core.ollama_client import OllamaClient
    from backend.core.vector_store import ArtisanVectorStore
    
    ollama = OllamaClient()
    vector_store = ArtisanVectorStore()
    
    agent = ProfileAnalystAgent(ollama, vector_store)
    
    # Test input
    test_input = {
        "input_text": "I'm Raj, I make traditional blue pottery in Jaipur. Been doing this for 10 years, learned from my father. We specialize in decorative plates and vases with intricate floral patterns.",
        "user_id": "test_user_001"
    }
    
    print("Analyzing profile...")
    result = await agent.analyze(test_input)
    
    print("\n=== ANALYSIS RESULT ===")
    print(json.dumps(result, indent=2))
    
    print("\n=== EXECUTION LOGS ===")
    for log in result['execution_logs']:
        print(f"[{log['timestamp']}] {log['step']}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_profile_analyst())
