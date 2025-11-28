"""
Event Scout Agent - Finds relevant events and opportunities
"""
from typing import Dict, List, Optional
from backend.agents.base_agent import BaseAgent
from loguru import logger
import json
from datetime import datetime


class EventScoutAgent(BaseAgent):
    """
    Event Scout Agent
    
    Responsibilities:
    1. Find craft fairs and exhibitions
    2. Discover relevant marketplaces
    3. Identify workshop opportunities
    4. Scout government schemes for artisans
    5. Match events to artisan's location and craft
    6. Calculate event ROI (booth cost vs potential revenue)
    7. Provide contact details for event organizers
    
    Uses: Gemma 3 4B for matching and analysis, 1B for classification
    """
    
    def __init__(self, cloud_llm_client, vector_store, scraper_service, maps_service):
        super().__init__(
            name="Event Scout",
            description="Finds relevant events and opportunities",
            cloud_llm_client=cloud_llm_client,
            vector_store=vector_store
        )
        self.scraper = scraper_service
        self.maps = maps_service
    
    async def analyze(self, user_profile: Dict) -> Dict:
        """
        Find events and opportunities for the artisan
        
        Input format:
        {
            "craft_type": "pottery",
            "location": {"city": "Jaipur", "state": "Rajasthan", "lat": 26.9, "lon": 75.8},
            "available_months": ["November", "December", "January"],
            "travel_radius_km": 100
        }
        
        Output format:
        {
            "upcoming_events": [...],
            "government_schemes": [...],
            "workshop_opportunities": [...],
            "total_events_found": 12,
            "events_within_radius": 8
        }
        """
        self.log_execution("start", {"location": user_profile.get("location")})
        
        craft_type = user_profile.get("craft_type", "")
        location = user_profile.get("location", {})
        travel_radius = user_profile.get("travel_radius_km", 100)

        # Fail fast when web search is unavailable
        if not getattr(self.scraper, "tavily_api_key", None) and not getattr(self.scraper, "serpapi_key", None):
            message = "Web search unavailable: add TAVILY_API_KEY (preferred) or SERPAPI_KEY to .env and restart the backend."
            self.log_execution("error", {"message": message, "provider": None})
            return {
                "upcoming_events": [],
                "government_schemes": [],
                "workshop_opportunities": [],
                "total_events_found": 0,
                "events_within_radius": 0,
                "error": {
                    "error": "missing_api_key",
                    "message": message,
                    "provider": None,
                    "action_required": True,
                },
                "execution_logs": self.get_logs(),
            }
        
        # Step 1: Search for upcoming craft fairs and exhibitions
        events = await self._search_events(craft_type, location, travel_radius)
        if isinstance(events, dict) and events.get("error"):
            return {
                "upcoming_events": [],
                "government_schemes": [],
                "workshop_opportunities": [],
                "total_events_found": 0,
                "events_within_radius": 0,
                "error": events["error"],
                "execution_logs": self.get_logs(),
            }
        
        # Step 2: Find government schemes
        schemes = await self._find_government_schemes(craft_type, location)
        if isinstance(schemes, dict) and schemes.get("error"):
            return {
                "upcoming_events": [],
                "government_schemes": [],
                "workshop_opportunities": [],
                "total_events_found": 0,
                "events_within_radius": 0,
                "error": schemes["error"],
                "execution_logs": self.get_logs(),
            }
        
        # Step 3: Discover workshop opportunities
        workshops = await self._find_workshops(craft_type, location)
        if isinstance(workshops, dict) and workshops.get("error"):
            return {
                "upcoming_events": [],
                "government_schemes": [],
                "workshop_opportunities": [],
                "total_events_found": 0,
                "events_within_radius": 0,
                "error": workshops["error"],
                "execution_logs": self.get_logs(),
            }
        
        # Step 4: Calculate ROI for each event
        for event in events:
            event["roi_analysis"] = await self._calculate_event_roi(event, craft_type)
        
        # Step 5: Sort by relevance and proximity
        events.sort(
            key=lambda x: (
                x.get("relevance_score", 0) * 0.7 + 
                (1 - min(x.get("distance_km", 500) / travel_radius, 1)) * 0.3
            ),
            reverse=True
        )
        
        within_radius = sum(1 for e in events if e.get("distance_km", 0) <= travel_radius)
        
        self.log_execution("complete", {
            "events_found": len(events),
            "within_radius": within_radius
        })
        
        return {
            "upcoming_events": events,
            "government_schemes": schemes,
            "workshop_opportunities": workshops,
            "total_events_found": len(events),
            "events_within_radius": within_radius,
            "execution_logs": self.get_logs()
        }
    
    async def _search_events(
        self,
        craft_type: str,
        location: Dict,
        radius_km: int
    ) -> List[Dict] | Dict:
        """Search for craft events"""
        self.log_execution("searching_events", {"craft": craft_type, "location": location})
        
        city = location.get("city", "")
        state = location.get("state", "")
        
        # Build search queries
        current_year = datetime.now().year
        next_year = current_year + 1
        
        queries = [
            f"craft fair {city} {state} {current_year}",
            f"{craft_type} exhibition India {current_year}",
            f"artisan market {state} upcoming",
            f"handicraft mela {city} {current_year}",
            f"dilli haat {state} schedule",
            f"{craft_type} festival India {next_year}"
        ]
        
        all_events = []
        
        for query in queries:
            results = await self.scraper.search(query, region="in", num_results=5)
            if isinstance(results, dict) and results.get("error"):
                self.log_execution("error", {
                    "step": "web_search",
                    "query": query,
                    "error": results.get("error"),
                    "message": results.get("message"),
                })
                return {"error": results}
            
            for result in results:
                # Scrape event details
                content = await self.scraper.scrape_page(result['url'])
                
                if not content:
                    continue
                
                # Extract event information with LLM
                event_prompt = f"""Extract event information from this webpage:

URL: {result['url']}
Title: {result['title']}
Content: {content[:1500]}

Extract in JSON format:
{{
    "name": "event name",
    "type": "craft_fair/exhibition/market/festival/workshop",
    "date": "YYYY-MM-DD or date range",
    "location": {{
        "city": "",
        "venue": "",
        "address": ""
    }},
    "booth_cost": "cost information if mentioned",
    "expected_footfall": "attendance numbers if mentioned",
    "organizer": "organizer name",
    "contact": {{
        "phone": "",
        "email": "",
        "website": "{result['url']}"
    }},
    "booking_deadline": "deadline if mentioned",
    "description": "brief description"
}}

If this is not an event page, return {{"name": null}}
Return ONLY valid JSON."""

                event_result = await self.ollama.reasoning_task(event_prompt)
                
                try:
                    if "```json" in event_result:
                        event_result = event_result.split("```json")[1].split("```")[0]
                    elif "```" in event_result:
                        event_result = event_result.split("```")[1].split("```")[0]
                    event_data = json.loads(event_result.strip())
                    
                    if event_data.get("name"):
                        # Calculate distance
                        event_location = event_data.get("location", {})
                        distance = await self.maps.calculate_distance(
                            location,
                            event_location
                        )
                        
                        event_data["distance_km"] = distance
                        
                        # Calculate relevance score
                        relevance = await self._calculate_event_relevance(
                            event_data,
                            craft_type
                        )
                        event_data["relevance_score"] = relevance
                        
                        # Add source
                        event_data["source_url"] = result['url']
                        event_data["scraped_at"] = self._get_timestamp()
                        
                        all_events.append(event_data)
                except Exception as e:
                    logger.debug(f"Failed to parse event from {result['url']}: {e}")
                    continue
        
        # Deduplicate by name
        unique_events = self._deduplicate_events(all_events)
        
        return unique_events
    
    async def _find_government_schemes(self, craft_type: str, location: Dict) -> List[Dict] | Dict:
        """Find government schemes for artisans"""
        self.log_execution("finding_schemes", {"craft": craft_type})
        
        queries = [
            "government scheme for artisans India 2025",
            f"{craft_type} artisan subsidy India",
            "PM Vishwakarma Yojana benefits",
            "handicraft artisan financial support India"
        ]
        
        schemes = []
        
        for query in queries:
            results = await self.scraper.search(query, region="in", num_results=3)
            if isinstance(results, dict) and results.get("error"):
                self.log_execution("error", {
                    "step": "web_search",
                    "query": query,
                    "error": results.get("error"),
                    "message": results.get("message"),
                })
                return {"error": results}
            
            for result in results[:2]:
                content = await self.scraper.scrape_page(result['url'])
                
                if not content:
                    continue
                
                scheme_prompt = f"""Extract government scheme information:

Content: {content[:1000]}

Extract in JSON format:
{{
    "scheme_name": "name of scheme",
    "benefits": ["list of benefits"],
    "eligibility": "who can apply",
    "how_to_apply": "application process",
    "contact": "contact information",
    "deadline": "application deadline if any"
}}

If no scheme found, return {{"scheme_name": null}}
Return ONLY valid JSON."""

                result_text = await self.ollama.reasoning_task(scheme_prompt)
                
                try:
                    if "```json" in result_text:
                        result_text = result_text.split("```json")[1].split("```")[0]
                    elif "```" in result_text:
                        result_text = result_text.split("```")[1].split("```")[0]
                    scheme_data = json.loads(result_text.strip())
                    
                    if scheme_data.get("scheme_name"):
                        scheme_data["source"] = result['url']
                        schemes.append(scheme_data)
                except Exception as e:
                    logger.debug(f"Failed to parse scheme: {e}")
                    continue
        
        # Deduplicate
        unique_schemes = self._deduplicate_schemes(schemes)
        return unique_schemes[:5]
    
    async def _find_workshops(self, craft_type: str, location: Dict) -> List[Dict] | Dict:
        """Find workshop and teaching opportunities"""
        self.log_execution("finding_workshops", {"craft": craft_type})
        
        # Similar implementation to events search but focused on workshops
        queries = [
            f"{craft_type} workshop {location.get('city', '')}",
            f"{craft_type} teaching opportunity India",
            f"{craft_type} artisan training program"
        ]
        
        workshops = []
        
        for query in queries:
            results = await self.scraper.search(query, region="in", num_results=3)
            if isinstance(results, dict) and results.get("error"):
                self.log_execution("error", {
                    "step": "web_search",
                    "query": query,
                    "error": results.get("error"),
                    "message": results.get("message"),
                })
                return {"error": results}
            
            for result in results[:2]:
                content = await self.scraper.scrape_page(result['url'])
                
                if content:
                    # Similar extraction as events
                    workshops.append({
                        "name": result.get('title', ''),
                        "url": result['url'],
                        "type": "workshop"
                    })
        
        return workshops[:3]
    
    async def _calculate_event_relevance(self, event: Dict, craft_type: str) -> float:
        """Calculate how relevant the event is to the artisan"""
        relevance = 0.5  # Base score
        
        # Check event type
        event_type = event.get("type", "").lower()
        event_name = event.get("name", "").lower()
        
        if craft_type.lower() in event_name:
            relevance += 0.3
        
        if event_type in ["craft_fair", "artisan_market", "exhibition"]:
            relevance += 0.2
        
        # Check description for craft keywords
        description = event.get("description", "").lower()
        if craft_type.lower() in description:
            relevance += 0.1
        
        return min(1.0, relevance)
    
    async def _calculate_event_roi(self, event: Dict, craft_type: str) -> Dict:
        """Calculate expected ROI for attending event"""
        roi_prompt = f"""Calculate ROI for attending this event:

Event: {event.get('name')}
Type: {event.get('type')}
Booth Cost: {event.get('booth_cost', 'Unknown')}
Expected Footfall: {event.get('expected_footfall', 'Unknown')}
Craft Type: {craft_type}

Estimate in JSON:
{{
    "total_cost": {{
        "booth_rental": 0,
        "travel": 0,
        "accommodation": 0,
        "inventory": 0,
        "total": 0
    }},
    "revenue_estimate": {{
        "conservative": 0,
        "realistic": 0,
        "optimistic": 0
    }},
    "break_even_units": 0,
    "recommendation": "Attend/Maybe/Skip with reasoning"
}}

Amounts in Rs. Return ONLY valid JSON."""

        result = await self.ollama.reasoning_task(roi_prompt)
        
        try:
            if "```json" in result:
                result = result.split("```json")[1].split("```")[0]
            elif "```" in result:
                result = result.split("```")[1].split("```")[0]
            roi_data = json.loads(result.strip())
            return roi_data
        except Exception as e:
            logger.debug(f"Failed to calculate ROI: {e}")
            return {"error": "Could not calculate ROI"}
    
    def _deduplicate_events(self, events: List[Dict]) -> List[Dict]:
        """Remove duplicate events by name and date"""
        seen = set()
        unique = []
        
        for event in events:
            key = f"{event.get('name', '')}_{event.get('date', '')}"
            key_lower = key.lower()
            if key_lower not in seen:
                seen.add(key_lower)
                unique.append(event)
        
        return unique
    
    def _deduplicate_schemes(self, schemes: List[Dict]) -> List[Dict]:
        """Remove duplicate schemes by name"""
        seen = set()
        unique = []
        
        for scheme in schemes:
            name = scheme.get('scheme_name', '').lower()
            if name and name not in seen:
                seen.add(name)
                unique.append(scheme)
        
        return unique


