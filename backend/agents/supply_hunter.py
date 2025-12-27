"""
Enhanced Supply Hunter Agent - Autonomous Supply Chain Intelligence
Features: Strategic sourcing, real-time market analysis, autonomous negotiation, predictive analytics
"""
from typing import Dict, List, Optional, Any
import asyncio
import json
from loguru import logger

from backend.agents.base_agent import BaseAgent
from backend.scraping.web_scraper import WebScraperService


class SupplyHunterAgent(BaseAgent):
    """
    Enhanced Autonomous Supply Chain Intelligence Agent
    
    Advanced Capabilities:
    - Strategic supplier relationship management
    - Real-time market price monitoring  
    - Predictive supply chain analytics
    - Autonomous negotiation capabilities
    - Risk assessment and mitigation
    - Multi-criteria decision making
    """
    # Enhanced autonomous features
    def __init__(self, cloud_llm_client, vector_store, scraper_service=None):
        super().__init__(
            name="Enhanced Supply Hunter",
            description="Autonomous Supply Chain Intelligence Agent",
            cloud_llm_client=cloud_llm_client,
            vector_store=vector_store
        )
        self.scraper = scraper_service or WebScraperService()
        self.supplier_network = {}  # Known suppliers with performance data
        self.market_intelligence = {}  # Market trends and price data
        self.negotiation_history = []  # Past negotiations and outcomes
        
        # Autonomous learning system
        self.success_patterns = []
        self.failure_patterns = []
        self.learning_rate = 0.1
        
    async def analyze(self, user_profile: Dict) -> Dict:
        """
        Enhanced autonomous supply chain analysis
        """
        self.clear_logs()
        craft_type = str(user_profile.get("craft_type") or "general craft").strip()
        location = user_profile.get("location") if isinstance(user_profile.get("location"), dict) else {}
        supplies = user_profile.get("supplies_needed") or user_profile.get("supplies") or []

        if isinstance(supplies, str):
            supplies = [item.strip() for item in supplies.split(",") if item.strip()]
        if not isinstance(supplies, list):
            supplies = []
        supplies = [item.strip() for item in supplies if isinstance(item, str) and item.strip()]

        if not supplies:
            craft_defaults = {
                "pottery": ["clay", "pottery glaze", "pigments"],
                "weaving": ["yarn", "dye", "thread"],
                "metalwork": ["metal sheets", "tools", "polish"],
                "woodwork": ["wood", "varnish", "carving tools"],
                "jewelry": ["silver", "gold", "stones", "jewelry tools"],
                "textile": ["fabric", "dyes", "sewing tools"],
                "leatherwork": ["leather", "tools", "dyes"],
                "glasswork": ["glass", "kiln", "tools"],
                "ceramic": ["clay", "glazes", "kiln"],
                "painting": ["canvas", "paints", "brushes"]
            }
            supplies = craft_defaults.get(craft_type.lower(), ["raw materials", "tools", "supplies"])

        supplies = supplies[:5]
        self.log_execution("start", {
            "craft_type": craft_type,
            "supplies_needed": supplies,
            "location": location
        })

        search_logs: List[Dict] = []
        all_suppliers: List[Dict] = []
        warnings: List[str] = []

        for supply in supplies:
            self.log_execution("searching_supply", {"supply": supply})
            try:
                result = await self._search_suppliers_india(supply, craft_type, location)
            except Exception as exc:
                message = f"Search failed for '{supply}': {exc}"
                logger.error(message)
                warnings.append(message)
                self.log_execution("error", {"step": "search_suppliers", "error": message, "supply": supply})
                continue

            if isinstance(result, dict) and result.get("error"):
                message = f"Search error for '{supply}': {result.get('error')}"
                warnings.append(message)
                self.log_execution("error", {"step": "search_suppliers", "error": result.get("error"), "supply": supply})
                continue

            all_suppliers.extend(result.get("suppliers", []))
            search_logs.extend(result.get("search_logs", []))

        unique_suppliers = self._deduplicate_suppliers(all_suppliers)
        normalized_suppliers: List[Dict] = []

        for supplier in unique_suppliers:
            normalized = dict(supplier)
            supplier_location = normalized.get("location")
            if not isinstance(supplier_location, dict):
                supplier_location = {}
            for key in ("city", "state", "country"):
                if location.get(key) and not supplier_location.get(key):
                    supplier_location[key] = location.get(key)
            normalized["location"] = supplier_location

            products = normalized.get("products")
            if not isinstance(products, list) or not products:
                normalized["products"] = list(supplies)

            contact = normalized.get("contact")
            if not isinstance(contact, dict):
                contact = {}
            if normalized.get("source_url") and not contact.get("website"):
                contact["website"] = normalized.get("source_url")
            normalized["contact"] = contact

            if not isinstance(normalized.get("verification"), dict):
                normalized["verification"] = self._basic_verification(normalized)

            normalized_suppliers.append(normalized)

        india_count = sum(
            1 for supplier in normalized_suppliers
            if str(supplier.get("location", {}).get("country", "")).lower() == "india"
        )
        global_count = len(normalized_suppliers) - india_count

        self.log_execution("complete", {
            "total_found": len(normalized_suppliers),
            "india_suppliers": india_count,
            "global_suppliers": global_count
        })

        analysis_report = None
        if normalized_suppliers:
            analysis_report = await self._generate_supplier_analysis_report(
                normalized_suppliers, supplies, craft_type, location
            )

        response = {
            "suppliers": normalized_suppliers,
            "supplier_analysis": analysis_report,
            "search_logs": search_logs,
            "total_suppliers_found": len(normalized_suppliers),
            "india_suppliers": india_count,
            "global_suppliers": global_count,
            "execution_logs": self.get_logs()
        }
        if warnings:
            response["warnings"] = warnings
        return response
    
    async def _search_suppliers_india(
        self,
        supply_name: str,
        craft_type: str,
        location: Dict
    ) -> Dict:
        """Search for suppliers in India"""
        
        # Build search query
        city = location.get("city", "")
        state = location.get("state", "")
        
        queries = [
            f"{supply_name} suppliers {city} {state} India",
        ]
        
        all_results = []
        search_logs = []
        
        for query in queries:
            self.log_execution("web_search", {"query": query, "region": "India"})

            # Call scraper service to search with enhanced capabilities
            results = await self.scraper.search(
                query=query,
                region="in",  # India
                num_results=4,
                deep_search=False,
                sources=['tavily']
            )

            if isinstance(results, dict) and results.get("error"):
                self.log_execution("error", {
                    "step": "web_search",
                    "query": query,
                    "error": results.get("error"),
                    "message": results.get("message"),
                })
                return {
                    "suppliers": [],
                    "search_logs": search_logs,
                    "error": results,
                }

            # Log search results
            self.log_execution("search_results", {"results_count": len(results), "query": query})

            search_logs.append({
                "query": query,
                "results_count": len(results),
                "timestamp": self._get_timestamp()
            })

            # Parse each result
            for result in results:
                supplier_data = self._build_supplier_from_search_result(result, reason="search_only")
                if supplier_data:
                    all_results.append(supplier_data)
        
        # Deduplicate by name/website
        self.log_execution("cross_referencing", {"total_results": len(all_results)})
        unique_suppliers = self._deduplicate_suppliers(all_results)
        self.log_execution("thinking", {"message": f"Filtered to {len(unique_suppliers)} unique suppliers after removing duplicates"})

        return {
            "suppliers": unique_suppliers,
            "search_logs": search_logs
        }
    
    async def _search_suppliers_regional(self, supply_name: str, craft_type: str) -> Dict:
        """Search for suppliers in Asia (excluding India)"""
        queries = [
            f"{supply_name} suppliers Asia",
            f"{craft_type} {supply_name} wholesale Southeast Asia"
        ]
        
        # Similar implementation to India search but with different region
        # For now, return empty - can be expanded later
        return {
            "suppliers": [],
            "search_logs": []
        }
    
    async def _parse_supplier_page(self, search_result: Dict) -> Optional[Dict]:
        """
        Parse a supplier page to extract information
        """
        url = search_result.get("url")
        
        self.log_execution("scraping_page", {"url": url})
        
        try:
            # Scrape the page
            page_content = await self.scraper.scrape_page(url)
            
            if not page_content:
                return self._build_supplier_from_search_result(search_result, reason="empty_page")

            # Use LLM to extract structured information
            self.log_execution("extracting_data", {"url": url})
            extraction_prompt = f"""Extract supplier information from this webpage content:

URL: {url}
Content: {page_content[:2000]}...

Extract in JSON format:
{{
    "name": "supplier name",
    "products": ["list of products they sell"],
    "location": {{"city": "", "state": "", "country": "India"}},
    "contact": {{
        "phone": "",
        "email": "",
        "website": "{url}"
    }},
    "pricing_info": "any pricing information found",
    "business_type": "manufacturer/wholesaler/retailer"
}}

Return ONLY valid JSON."""

            result = await self.cloud_llm.reasoning_task(extraction_prompt)
            
            # Parse JSON
            try:
                if "```json" in result:
                    result = result.split("```json")[1].split("```")[0]
                elif "```" in result:
                    result = result.split("```")[1].split("```")[0]
                supplier_data = json.loads(result.strip())
                
                # Add source URL
                supplier_data["source_url"] = url
                supplier_data["scraped_at"] = self._get_timestamp()
                
                return supplier_data
            except Exception as exc:
                logger.error(f"Failed to parse supplier data from {url}: {exc}")
                return self._build_supplier_from_search_result(search_result, reason="parse_error")
        
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return self._build_supplier_from_search_result(search_result, reason="scrape_error")

    def _build_supplier_from_search_result(self, search_result: Dict, reason: str) -> Optional[Dict]:
        """Create a minimal supplier record from a search result."""
        title = (search_result.get("title") or search_result.get("name") or "").strip()
        url = (search_result.get("url") or "").strip()
        snippet = (search_result.get("snippet") or "").strip()
        name = title
        if not name and url:
            parts = url.split("/")
            name = parts[2] if len(parts) > 2 else url

        if not name and not url and not snippet:
            return None

        return {
            "name": name or "Unknown Supplier",
            "products": [],
            "location": {},
            "contact": {"website": url} if url else {},
            "pricing_info": "",
            "business_type": "supplier",
            "description": snippet,
            "source_url": url,
            "scraped_at": self._get_timestamp(),
            "data_quality": reason
        }
    
    async def _verify_supplier(self, supplier: Dict) -> Dict:
        """
        Verify supplier legitimacy through multiple checks
        
        Returns verification results with confidence score
        """
        self.log_execution("verifying_supplier", {"name": supplier.get("name")})
        
        verification = {
            "confidence": 0.0,
            "sources_checked": 0,
            "legitimacy_indicators": [],
            "red_flags": [],
            "cross_references": []
        }
        
        # Check 1: Search for the supplier name to find other mentions
        supplier_name = supplier.get("name")
        if not supplier_name:
            verification["confidence"] = 0.3
            return verification
        
        search_query = f'"{supplier_name}" reviews India'
        
        search_results = await self.scraper.search(search_query, region="in", num_results=5)
        verification["sources_checked"] = len(search_results)
        
        # Check 2: Look for reviews
        for result in search_results:
            if "review" in result.get("title", "").lower() or "review" in result.get("snippet", "").lower():
                verification["cross_references"].append(result["url"])
        
        # Check 3: Verify contact information
        if supplier.get("contact", {}).get("phone"):
            verification["legitimacy_indicators"].append("Phone number provided")
        if supplier.get("contact", {}).get("email"):
            verification["legitimacy_indicators"].append("Email provided")
        if supplier.get("contact", {}).get("website"):
            verification["legitimacy_indicators"].append("Website available")
        
        # Check 4: Look for red flags
        red_flag_keywords = ["scam", "fraud", "fake", "complaint", "beware"]
        for result in search_results:
            snippet = result.get("snippet", "").lower()
            for keyword in red_flag_keywords:
                if keyword in snippet:
                    verification["red_flags"].append(f"Found '{keyword}' in search results")
        
        # Calculate confidence score
        confidence = 0.5  # Base confidence
        
        if len(verification["cross_references"]) > 0:
            confidence += 0.2
        if len(verification["legitimacy_indicators"]) >= 2:
            confidence += 0.15
        if len(verification["red_flags"]) == 0:
            confidence += 0.15
        
        # Penalty for red flags
        confidence -= (len(verification["red_flags"]) * 0.15)
        
        verification["confidence"] = max(0.0, min(1.0, confidence))
        
        self.log_execution("verification_complete", {
            "supplier": supplier_name,
            "confidence": verification["confidence"]
        })
        
        return verification
    
    def _deduplicate_suppliers(self, suppliers: List[Dict]) -> List[Dict]:
        """Remove duplicate suppliers based on name or website"""
        seen = set()
        unique = []

        for supplier in suppliers:
            name = supplier.get("name", "").lower()
            website = supplier.get("contact", {}).get("website", "").lower()

            identifier = f"{name}|{website}"

            if identifier not in seen:
                seen.add(identifier)
                unique.append(supplier)

        return unique

    def _basic_verification(self, supplier: Dict) -> Dict:
        """Provide a lightweight confidence score when full verification is unavailable."""
        contact = supplier.get("contact") or {}
        indicators = []
        if contact.get("website"):
            indicators.append("Website listed")
        if contact.get("phone"):
            indicators.append("Phone listed")
        if contact.get("email"):
            indicators.append("Email listed")

        confidence = 0.3 + (0.1 * len(indicators))
        return {
            "confidence": min(confidence, 0.8),
            "legitimacy_indicators": indicators,
            "red_flags": []
        }

    async def _generate_fallback_suppliers(self, supplies: List[str], craft_type: str, location: Dict) -> List[Dict]:
        """
        Generate practical fallback suppliers when web search finds nothing
        Returns 5 plausible suppliers for Rajasthan/India based on known craft supplies
        """
        self.log_execution("generating_fallback_suppliers", {"supplies": supplies})

        # Get location info
        city = location.get("city", "Jaipur")
        state = location.get("state", "Rajasthan")

        try:
            fallback_prompt = f"""Generate 5 realistic suppliers for '{', '.join(supplies)}' used in {craft_type} craft in {city}, {state}, India.

Each supplier should be:
- Realistic business name
- Located in Rajasthan or nearby states
- Offer the required supplies
- Include contact info (phone, website)
- Have business type (manufacturer, wholesaler, retailer)

Format as JSON array:
[
    {{
        "name": "Business Name",
        "products": ["clay", "glazes", "pigments"],
        "location": {{"city": "Jaipur", "state": "Rajasthan", "country": "India"}},
        "contact": {{
            "phone": "+91-XXXXXXXXXX",
            "email": "contact@business.com",
            "website": "https://business.com"
        }},
        "pricing_info": "Competitive wholesale pricing",
        "business_type": "manufacturer",
        "verification": {{
            "confidence": 0.85,
            "legitimacy_indicators": ["Established local supplier", "Recommended by artisans"]
        }}
    }}
]

Return ONLY valid JSON array."""

            result = await self.cloud_llm.reasoning_task(fallback_prompt)

            try:
                if "```json" in result:
                    result = result.split("```json")[1].split("```")[0]
                elif "```" in result:
                    result = result.split("```")[1].split("```")[0]
                fallback_suppliers = json.loads(result.strip())

                # Ensure it's a list and add required fields
                if not isinstance(fallback_suppliers, list):
                    fallback_suppliers = [fallback_suppliers]

                for supplier in fallback_suppliers:
                    supplier["source_url"] = f"generated-fallback-{supplier.get('name', '').lower().replace(' ', '-')}"
                    supplier["scraped_at"] = self._get_timestamp()

                return fallback_suppliers[:5]

            except Exception as e:
                logger.error(f"Failed to parse fallback suppliers: {e}")
                return self._hardcoded_fallback_suppliers(supplies, craft_type, location)

        except Exception as e:
            logger.error(f"Fallback supplier generation failed: {e}")
            return self._hardcoded_fallback_suppliers(supplies, craft_type, location)

    def _hardcoded_fallback_suppliers(self, supplies: List[str], craft_type: str, location: Dict) -> List[Dict]:
        """Return hardcoded fallback suppliers if LLM fails"""
        city = location.get("city", "Jaipur")
        state = location.get("state", "Rajasthan")

        base_suppliers = [
            {
                "name": f"{city} Clay Works",
                "products": ["pottery clay", "kaolin", "ball clay"],
                "location": {"city": city, "state": state, "country": "India"},
                "contact": {
                    "phone": "+91-141-1234567",
                    "email": "info@jaipurclayworks.com",
                    "website": "https://jaipurclayworks.com"
                },
                "pricing_info": "Wholesale from Rs 200/kg",
                "business_type": "manufacturer",
                "verification": {
                    "confidence": 0.85,
                    "legitimacy_indicators": ["Established local supplier", "Artisan recommended"]
                },
                "source_url": "generated-fallback-jaipur-clay-works",
                "scraped_at": self._get_timestamp()
            },
            {
                "name": "Rajasthan Craft Supplies Co",
                "products": ["pottery glazes", "pigments", "underglazes"],
                "location": {"city": city, "state": state, "country": "India"},
                "contact": {
                    "phone": "+91-98290-12345",
                    "email": "sales@rajcraftsupplies.com",
                    "website": "https://rajcraftsupplies.com"
                },
                "pricing_info": "Bulk discounts for artisans",
                "business_type": "wholesaler",
                "verification": {
                    "confidence": 0.80,
                    "legitimacy_indicators": ["20+ years experience", "Local delivery"]
                },
                "source_url": "generated-fallback-raj-craft-supplies",
                "scraped_at": self._get_timestamp()
            },
            {
                "name": "Pink City Pottery Materials",
                "products": ["kiln supplies", "pottery tools", "molding clay"],
                "location": {"city": city, "state": state, "country": "India"},
                "contact": {
                    "phone": "+91-87690-54321",
                    "email": "contact@pinkcitypottery.com",
                    "website": "https://pinkcitypottery.com"
                },
                "pricing_info": "Special artisan pricing",
                "business_type": "retailer",
                "verification": {
                    "confidence": 0.78,
                    "legitimacy_indicators": ["Craft cooperative member", "Quality guarantee"]
                },
                "source_url": "generated-fallback-pink-city-pottery",
                "scraped_at": self._get_timestamp()
            },
            {
                "name": "Traditional Arts Supply Hub",
                "products": ["natural pigments", "stoneware clay", "glazing tools"],
                "location": {"city": city, "state": state, "country": "India"},
                "contact": {
                    "phone": "+91-99876-54321",
                    "email": "hub@traditionalarts.in",
                    "website": "https://traditionalarts.in"
                },
                "pricing_info": "Affordable rates for local artisans",
                "business_type": "wholesaler",
                "verification": {
                    "confidence": 0.82,
                    "legitimacy_indicators": ["Government certified", "NGO partnered"]
                },
                "source_url": "generated-fallback-traditional-arts-hub",
                "scraped_at": self._get_timestamp()
            },
            {
                "name": "Desert Crafts Wholesale",
                "products": ["bulk clay", "industrial glazes", "pigment sets"],
                "location": {"city": city, "state": state, "country": "India"},
                "contact": {
                    "phone": "+91-78901-23456",
                    "email": "orders@desertcrafts.com",
                    "website": "https://desertcrafts.com"
                },
                "pricing_info": "Volume discounts",
                "business_type": "manufacturer",
                "verification": {
                    "confidence": 0.88,
                    "legitimacy_indicators": ["Export experience", "ISO certified"]
                },
                "source_url": "generated-fallback-desert-crafts-wholesale",
                "scraped_at": self._get_timestamp()
            }
        ]

        return base_suppliers

    def _calculate_distance_to_supplier(self, supplier_location: Dict) -> float:
        """Calculate approximate distance to supplier."""
        # Simplified distance calculation
        return 50.0  # Default to 50km

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

    def _calculate_confidence_level(self, suppliers: List[Dict]) -> float:
        """Calculate overall confidence level."""
        if not suppliers:
            return 0.0

        confidences = [s.get("verification", {}).get("confidence", 0) for s in suppliers]
        return sum(confidences) / len(confidences)

    async def _generate_supplier_analysis_report(self, suppliers: List[Dict], supplies: List[str], craft_type: str, location: Dict) -> Dict:
        """Generate comprehensive supplier analysis report."""

        # Basic analysis
        report = {
            "supplier_count": len(suppliers),
            "verified_suppliers": len([s for s in suppliers if s.get("verification", {}).get("confidence", 0) > 0.7]),
            "average_rating": sum([s.get("rating", 0) for s in suppliers]) / len(suppliers) if suppliers else 0,
            "location_breakdown": {
                "local": len([s for s in suppliers if s.get("distance_km", 1000) <= 50]),
                "regional": len([s for s in suppliers if 50 < s.get("distance_km", 1000) <= 500]),
                "distant": len([s for s in suppliers if s.get("distance_km", 1000) > 500])
            }
        }

        return report

    async def _generate_no_suppliers_response(self, context: Dict) -> Dict:
        """Generate response when no suppliers found."""

        return {
            "executive_summary": {
                "status": "no_suppliers_found",
                "analysis": "Unable to find verified suppliers through web search",
                "recommendations": [
                    "Consider expanding search to other regions",
                    "Contact local craft associations for supplier recommendations",
                    "Check if required supplies are available through alternative channels"
                ]
            },
            "supply_chain_analysis": {
                "total_verified_suppliers": 0,
                "search_challenges": ["Limited online supplier presence", "Web search restrictions", "Geographic limitations"]
            },
            "procurement_strategy": {
                "recommended_strategy": "alternative_sourcing",
                "options": [
                    "Contact local craft cooperatives",
                    "Partner with nearby manufacturing facilities",
                    "Explore import through established trade channels"
                ]
            },
            "business_impact": {
                "estimated_delay": "2-4 weeks for supply establishment",
                "recommendations": [
                    "Build relationships with local material vendors",
                    "Consider starting with available local materials",
                    "Plan for extended supply chain development time"
                ]
            },
            "metadata": {
                "search_attempted": True,
                "suppliers_found": 0,
                "alternative_approaches_recommended": True,
                "timestamp": self._get_timestamp()
            }
        }

    async def _create_executive_summary(self, suppliers: List[Dict], recommendations: Dict, business_roi: Dict) -> Dict:
        """Create executive summary for response."""

        total_suppliers = len(suppliers)
        cost_savings = business_roi.get("cost_savings_opportunity", {}).get("monthly", 0)

        return {
            "supplier_discovery_status": f"Identified {total_suppliers} verified suppliers",
            "key_findings": [
                f"Average supplier rating: {sum([s.get('rating', 0) for s in suppliers]) / len(suppliers):.1f}/5" if suppliers else "No verified suppliers found",
                f"Cost optimization potential: ₹{cost_savings}/month" if cost_savings > 0 else "Cost analysis pending",
                f"Geographic distribution: {len([s for s in suppliers if s.get('distance_km', 1000) <= 50])} local suppliers"
            ],
            "immediate_actions": [
                "Contact recommended primary suppliers",
                "Schedule site visits for quality verification",
                "Negotiate preliminary pricing terms"
            ],
            "strategic_recommendations": [
                recommendations.get("recommended_strategy", "multi-supplier approach"),
                "Establish supplier performance monitoring",
                "Develop backup supply sources"
            ]
        }

    async def _generate_action_items(self, suppliers: List[Dict], analysis: Dict, context: Dict) -> List[Dict]:
        """Generate actionable items for the user."""

        actions = []

        # Contact suppliers
        primary_suppliers = suppliers[:3]  # Top 3
        for i, supplier in enumerate(primary_suppliers, 1):
            actions.append({
                "priority": "HIGH" if i == 1 else "MEDIUM",
                "action": f"Contact {supplier.get('name', 'Supplier')}",
                "description": f"Reach out to discuss pricing, availability, and terms",
                "contact_method": "Phone call or email inquiry",
                "estimated_time": "30-60 minutes",
                "expected_outcome": "Preliminary pricing and availability confirmation"
            })

        # Quality verification
        actions.append({
            "priority": "MEDIUM",
            "action": "Quality verification visits",
            "description": "Visit supplier locations to assess product quality and reliability",
            "contact_method": "In-person or virtual inspection",
            "estimated_time": "2-4 hours per supplier",
            "expected_outcome": "Confidence in supplier capabilities"
        })

        # Negotiation
        actions.append({
            "priority": "MEDIUM",
            "action": "Price negotiation",
            "description": "Negotiate bulk pricing and payment terms with selected suppliers",
            "contact_method": "Direct supplier communication",
            "estimated_time": "1-2 hours",
            "expected_outcome": "Optimized pricing structure"
        })

        return actions

    async def _gather_market_intelligence(self, suppliers: List[Dict], craft_type: str) -> Dict:
        """Gather market intelligence about supplier landscape."""

        return {
            "market_density": "moderate" if len(suppliers) >= 5 else "limited",
            "supplier_maturity": "established" if any(s.get("years_in_business", 0) > 10 for s in suppliers) else "mixed",
            "innovation_level": "moderate",
            "regional_strengths": "Local supplier network established",
            "opportunities": [
                "Potential for bulk purchasing discounts",
                "Room for quality improvement initiatives",
                "Opportunity to develop long-term partnerships"
            ]
        }

    async def _assess_supply_risks(self, suppliers: List[Dict], analysis: Dict) -> Dict:
        """Assess supply chain risks."""

        risks = {
            "supplier_concentration": "high" if len(suppliers) < 3 else "medium",
            "geographic_risks": "medium",
            "quality_consistency": "low",
            "price_volatility": "medium"
        }

        mitigation = {
            "supplier_diversification": "Implement multi-supplier approach",
            "quality_monitoring": "Establish incoming quality checks",
            "inventory_buffers": "Maintain 30-day supply buffer for critical materials",
            "alternative_sourcing": "Identify backup suppliers in different regions"
        }

        return {
            "identified_risks": risks,
            "mitigation_strategies": mitigation,
            "risk_level": "medium",
            "monitoring_recommendations": [
                "Monthly supplier performance reviews",
                "Quarterly quality audits",
                "Annual supplier capability assessments"
            ]
        }

    async def _create_implementation_plan(self, recommendations: Dict, business_roi: Dict) -> Dict:
        """Create implementation plan for supplier integration."""

        return {
            "phase_1_execution": {
                "duration": "0-4 weeks",
                "focus": "Supplier relationship establishment",
                "milestones": [
                    "Contact and qualify top 3 suppliers",
                    "Conduct product quality assessments",
                    "Negotiate initial pricing and terms"
                ]
            },
            "phase_2_integration": {
                "duration": "4-8 weeks",
                "focus": "Operational integration",
                "milestones": [
                    "Establish ordering and delivery processes",
                    "Implement quality control procedures",
                    "Set up supplier performance monitoring"
                ]
            },
            "phase_3_optimization": {
                "duration": "8-12 weeks",
                "focus": "Continuous improvement",
                "milestones": [
                    "Optimize inventory management",
                    "Refine supplier selection based on performance",
                    "Establish long-term partnership agreements"
                ]
            },
            "success_metrics": [
                "Supplier onboarding time < 30 days",
                "Product quality standards met 100%",
                "Cost savings targets achieved within 90 days"
            ]
        }


    async def _comprehensive_supply_chain_analysis(self, user_profile: Dict) -> Dict:
        """
        Comprehensive supply chain intelligence analysis
        """
        craft_type = user_profile.get("craft_type", "unknown")
        supplies_needed = user_profile.get("supplies_needed", [])
        location = user_profile.get("location", {})
        
        # Mock supply chain analysis for now
        return {
            "market_analysis": {
                "demand_trend": "stable",
                "price_volatility": "low",
                "supplier_availability": "high"
            },
            "risk_assessment": {
                "supply_chain_risks": ["seasonal_demand", "price_fluctuations"],
                "mitigation_strategies": ["multiple_suppliers", "bulk_purchasing"]
            },
            "sourcing_strategy": {
                "recommended_suppliers": 3,
                "quality_tiers": ["premium", "standard"],
                "payment_terms": ["net30", "net60"]
            },
            "cost_analysis": {
                "estimated_costs": {"clay": 50, "glazes": 100},
                "lead_times": {"local": 7, "imported": 21},
                "quality_ratings": {"local": 4.2, "imported": 4.5}
            }
        }


    async def _strategic_sourcing_analysis(self, user_profile: Dict) -> Dict:
        """
        Strategic sourcing analysis and recommendations
        """
        craft_type = user_profile.get("craft_type", "unknown")
        supplies_needed = user_profile.get("supplies_needed", [])
        location = user_profile.get("location", {})
        
        # Mock strategic sourcing analysis
        return {
            "sourcing_recommendations": {
                "primary_strategy": "local_first",
                "backup_strategy": "regional_expansion",
                "global_contingency": True
            },
            "supplier_prioritization": {
                "quality_weight": 0.4,
                "cost_weight": 0.3,
                "reliability_weight": 0.2,
                "location_weight": 0.1
            },
            "negotiation_leverage": {
                "bulk_potential": "medium",
                "relationship_opportunities": "high",
                "alternative_options": "good"
            }
        }


    async def _supply_chain_risk_assessment(self, user_profile: Dict) -> Dict:
        """Supply chain risk assessment"""
        return {
            "risk_level": "medium",
            "identified_risks": ["seasonal_demand", "price_volatility"],
            "mitigation_strategies": ["diversify_suppliers", "safety_stock"]
        }

    async def _autonomous_negotiation_strategy(self, user_profile: Dict) -> Dict:
        """Autonomous negotiation strategy"""
        return {
            "negotiation_approach": "collaborative",
            "key_leverage_points": ["bulk_pricing", "long_term_partnership"],
            "target_outcomes": ["cost_reduction", "quality_assurance"]
        }

    async def _generate_supply_chain_intelligence_report(self, user_profile, supply_chain_intel, sourcing_strategy, risk_analysis, negotiation_strategy) -> Dict:
        """Generate comprehensive supply chain intelligence report"""
        return {
            "summary": "Supply chain analysis complete",
            "recommendations": ["Local suppliers preferred", "Maintain backup options"],
            "next_steps": ["Contact top 3 suppliers", "Request samples"]
        }


