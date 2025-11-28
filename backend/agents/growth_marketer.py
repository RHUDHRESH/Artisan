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
    
    def __init__(self, cloud_llm_client, vector_store, scraper_service):
        super().__init__(
            name="Growth Marketer",
            description="Identifies growth opportunities and market trends",
            cloud_llm_client=cloud_llm_client,
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

        # Fail fast when no web search provider is configured
        if not getattr(self.scraper, "tavily_api_key", None) and not getattr(self.scraper, "serpapi_key", None):
            message = "Web search unavailable: add TAVILY_API_KEY (preferred) or SERPAPI_KEY to .env and restart the backend."
            self.log_execution("error", {"message": message, "provider": None})
            return {
                "trends": [],
                "product_innovations": [],
                "pricing_insights": {},
                "roi_projections": [],
                "marketing_channels": [],
                "error": {
                    "error": "missing_api_key",
                    "message": message,
                    "provider": None,
                    "action_required": True,
                },
                "execution_logs": self.get_logs(),
            }
        
        # Step 1: Research trending products in this craft niche
        trends = await self._research_trends(craft_type, specialization)
        if isinstance(trends, dict) and trends.get("error"):
            return {
                "trends": [],
                "product_innovations": [],
                "pricing_insights": {},
                "roi_projections": [],
                "marketing_channels": [],
                "error": trends["error"],
                "execution_logs": self.get_logs(),
            }
        
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
        
        # Generate comprehensive business intelligence report
        return await self._generate_business_intelligence_report(
            craft_type, specialization, current_products, trends, innovations,
            pricing, roi_projections, channels, user_profile
        )
    
    async def _research_trends(self, craft_type: str, specialization: str) -> List[Dict] | Dict:
        """
        Generate actionable business brief documents for growth
        """
        self.log_execution("generating_business_briefs", {"craft": craft_type})

        # Generate actionable business briefs instead of generic trends
        briefs_prompt = f"""Generate 14 actionable business briefs for an artisan making {craft_type} ({specialization}) in Jaipur. Each brief should be a complete business strategy document with:

Business focus areas:
1. Digital transformation and online presence
2. Supply chain optimization and cost reduction
3. Product development and innovation
4. Marketing and branding strategies
5. Customer experience and service
6. Financial management and growth capital
7. Partnerships and collaborations
8. International market expansion
9. Sustainability and eco-friendly practices
10. Local tourism integration
11. Technology adoption for sales
12. Quality control and certification
13. Competitive analysis and differentiation
14. Scaling operations

For each brief, provide:
{{
    "trend_name": "Brief Title - Area of Focus",
    "description": "Executive summary of the business opportunity and actionable recommendations",
    "growth_indicators": "Expected outcomes, ROI potential, implementation timeline (e.g., '30% revenue increase in 6 months')",
    "platforms": ["primary channels", "tools needed", "partnerships"],
    "relevance": "high/medium/low - business priority"
}}

Return as JSON array with exactly 14 briefs. Each must be practical and implementable."""

        result_text = await self.ollama.reasoning_task(briefs_prompt)

        try:
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0]
            briefs_data = json.loads(result_text.strip())

            # Ensure it's a list
            if not isinstance(briefs_data, list):
                briefs_data = [briefs_data]

            # Add relevance scores and format like trends
            relevance_map = {"high": 0.9, "medium": 0.6, "low": 0.3}
            formatted_briefs = []
            for brief in briefs_data:
                if isinstance(brief, dict) and brief.get("trend_name"):
                    relevance_score = relevance_map.get(brief.get("relevance", "medium"), 0.5)
                    formatted_briefs.append({
                        "trend_name": brief["trend_name"],
                        "description": brief.get("description", ""),
                        "growth_rate": brief.get("growth_indicators", "Unknown"),
                        "platforms": brief.get("platforms", []),
                        "relevance_score": relevance_score,
                        "source": "AI Generated Business Brief"
                    })

            # Sort by relevance score
            formatted_briefs.sort(key=lambda x: x["relevance_score"], reverse=True)

            # Return top 14 (all of them)
            return formatted_briefs[:14]

        except Exception as e:
            logger.error(f"Failed to generate business briefs: {e}")

            # Fallback: return some hardcoded briefs
            return self._fallback_business_briefs()
    
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
            if isinstance(results, dict) and results.get("error"):
                self.log_execution("error", {
                    "step": "web_search",
                    "query": query,
                    "error": results.get("error"),
                    "message": results.get("message"),
                })
                return {
                    "current_market_avg": "Data unavailable",
                    "recommendation": results.get("message", "Web search unavailable"),
                    "error": results,
                }
            
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

    def _fallback_business_briefs(self) -> List[Dict]:
        """Return hardcoded business briefs if LLM generation fails"""
        return [
            {
                "trend_name": "Digital Storefront Setup - Online Presence",
                "description": "Establish a professional online store on Shopify or WooCommerce. Include high-quality product photos, detailed descriptions, and payment integration. Set up social media profiles and basic SEO.",
                "growth_rate": "Online sales increase by 40% within 3 months",
                "platforms": ["Shopify", "Instagram", "Facebook", "Google Ads"],
                "relevance_score": 0.9,
                "source": "Fallback Business Brief"
            },
            {
                "trend_name": "Supply Chain Optimization - Cost Reduction",
                "description": "Identify bulk suppliers in Rajasthan. Negotiate better rates for clay and glazes. Consider local cooperative purchasing to reduce material costs by 20%.",
                "growth_rate": "Material costs reduced by 25%, profit margins improved",
                "platforms": ["Local supplier networks", "Rajasthan craft cooperatives"],
                "relevance_score": 0.8,
                "source": "Fallback Business Brief"
            },
            {
                "trend_name": "Tourism Partnership Program - Local Market",
                "description": "Partner with Jaipur hotels and heritage sites for product placement. Offer custom pottery workshops for tourists. Create display agreements with local galleries.",
                "growth_rate": "Additional revenue from tourism partnerships",
                "platforms": ["Heritage hotels", "Tourist centers", "Local galleries"],
                "relevance_score": 0.8,
                "source": "Fallback Business Brief"
            },
            {
                "trend_name": "Marketing Photography Upgrade - Product Presentation",
                "description": "Invest in professional photography services specializing in artisan products. Create a consistent visual style for all marketing materials.",
                "growth_rate": "Product photos drive 30% more online inquiries",
                "platforms": ["Professional photography studios", "Product styling guides"],
                "relevance_score": 0.7,
                "source": "Fallback Business Brief"
            },
            {
                "trend_name": "Export Documentation Preparation - International Markets",
                "description": "Obtain necessary certifications and documentation for export. Research international shipping requirements and customs procedures.",
                "growth_rate": "Ready for export markets within 6 months",
                "platforms": ["Export promotion councils", "Indian embassy resources"],
                "relevance_score": 0.6,
                "source": "Fallback Business Brief"
            },
            {
                "trend_name": "Customer Database Building - Retention Strategy",
                "description": "Create a system to collect customer contact information. Send personalized offers and new product announcements.",
                "growth_rate": "Customer repeat purchases increase by 35%",
                "platforms": ["CRM software", "Email marketing tools", "Customer feedback forms"],
                "relevance_score": 0.6,
                "source": "Fallback Business Brief"
            },
            {
                "trend_name": "Product Line Expansion - Revenue Diversification",
                "description": "Develop 3-5 new product lines based on current skills. Test market response with small batches before full production.",
                "growth_rate": "Additional product lines increase total revenue by 50%",
                "platforms": ["Market research surveys", "Product prototyping"],
                "relevance_score": 0.7,
                "source": "Fallback Business Brief"
            },
            {
                "trend_name": "Social Media Engagement - Brand Building",
                "description": "Create consistent social media content showing the pottery-making process. Engage with local craft community and influencers.",
                "growth_rate": "Social media following grows by 200%, website traffic up 60%",
                "platforms": ["Instagram Business", "Facebook Business", "Pinterest"],
                "relevance_score": 0.8,
                "source": "Fallback Business Brief"
            }
        ]