# Test the Event Scout Agent
async def test_event_scout():
    from core.cloud_llm_client import CloudLLMClient
    from core.vector_store import ArtisanVectorStore
    from scraping.web_scraper import WebScraperService
    from services.maps_service import MapsService
    
    llm = CloudLLMClient()
    vector_store = ArtisanVectorStore()
    scraper = WebScraperService()
    maps = MapsService()
    
    agent = EventScoutAgent(llm, vector_store, scraper, maps)
    
    # Test input
    test_input = {
        "craft_type": "pottery",
        "location": {
            "city": "Jaipur",
            "state": "Rajasthan",
            "country": "India"
        },
        "travel_radius_km": 100,
        "user_id": "test_user_001"
    }
    
    print("Scouting for events...")
    result = await agent.analyze(test_input)
    
    print(f"\n=== EVENTS FOUND: {result['total_events_found']} ===")
    print(f"Within radius: {result['events_within_radius']}")
    
    for i, event in enumerate(result['upcoming_events'][:3]):
        print(f"\n{i+1}. {event.get('name', 'Unknown')}")
        print(f"   Date: {event.get('date', 'TBD')}")
        print(f"   Location: {event.get('location', {}).get('city', 'Unknown')}")
        print(f"   Distance: {event.get('distance_km', 0)} km")
        print(f"   Relevance: {event.get('relevance_score', 0):.2f}")
    
    if result['government_schemes']:
        print(f"\n=== GOVERNMENT SCHEMES: {len(result['government_schemes'])} ===")
        for scheme in result['government_schemes']:
            print(f"\n- {scheme.get('scheme_name', 'Unknown')}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_event_scout())
