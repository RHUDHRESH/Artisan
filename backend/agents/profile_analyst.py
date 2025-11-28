"""
Profile Analyst Agent - Infers artisan needs from organic conversation
"""
from typing import Dict, List
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
    
    def __init__(self, cloud_llm_client, vector_store=None):
        super().__init__(
            name="Profile Analyst",
            description="Infers artisan needs from organic conversation",
            cloud_llm_client=cloud_llm_client,
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

        # City-to-craft mapping for Rajasthan cities
        CITY_CRAFT_MAPPING = {
            "jaipur": "pottery",
            "udaipur": "traditional crafts",
            "jodhpur": "furniture",
            "jaisalmer": "handicrafts",
            "bikaner": "carpets",
            "kota": "embroidery",
            "ajmer": "traditional arts",
            "alwar": "textiles",
            "bharatpur": "handmade items",
            "chittorgarh": "traditional crafts",
            "pushkar": "traditional arts",
            "jhunjhunu": "traditional crafts"
        }

        # Defaults to ensure variables are always defined
        basic_info: Dict = {}
        needs_info: Dict = {}
        adjacencies: List[str] = []

        # Check if input is just "City CITYNAME" or similar
        if input_text.lower().startswith("city ") and len(input_text.split()) == 2:
            city_name = input_text.split()[1].lower()
            if city_name in CITY_CRAFT_MAPPING:
                # Direct mapping for location-based input
                basic_info = {
                    "name": "Local Artisan",
                    "craft_type": CITY_CRAFT_MAPPING[city_name],
                    "specialization": f"traditional {CITY_CRAFT_MAPPING[city_name]}",
                    "location": {
                        "city": city_name.title(),
                        "state": "Rajasthan",
                        "country": "India"
                    },
                    "experience_years": None,
                    "learned_from": "local craft tradition",
                    "story_elements": [f"Based in {city_name.title()}, specializes in {CITY_CRAFT_MAPPING[city_name]} craftsmanship"]
                }

                # Get default needs based on craft
                needs_info = self._get_craft_defaults(CITY_CRAFT_MAPPING[city_name])
                adjacencies = self._get_craft_adjacencies(CITY_CRAFT_MAPPING[city_name])

        # If not matched to a known city pattern, perform standard analysis
        if not basic_info:
            # Standard analysis using LLM
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

            extraction_result = await self.cloud_llm.reasoning_task(extraction_prompt)

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

            needs_result = await self.cloud_llm.reasoning_task(needs_prompt)

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

            adjacency_result = await self.cloud_llm.reasoning_task(adjacency_prompt)

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
    
    def _get_craft_defaults(self, craft_type: str) -> Dict:
        """Get default needs for a craft type"""
        craft_defaults = {
            "pottery": {
                "tools": ["pottery wheel", "kiln", "glazing tools", "measuring tools"],
                "workspace_requirements": "kiln required, ventilation needed, clay storage space",
                "raw_materials": ["clay", "pottery glaze", "pigments"],
                "skills_required": ["wheel throwing", "glazing", "firing"],
                "typical_products": ["plates", "vases", "bowls", "cups"],
                "market_segment": "traditional craft, premium segment"
            },
            "traditional crafts": {
                "tools": ["hand tools", "measuring tools", "finishing supplies"],
                "workspace_requirements": "well-lit workspace with storage",
                "raw_materials": ["fabric", "threads", "dyes"],
                "skills_required": ["hand craftsmanship", "traditional techniques"],
                "typical_products": ["traditional items", "decorative pieces"],
                "market_segment": "traditional craft, mid-range"
            },
            "furniture": {
                "tools": ["woodworking tools", "finishing equipment"],
                "workspace_requirements": "wood shop with dust collection",
                "raw_materials": ["wood", "varnish", "hardware"],
                "skills_required": ["woodworking", "finishing", "assembly"],
                "typical_products": ["furniture pieces", "decorative items"],
                "market_segment": "traditional craft, premium"
            }
        }
        return craft_defaults.get(craft_type.lower(), {
            "tools": ["basic tools"],
            "workspace_requirements": "standard workspace",
            "raw_materials": ["basic materials"],
            "skills_required": ["craftsmanship"],
            "typical_products": ["handmade items"],
            "market_segment": "traditional craft"
        })

    def _get_craft_adjacencies(self, craft_type: str) -> List[str]:
        """Get skill adjacencies for a craft type"""
        adjacencies = {
            "pottery": ["ceramic jewelry", "tile making", "sculpture", "kitchenware"],
            "traditional crafts": ["textiles", "embroidery", "handmade accessories", "traditional decor"],
            "furniture": ["wood carving", "home decor", "custom pieces"]
        }
        return adjacencies.get(craft_type.lower(), ["related craft items", "traditional accessories"])

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
    from backend.core.cloud_llm_client import CloudLLMClient
    from backend.core.vector_store import ArtisanVectorStore
    
    llm = CloudLLMClient()
    vector_store = ArtisanVectorStore()
    
    agent = ProfileAnalystAgent(llm, vector_store)
    
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