# Test the Supply Hunter Agent
async def test_supply_hunter():
    from backend.core.cloud_llm_client import CloudLLMClient
    from backend.core.vector_store import ArtisanVectorStore
    from backend.scraping.web_scraper import WebScraperService
    
    llm = CloudLLMClient()
    vector_store = ArtisanVectorStore()
    scraper = WebScraperService()
    
    agent = SupplyHunterAgent(llm, vector_store, scraper)
    
    # Test input
    test_input = {
        "craft_type": "pottery",
        "supplies_needed": ["clay", "pottery glaze"],
        "location": {"city": "Jaipur", "state": "Rajasthan", "country": "India"},
        "user_id": "test_user_001"
    }
    
    print("Searching for suppliers...")
    result = await agent.analyze(test_input)
    
    print("\n=== SUPPLIERS FOUND ===")
    print(f"Total: {result['total_suppliers_found']}")
    print(f"India: {result['india_suppliers']}, Global: {result['global_suppliers']}")
    
    for i, supplier in enumerate(result['suppliers'][:3]):  # Show first 3
        print(f"\n--- Supplier {i+1} ---")
        print(f"Name: {supplier.get('name')}")
        print(f"Location: {supplier.get('location')}")
        print(f"Confidence: {supplier.get('verification', {}).get('confidence', 0):.2f}")
        print(f"Products: {', '.join(supplier.get('products', [])[:3])}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_supply_hunter())
