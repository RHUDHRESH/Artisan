"""
Growth Marketer Agent - Identifies growth opportunities and market trends
"""
from typing import Dict, List, Optional
from backend.agents.base_agent import BaseAgent
from loguru import logger
import json


class GrowthMarketerAgent(BaseAgent):
    """
    Growth Marketer Agent
    
    Responsibilities:
    1. Identify adjacent market opportunities
    2. Analyze product innovation possibilities
    3. Provide pricing optimization suggestions
    4. Calculate ROI projections
    5. Discover trending products in artisan's niche
    6. Suggest modern adaptations of traditional crafts
    7. Identify high-margin applications
    
    Uses: Gemma 3 4B for complex market analysis
    """
    
    def __init__(self, ollama_client, vector_store, scraper_service):
        super().__init__(
            name="Growth Marketer",
            description="Identifies growth opportunities and market trends",
            ollama_client=ollama_client,
            vector_store=vector_store
        )
        self.scraper = scraper_service
    
    async def analyze(self, user_profile: Dict) -> Dict:
        """
        Analyze growth opportunities for the artisan
        
        Input format:
        {
            "craft_type": "pottery",
            "specialization": "blue pottery",
            "current_products": ["plates", "vases"],
            "location": {"city": "Jaipur", "state": "Rajasthan"},
            "typical_price_range": "Rs 500-2000" (optional)
        }
        
        Output format:
        {
            "trends": [...],
            "product_innovations": [...],
            "pricing_insights": {...},
            "roi_projections": [...],
            "marketing_channels": [...]
        }
        """
        self.log_execution("start", {"craft": user_profile.get("craft_type")})
        
        craft_type = user_profile.get("craft_type", "")
        specialization = user_profile.get("specialization", "")
        current_products = user_profile.get("current_products", [])
        
        # Step 1: Research trending products in this craft niche
        trends = await self._research_trends(craft_type, specialization)
        
        # Step 2: Generate product innovation ideas
        innovations = await self._generate_innovations(
            craft_type,
            specialization,
            current_products,
            trends
        )
        
        # Step 3: Analyze pricing strategies
        pricing = await self._analyze_pricing(craft_type, specialization)
        
        # Step 4: Calculate ROI projections
        roi_projections = await self._calculate_roi(innovations[:3])  # Top 3 ideas
        
        # Step 5: Identify marketing channels
        channels = await self._identify_channels(craft_type, user_profile.get("location"))
        
        self.log_execution("complete", {
            "trends_found": len(trends),
            "innovations": len(innovations)
        })
        
        return {
            "trends": trends,
            "product_innovations": innovations,
            "pricing_insights": pricing,
            "roi_projections": roi_projections,
            "marketing_channels": channels,
            "execution_logs": self.get_logs()
        }
    
    async def _research_trends(self, craft_type: str, specialization: str) -> List[Dict]:
        """
        Research current trends in the craft market
        """
        self.log_execution("researching_trends", {"craft": craft_type})
        
        # Search queries to find trends
        queries = [
            f"{craft_type} trends 2025",
            f"{specialization} trending products",
            f"{craft_type} best selling items Etsy",
            f"{craft_type} viral products Instagram",
            f"modern {craft_type} designs"
        ]
        
        all_trends = []
        
        for query in queries:
            results = await self.scraper.search(query, region="in", num_results=5)
            
            # Analyze each result for trend information
            for result in results[:3]:  # Top 3 per query
                # Scrape the page
                content = await self.scraper.scrape_page(result['url'])
                
                if not content:
                    continue
                
                # Use LLM to extract trend info
                trend_prompt = f"""Analyze this content about {craft_type} trends:

URL: {result['url']}
Title: {result['title']}
Content snippet: {content[:1000]}

Extract trend information in JSON format:
{{
    "trend_name": "name of the trend",
    "description": "what the trend is about",
    "growth_indicators": "evidence of growth (numbers, percentages)",
    "platforms": ["where this trend is popular"],
    "relevance": "high/medium/low - how relevant to {specialization}"
}}

If no clear trend found, return {{"trend_name": null}}
Return ONLY valid JSON."""

                result_text = await self.ollama.reasoning_task(trend_prompt)
                
                try:
                    if "```json" in result_text:
                        result_text = result_text.split("```json")[1].split("```")[0]
                    elif "```" in result_text:
                        result_text = result_text.split("```")[1].split("```")[0]
                    trend_data = json.loads(result_text.strip())
                    
                    if trend_data.get("trend_name"):
                        # Calculate relevance score
                        relevance_map = {"high": 0.9, "medium": 0.6, "low": 0.3}
                        relevance_score = relevance_map.get(
                            trend_data.get("relevance", "medium"),
                            0.5
                        )
                        
                        all_trends.append({
                            "trend_name": trend_data["trend_name"],
                            "description": trend_data.get("description", ""),
                            "growth_rate": trend_data.get("growth_indicators", "Unknown"),
                            "platforms": trend_data.get("platforms", []),
                            "relevance_score": relevance_score,
                            "source": result['url']
                        })
                except Exception as e:
                    logger.debug(f"Failed to parse trend from {result['url']}: {e}")
                    continue
        
        # Sort by relevance and deduplicate
        all_trends.sort(key=lambda x: x["relevance_score"], reverse=True)
        unique_trends = self._deduplicate_trends(all_trends)
        
        return unique_trends[:5]  # Top 5 trends
    
    async def _generate_innovations(
        self,
        craft_type: str,
        specialization: str,
        current_products: List[str],
        trends: List[Dict]
    ) -> List[Dict]:
        """
        Generate product innovation ideas based on trends and skills
        """
        self.log_execution("generating_innovations", {"craft": craft_type})
        
        # Build context about trends
        trends_context = "\n".join([
            f"- {t['trend_name']}: {t['description']}"
            for t in trends[:3]
        ]) if trends else "No specific trends found"
        
        innovation_prompt = f"""You are a product innovation consultant for artisans.

Artisan Profile:
- Craft: {craft_type} ({specialization})
- Current products: {', '.join(current_products) if current_products else 'Various items'}

Current Market Trends:
{trends_context}

Generate 5 innovative product ideas that:
1. Build on the artisan's existing skills
2. Align with market trends
3. Can be produced with minimal additional investment
4. Have high profit potential
5. Are unique or differentiated

For each idea, provide in JSON format:
[
    {{
        "idea": "product name",
        "description": "what it is and why it's innovative",
        "market_size": "Small/Medium/Large",
        "competition": "Low/Medium/High",
        "estimated_price_point": "price range in Rs",
        "materials_needed": ["list of materials"],
        "skill_overlap_percent": 0-100,
        "unique_selling_point": "what makes it special",
        "target_customer": "who would buy this"
    }}
]

Return ONLY valid JSON array."""

        result = await self.ollama.reasoning_task(innovation_prompt)
        
        try:
            if "```json" in result:
                result = result.split("```json")[1].split("```")[0]
            elif "```" in result:
                result = result.split("```")[1].split("```")[0]
            innovations = json.loads(result.strip())
            
            # Ensure it's a list
            if not isinstance(innovations, list):
                innovations = [innovations]
            
            # Add confidence scores
            for innovation in innovations:
                # Calculate confidence based on skill overlap and market size
                skill_overlap = innovation.get("skill_overlap_percent", 50) / 100
                market_size_map = {"Large": 0.3, "Medium": 0.2, "Small": 0.1}
                market_score = market_size_map.get(innovation.get("market_size", "Medium"), 0.2)
                competition_map = {"Low": 0.3, "Medium": 0.2, "High": 0.1}
                competition_score = competition_map.get(innovation.get("competition", "Medium"), 0.2)
                
                confidence = skill_overlap * 0.5 + market_score + competition_score
                innovation["confidence"] = min(1.0, confidence)
            
            # Sort by confidence
            innovations.sort(key=lambda x: x.get("confidence", 0), reverse=True)
            
            return innovations
        except Exception as e:
            logger.error(f"Failed to parse innovation ideas: {e}")
            return []
    
    async def _analyze_pricing(self, craft_type: str, specialization: str) -> Dict:
        """
        Analyze pricing strategies for the craft
        """
        self.log_execution("analyzing_pricing", {"craft": craft_type})
        
        # Search for pricing information
        queries = [
            f"{specialization} {craft_type} price India",
            f"{craft_type} pricing strategy handmade",
            f"how much does {specialization} sell for"
        ]
        
        pricing_data = []
        
        for query in queries:
            results = await self.scraper.search(query, region="in", num_results=3)
            
            for result in results[:2]:
                content = await self.scraper.scrape_page(result['url'])
                if content:
                    pricing_data.append(content[:500])
        
        if not pricing_data:
            return {
                "current_market_avg": "Data unavailable",
                "recommendation": "Research local market prices"
            }
        
        # Analyze with LLM
        pricing_context = "\n---\n".join(pricing_data)
        
        pricing_prompt = f"""Analyze pricing information for {craft_type} ({specialization}):

Market Data:
{pricing_context}

Provide pricing insights in JSON format:
{{
    "current_market_avg": "average price range",
    "premium_opportunity": "price range for premium positioning",
    "volume_pricing": "price range for volume sales",
    "factors_affecting_price": ["list of factors"],
    "recommendation": "strategic pricing recommendation"
}}

Return ONLY valid JSON."""

        result = await self.ollama.reasoning_task(pricing_prompt)
        
        try:
            if "```json" in result:
                result = result.split("```json")[1].split("```")[0]
            elif "```" in result:
                result = result.split("```")[1].split("```")[0]
            pricing_insights = json.loads(result.strip())
            return pricing_insights
        except Exception as e:
            logger.error(f"Failed to parse pricing insights: {e}")
            return {
                "current_market_avg": "Data unavailable",
                "recommendation": "Research local market prices"
            }
    
    async def _calculate_roi(self, innovations: List[Dict]) -> List[Dict]:
        """
        Calculate ROI projections for top innovation ideas
        """
        self.log_execution("calculating_roi", {"innovations_count": len(innovations)})
        
        roi_projections = []
        
        for innovation in innovations:
            # Use LLM to estimate costs and returns
            roi_prompt = f"""Calculate ROI projection for this product idea:

Product: {innovation.get('idea', 'Unknown')}
Description: {innovation.get('description', '')}
Estimated Price: {innovation.get('estimated_price_point', 'Unknown')}
Materials Needed: {', '.join(innovation.get('materials_needed', []))}

Provide realistic estimates in JSON:
{{
    "initial_investment": {{
        "materials": 0,
        "tools": 0,
        "marketing": 0,
        "total": 0
    }},
    "monthly_costs": {{
        "materials_per_unit": 0,
        "time_hours_per_unit": 0,
        "units_per_month_realistic": 0
    }},
    "revenue_projection": {{
        "price_per_unit": 0,
        "units_sold_month": 0,
        "monthly_revenue": 0
    }},
    "breakeven_analysis": {{
        "months_to_breakeven": 0,
        "units_to_breakeven": 0
    }}
}}

All amounts in Indian Rupees. Return ONLY valid JSON."""

            result = await self.ollama.reasoning_task(roi_prompt)
            
            try:
                if "```json" in result:
                    result = result.split("```json")[1].split("```")[0]
                elif "```" in result:
                    result = result.split("```")[1].split("```")[0]
                roi_data = json.loads(result.strip())
                
                roi_projections.append({
                    "scenario": innovation.get('idea', 'Unknown'),
                    "investment_needed": roi_data.get('initial_investment', {}).get('total', 0),
                    "monthly_revenue_potential": roi_data.get('revenue_projection', {}).get('monthly_revenue', 0),
                    "breakeven_months": roi_data.get('breakeven_analysis', {}).get('months_to_breakeven', 0),
                    "confidence": innovation.get('confidence', 0.5)
                })
            except Exception as e:
                logger.debug(f"Failed to calculate ROI for {innovation.get('idea')}: {e}")
                continue
        
        return roi_projections
    
    async def _identify_channels(self, craft_type: str, location: Dict) -> List[Dict]:
        """
        Identify marketing channels suitable for the artisan
        """
        self.log_execution("identifying_channels", {"craft": craft_type})
        
        location_str = f"{location.get('city', '')}, {location.get('state', '')}" if location else "India"
        
        channels_prompt = f"""Identify the best marketing channels for an artisan making {craft_type} in {location_str}.

Consider:
- Online platforms (Instagram, Facebook, Etsy, Amazon Handmade)
- Local opportunities (craft fairs, exhibitions, local stores)
- B2B channels (hotels, restaurants, interior designers)
- Export opportunities

Provide in JSON format:
[
    {{
        "channel": "channel name",
        "audience_size": "estimated reach",
        "cost": "Free/Low/Medium/High",
        "effort": "Low/Medium/High",
        "best_for": "what products/goals",
        "getting_started": "first steps to start"
    }}
]

Return ONLY valid JSON array with top 5 channels."""

        result = await self.ollama.reasoning_task(channels_prompt)
        
        try:
            if "```json" in result:
                result = result.split("```json")[1].split("```")[0]
            elif "```" in result:
                result = result.split("```")[1].split("```")[0]
            channels = json.loads(result.strip())
            
            # Ensure it's a list
            if not isinstance(channels, list):
                channels = [channels]
            
            return channels[:5]
        except Exception as e:
            logger.error(f"Failed to parse marketing channels: {e}")
            return []
    
    def _deduplicate_trends(self, trends: List[Dict]) -> List[Dict]:
        """Remove duplicate trends by name"""
        seen = set()
        unique = []
        
        for trend in trends:
            name = trend.get('trend_name', '').lower()
            if name and name not in seen:
                seen.add(name)
                unique.append(trend)
        
        return unique