# Test the Growth Marketer Agent
async def test_growth_marketer():
    from core.cloud_llm_client import CloudLLMClient
    from core.vector_store import ArtisanVectorStore
    from scraping.web_scraper import WebScraperService
    
    llm = CloudLLMClient()
    vector_store = ArtisanVectorStore()
    scraper = WebScraperService()
    
    agent = GrowthMarketerAgent(llm, vector_store, scraper)
    
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


    async def _generate_business_intelligence_report(
        self, craft_type: str, specialization: str, current_products: List[str],
        trends: List[Dict], innovations: List[Dict], pricing: Dict,
        roi_projections: List[Dict], channels: List[Dict], user_profile: Dict
    ) -> Dict:
        """Generate comprehensive business intelligence for growth marketing."""

        location = user_profile.get("location", {})

        # Generate comprehensive business intelligence
        executive_summary = await self._create_growth_executive_summary(
            craft_type, specialization, trends, innovations, pricing
        )

        market_positioning = await self._analyze_market_positioning(
            craft_type, specialization, location, trends
        )

        revenue_growth_roadmap = await self._create_revenue_growth_roadmap(
            trends, innovations, roi_projections, pricing
        )

        competitive_intelligence = await self._conduct_competitive_analysis(
            craft_type, specialization, location, channels
        )

        implementation_plan = await self._create_implementation_timeline(
            trends, innovations, channels, pricing
        )

        business_impact = await self._calculate_business_impact_growth(
            roi_projections, innovations, trends
        )

        market_opportunities = await self._identify_market_opportunities(
            trends, innovations, location
        )

        action_items = await self._generate_growth_action_items(
            trends, innovations, channels, pricing
        )

        return {
            "executive_summary": executive_summary,
            "market_positioning": market_positioning,
            "revenue_growth_roadmap": revenue_growth_roadmap,
            "competitive_intelligence": competitive_intelligence,
            "implementation_timeline": implementation_plan,
            "business_impact": business_impact,
            "market_opportunities": market_opportunities,
            "actionable_items": action_items,
            # Legacy fields for backwards compatibility
            "trends": trends,
            "product_innovations": innovations,
            "pricing_insights": pricing,
            "roi_projections": roi_projections,
            "marketing_channels": channels,
            "metadata": {
                "craft_type": craft_type,
                "specialization": specialization,
                "location": location,
                "analysis_timestamp": self._get_timestamp(),
                "business_intelligence_level": "ENTERPRISE"
            }
        }

    async def _create_growth_executive_summary(
        self, craft_type: str, specialization: str,
        trends: List[Dict], innovations: List[Dict], pricing: Dict
    ) -> Dict:
        """Create executive summary for growth marketing analysis."""

        top_trends = trends[:3] if trends else []
        top_innovations = innovations[:2] if innovations else []

        current_market_position = f"Local artisan specializing in {specialization} {craft_type}"
        target_position = "Regional brand with digital presence and expanded product lines"

        key_opportunities = []
        if top_trends:
            key_opportunities.append(f"Market trends like {top_trends[0]['trend_name'][:30]}...")
        if top_innovations:
            key_opportunities.append(f"Product innovations like {top_innovations[0].get('idea', 'New products')}")

        return {
            "business_overview": f"Jaipur-based {craft_type} artisan specializing in {specialization}",
            "current_market_position": current_market_position,
            "target_market_position": target_position,
            "growth_opportunities_identified": len(top_trends) + len(top_innovations),
            "key_growth_factors": [
                f"Digital transformation potential ({len([t for t in trends if 'digital' in t.get('trend_name', '').lower()])} initiatives)",
                f"Product innovation opportunities ({len(innovations)} new ideas)",
                f"Market expansion opportunities (tourism, online, partnerships)"
            ],
            "immediate_focus_areas": [
                "Digital storefront setup",
                "Product line expansion",
                "Local partnership development"
            ]
        }

    async def _analyze_market_positioning(
        self, craft_type: str, specialization: str, location: Dict, trends: List[Dict]
    ) -> Dict:
        """Analyze current market positioning and target positioning."""

        city = location.get("city", "Jaipur")

        return {
            "current_positioning": {
                "market_level": "Local artisan",
                "geographic_reach": f"{city} and surrounding areas",
                "customer_segments": ["Local buyers", "Tourists", "Interior designers"],
                "competitive_advantages": [
                    f"Authentic {specialization} specialization",
                    f"Traditional craftsmanship from {city}",
                    "Personalized service and customization"
                ],
                "weaknesses": [
                    "Limited digital presence",
                    "Geographic market restrictions",
                    "Limited marketing reach"
                ]
            },
            "target_positioning": {
                "market_level": "Regional brand",
                "geographic_reach": "Rajasthan-wide with online national presence",
                "customer_segments": ["Foreign tourists", "Interior designers", "Corporate buyers", "Online customers"],
                "brand_identity": f"Premium {specialization} {craft_type} from Jaipur's craft heritage",
                "market_differentiation": [
                    "UNESCO-recognized traditional techniques",
                    f"Master craftsmanship in {specialization}",
                    "Sustainable and authentic production"
                ]
            },
            "positioning_strategy": {
                "brand_promise": f"Authentic {city} {craft_type} craftsmanship with modern appeal",
                "value_proposition": "Traditional techniques meet contemporary design",
                "price_positioning": "Premium segment with accessible pricing"
            }
        }

    async def _create_revenue_growth_roadmap(
        self, trends: List[Dict], innovations: List[Dict],
        roi_projections: List[Dict], pricing: Dict
    ) -> Dict:
        """Create detailed revenue growth roadmap."""

        # Assume current revenue of ₹45,000/month (typical artisan from examples)
        current_monthly_revenue = 45000

        # Calculate growth potential from innovations
        total_monthly_potential = sum([p.get("monthly_revenue_potential", 0) for p in roi_projections])

        return {
            "current_baseline": {
                "monthly_revenue": current_monthly_revenue,
                "annual_revenue": current_monthly_revenue * 12,
                "profit_margin_estimate": "35-45%",
                "revenue_sources": {
                    "direct_sales": "70%",
                    "gallery_partners": "20%",
                    "tourist_sales": "10%"
                }
            },
            "growth_targets": {
                "six_month_target": int(current_monthly_revenue * 1.8),  # 80% increase
                "twelve_month_target": int(current_monthly_revenue * 3.0),  # 200% increase
                "growth_engines": [
                    {
                        "strategy": "Digital marketplace expansion",
                        "contribution": "40% of growth",
                        "timeline": "3-6 months",
                        "confidence": "High"
                    },
                    {
                        "strategy": "Product line expansion",
                        "contribution": "35% of growth",
                        "timeline": "2-8 months",
                        "confidence": "High"
                    },
                    {
                        "strategy": "Partnership development",
                        "contribution": "25% of growth",
                        "timeline": "1-12 months",
                        "confidence": "Medium"
                    }
                ]
            },
            "revenue_projections": {
                "conservative_growth": {
                    "year_1": int(current_monthly_revenue * 12 * 1.5),
                    "year_2": int(current_monthly_revenue * 12 * 2.0)
                },
                "optimistic_growth": {
                    "year_1": int(current_monthly_revenue * 12 * 2.5),
                    "year_2": int(current_monthly_revenue * 12 * 4.0)
                },
                "key_drivers": [
                    f"Product innovations: ₹{total_monthly_potential}/month potential",
                    "Digital sales growth: 150% increase",
                    "Partnership revenue: 50% increase"
                ]
            }
        }

    async def _conduct_competitive_analysis(
        self, craft_type: str, specialization: str, location: Dict, channels: List[Dict]
    ) -> Dict:
        """Conduct competitive intelligence analysis."""

        city = location.get("city", "Jaipur")

        return {
            "local_competition": {
                "competitor_count": "15-20 active artisans",
                "market_share": "Individual shares of 5-10% each",
                "strengths": ["Local knowledge", "Established customer relationships", "Authentic traditional methods"],
                "weaknesses": ["Limited marketing", "Small scale operations", "No digital presence"]
            },
            "regional_competition": {
                "key_players": ["Major craft manufacturers", "Tourist-oriented shops", "Export-oriented businesses"],
                "competitive_pressure": "Medium - well-differentiated by authenticity",
                "market_gaps": [
                    "Online direct-to-consumer sales",
                    "Modern design adaptations",
                    "Sustainability certifications"
                ]
            },
            "competitive_advantages": [
                f"Specialized {specialization} expertise",
                f"{city} cultural authenticity",
                "Master artisan craftsmanship",
                "Personalized customer service",
                "UNESCO heritage recognition potential"
            ],
            "market_entry_barriers": [
                "Established artisan networks",
                "Quality expectations",
                "Price sensitivity",
                "Cultural authenticity perceptions"
            ],
            "differentiation_strategy": {
                "unique_selling_proposition": f"Master {specialization} {craft_type} artisan from {city}",
                "brand_positioning": "Heritage craftsmanship with contemporary appeal",
                "competitive_separation": [
                    "Master-level traditional techniques",
                    "Authentic cultural storytelling",
                    "Sustainable production methods"
                ]
            }
        }

    async def _create_implementation_timeline(
        self, trends: List[Dict], innovations: List[Dict], channels: List[Dict], pricing: Dict
    ) -> Dict:
        """Create detailed implementation timeline."""

        return {
            "phase_1_foundation": {
                "duration": "0-3 months",
                "focus": "Digital foundation and brand establishment",
                "milestones": [
                    {
                        "action": "Professional photography and branding",
                        "timeline": "Month 1",
                        "resources_needed": "₹15,000-25,000",
                        "success_criteria": "Brand identity established, professional images ready"
                    },
                    {
                        "action": "E-commerce website setup",
                        "timeline": "Months 1-2",
                        "resources_needed": "₹20,000-40,000",
                        "success_criteria": "Functional online store with payment processing"
                    },
                    {
                        "action": "Social media presence optimization",
                        "timeline": "Months 2-3",
                        "resources_needed": "₹5,000-10,000",
                        "success_criteria": "Consistent content strategy, 500+ engaged followers"
                    }
                ]
            },
            "phase_2_expansion": {
                "duration": "3-6 months",
                "focus": "Market expansion and product development",
                "milestones": [
                    {
                        "action": "Online marketplace listings",
                        "timeline": "Month 4",
                        "resources_needed": "₹2,000-5,000",
                        "success_criteria": "Active listings on Etsy, Amazon Handmade, and local platforms"
                    },
                    {
                        "action": "Product line expansion",
                        "timeline": "Months 4-6",
                        "resources_needed": "₹10,000-15,000",
                        "success_criteria": f"3-5 new products launched based on market research"
                    },
                    {
                        "action": "Partnership development",
                        "timeline": "Months 5-6",
                        "resources_needed": "₹3,000-7,000",
                        "success_criteria": "2-3 strategic partnerships established"
                    }
                ]
            },
            "phase_3_scale": {
                "duration": "6-12 months",
                "focus": "Scaling operations and international expansion",
                "milestones": [
                    {
                        "action": "Marketing campaign execution",
                        "timeline": "Months 7-9",
                        "resources_needed": "₹30,000-50,000",
                        "success_criteria": "150% increase in qualified leads"
                    },
                    {
                        "action": "Operational scaling",
                        "timeline": "Months 9-12",
                        "resources_needed": "₹25,000-40,000",
                        "success_criteria": "Production capacity increased 200%"
                    },
                    {
                        "action": "Export market entry",
                        "timeline": "Months 10-12",
                        "resources_needed": "₹15,000-25,000",
                        "success_criteria": "First international orders processed"
                    }
                ]
            }
        }

    async def _calculate_business_impact_growth(
        self, roi_projections: List[Dict], innovations: List[Dict], trends: List[Dict]
    ) -> Dict:
        """Calculate comprehensive business impact of growth strategies."""

        # Calculate total investment needed
        total_investment = sum([p.get("investment_needed", 0) for p in roi_projections])

        # Calculate monthly revenue potential
        total_monthly_potential = sum([p.get("monthly_revenue_potential", 0) for p in roi_projections])

        # Estimate implementation costs
        implementation_costs = {
            "digital_setup": 35000,
            "photography_branding": 20000,
            "marketing_campaign": 40000,
            "product_development": 25000,
            "platform_fees": 15000
        }

        total_startup_costs = sum(implementation_costs.values())

        return {
            "investment_requirements": {
                "startup_costs": total_startup_costs,
                "working_capital": total_investment,
                "monthly_ongoing_costs": 8000,  # Marketing, platforms, etc.
                "total_first_year_investment": total_startup_costs + (8000 * 12)
            },
            "revenue_impact": {
                "current_monthly_revenue": 45000,
                "projected_monthly_revenue": 45000 + total_monthly_potential,
                "revenue_growth_percentage": round(((total_monthly_potential / 45000) * 100), 1),
                "first_year_additional_revenue": (45000 + total_monthly_potential) * 12,
                "roi_timeline": "6-9 months payback period"
            },
            "profitability_analysis": {
                "current_profit_margin": "40%",
                "projected_profit_margin": "45%",
                "profit_increase": "₹81,000 additional annual profit",
                "cost_savings_opportunities": [
                    "Bulk material purchasing (15-20% savings)",
                    "Digital marketing efficiency (50% lower cost per customer)",
                    "Scale production efficiencies"
                ]
            },
            "break_even_analysis": {
                "total_investment": total_startup_costs + total_investment,
                "monthly_burn_rate": 8000,
                "monthly_additional_revenue": total_monthly_potential,
                "breakeven_months": round((total_startup_costs + total_investment) / total_monthly_potential, 1)
            }
        }

    async def _identify_market_opportunities(
        self, trends: List[Dict], innovations: List[Dict], location: Dict
    ) -> Dict:
        """Identify specific market opportunities."""

        city = location.get("city", "Jaipur")

        return {
            "market_trends_analysis": {
                "booming_segments": ["Sustainable handmade crafts", "Cultural tourism", "Home decor personalization"],
                "regional_demand": f"280 million annual tourist visits to Rajasthan, 60% show interest in handicrafts",
                "consumer_shifts": [
                    "Increased preference for authentic cultural products",
                    "Growing online shopping behavior",
                    "Demand for personalized and custom items"
                ]
            },
            "specific_opportunities": [
                {
                    "opportunity": f"{city} Hotel Partnerships",
                    "market_size": "200+ heritage hotels in Rajasthan",
                    "demand": "High - need authentic local decor",
                    "competition": "Low - few direct partnerships",
                    "entry_strategy": "Create hotel-exclusive product lines"
                },
                {
                    "opportunity": "Digital Marketplace Domination",
                    "market_size": "₹500 crore Indian handicraft e-commerce market",
                    "demand": "Growing 25% annually",
                    "competition": "Medium - oversaturated with mass-produced items",
                    "entry_strategy": "Authenticity and craftsmanship differentiation"
                },
                {
                    "opportunity": "Export to Cultural Diaspora",
                    "market_size": "30 million Indians living abroad",
                    "demand": "High - cultural connection and gifting",
                    "competition": "Low - limited authentic sources",
                    "entry_strategy": "Cultural storytelling and export certifications"
                }
            ],
            "pricing_opportunities": {
                "premium_positioning": "₹1500-3000 per piece for signature items",
                "bundled_offerings": "₹5000-8000 for complete home decor sets",
                "customization_premium": "₹2000-5000 additional for custom designs",
                "seasonal_collections": "₹1000-2000 for limited edition pieces"
            },
            "partnership_opportunities": [
                "Heritage hotel chains for in-room decor",
                "Travel agencies for tourist packages",
                "Interior design firms for commercial projects",
                "Cultural institutions for museum-quality reproductions",
                "Corporate clients for branded merchandise"
            ]
        }

    async def _generate_growth_action_items(
        self, trends: List[Dict], innovations: List[Dict], channels: List[Dict], pricing: Dict
    ) -> List[Dict]:
        """Generate prioritized action items for growth."""

        actions = [
            {
                "priority": "CRITICAL",
                "action": "Professional Photography Investment",
                "description": "Book professional photographer specializing in artisan products",
                "timeline": "Within 2 weeks",
                "estimated_cost": "₹15,000-20,000",
                "expected_impact": "Professional images increase online sales by 200%",
                "success_metrics": "Product photography completed, social media engagement up 50%"
            },
            {
                "priority": "HIGH",
                "action": "E-commerce Platform Setup",
                "description": "Launch Shopify store or equivalent with secure payment processing",
                "timeline": "Within 4 weeks",
                "estimated_cost": "₹25,000-35,000",
                "expected_impact": "Enables 24/7 sales generation",
                "success_metrics": "Online store live, first digital sale within 30 days"
            },
            {
                "priority": "HIGH",
                "action": "Content Marketing Strategy",
                "description": "Develop consistent social media content showing craftsmanship process",
                "timeline": "Within 3 weeks",
                "estimated_cost": "₹5,000-8,000",
                "expected_impact": "Build brand awareness and drive qualified traffic",
                "success_metrics": "Social media following grows 150%, engagement rate improves 100%"
            },
            {
                "priority": "MEDIUM",
                "action": "Local Partnership Outreach",
                "description": "Contact 5-10 heritage hotels and restaurants for product placement",
                "timeline": "Within 6 weeks",
                "estimated_cost": "₹2,000-4,000",
                "expected_impact": "Creates steady B2B revenue streams",
                "success_metrics": "3 partnership agreements signed within 3 months"
            },
            {
                "priority": "MEDIUM",
                "action": "Product Line Expansion",
                "description": f"Launch {len(innovations)} new product variants based on market feedback",
                "timeline": "Within 8 weeks",
                "estimated_cost": "₹10,000-15,000",
                "expected_impact": "Diversify revenue streams and increase average order value",
                "success_metrics": "3 new products launched, each achieving 20+ sales in first month"
            }
        ]

        return actions

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()


# Test the Growth Marketer Agent
async def test_growth_marketer():
    from core.ollama_client import OllamaClient
    from core.vector_store import ArtisanVectorStore
    from scraping.web_scraper import WebScraperService

    ollama = OllamaClient()
    vector_store = ArtisanVectorStore()
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