# Test the Growth Marketer Agent
async def test_growth_marketer():
    from core.ollama_client import OllamaClient
    from core.vector_store import ArtisanVectorStore
    from scraping.web_scraper import WebScraperService
    
    ollama = OllamaClient()
    vector_store = ArtisanVectorStore("./data/test_chroma")
    scraper = WebScraperService()
    
    agent = GrowthMarketerAgent(ollama, vector_store, scraper)
    
    # Test input
    test_input = {
        "craft_type": "pottery",
        "specialization": "blue pottery",
        "current_products": ["decorative plates", "vases", "bowls"],
        "location": {"city": "Jaipur", "state": "Rajasthan"},
        "user_id": "test_user_001"
    }
    
    print("Analyzing growth opportunities...")
    result = await agent.analyze(test_input)
    
    print("\n=== MARKET TRENDS ===")
    for i, trend in enumerate(result['trends'][:3]):
        print(f"\n{i+1}. {trend['trend_name']}")
        print(f"   Growth: {trend['growth_rate']}")
        print(f"   Relevance: {trend['relevance_score']:.2f}")
    
    print("\n=== PRODUCT INNOVATIONS ===")
    for i, innovation in enumerate(result['product_innovations'][:3]):
        print(f"\n{i+1}. {innovation.get('idea', 'Unknown')}")
        print(f"   Price: {innovation.get('estimated_price_point', 'Unknown')}")
        print(f"   Confidence: {innovation.get('confidence', 0):.2f}")
    
    print("\n=== ROI PROJECTIONS ===")
    for projection in result['roi_projections']:
        print(f"\n{projection['scenario']}")
        print(f"   Investment: Rs {projection['investment_needed']}")
        print(f"   Monthly Revenue: Rs {projection['monthly_revenue_potential']}")
        print(f"   Breakeven: {projection['breakeven_months']} months")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_growth_marketer())
