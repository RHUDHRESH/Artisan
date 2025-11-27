"""
Supply Hunter Agent - Finds and verifies suppliers for artisan materials
"""
from typing import Dict, List, Optional
from backend.agents.base_agent import BaseAgent
from loguru import logger
import json


class SupplyHunterAgent(BaseAgent):
    """
    Supply Hunter Agent
    
    Responsibilities:
    1. Search for suppliers based on inferred needs
    2. Scrape supplier websites for details
    3. Extract pricing information
    4. Analyze reviews and ratings
    5. Verify legitimacy through cross-referencing
    6. Calculate logistics (distance, delivery time)
    7. Maintain detailed search logs
    
    Search Priority:
    1. India (mandatory first)
    2. Regional (Asia) if needed
    3. Global only if unavailable in India/Asia
    
    Uses: Gemma 3 4B for analysis, 1B for classification
    """
    
    def __init__(self, ollama_client, vector_store, scraper_service):
        super().__init__(
            name="Supply Hunter",
            description="Finds and verifies suppliers for artisan materials",
            ollama_client=ollama_client,
            vector_store=vector_store
        )
        self.scraper = scraper_service
    
    async def analyze(self, user_profile: Dict) -> Dict:
        """
        Find suppliers for the artisan
        
        Input format:
        {
            "craft_type": "pottery",
            "supplies_needed": ["clay", "glazes", "pigments"],
            "location": {"city": "Jaipur", "state": "Rajasthan"},
            "budget_range": "mid" (optional)
        }
        
        Output format:
        {
            "suppliers": [...],
            "search_logs": [...],
            "total_suppliers_found": 5,
            "india_suppliers": 4,
            "global_suppliers": 1
        }
        """
        self.log_execution("start", {"supplies_needed": user_profile.get("supplies_needed", [])})
        
        supplies = user_profile.get("supplies_needed", [])
        location = user_profile.get("location", {})
        craft_type = user_profile.get("craft_type", "")
        
        all_suppliers = []
        search_logs = []
        
        # Search for each supply
        for supply in supplies:
            self.log_execution("searching_supply", {"supply": supply})
            
            # Step 1: Search in India first (MANDATORY)
            india_results = await self._search_suppliers_india(
                supply_name=supply,
                craft_type=craft_type,
                location=location
            )
            search_logs.extend(india_results.get("search_logs", []))

            # If search failed (e.g., missing API key), stop early with clear guidance
            if india_results.get("error"):
                error_info = india_results["error"]
                self.log_execution("error", {
                    "message": error_info.get("message", "Web search unavailable"),
                    "provider": error_info.get("provider"),
                })
                return {
                    "suppliers": [],
                    "search_logs": search_logs,
                    "total_suppliers_found": 0,
                    "india_suppliers": 0,
                    "global_suppliers": 0,
                    "error": error_info,
                    "execution_logs": self.get_logs()
                }
            
            # Step 2: If insufficient results, search regionally
            if len(india_results["suppliers"]) < 3:
                self.log_execution("expanding_search", {"reason": "insufficient_india_results"})
                regional_results = await self._search_suppliers_regional(
                    supply_name=supply,
                    craft_type=craft_type
                )
                india_results["suppliers"].extend(regional_results["suppliers"])
                search_logs.extend(regional_results["search_logs"])
            
            # Step 3: Verify each supplier
            verified_suppliers = []
            total_to_verify = min(5, len(india_results["suppliers"]))
            self.log_execution("thinking", {"message": f"Now verifying {total_to_verify} suppliers for {supply}..."})

            for supplier in india_results["suppliers"][:5]:  # Top 5
                verification = await self._verify_supplier(supplier)
                supplier["verification"] = verification

                if verification["confidence"] > 0.6:  # Only include if confidence > 60%
                    verified_suppliers.append(supplier)
                    self.log_execution("thinking", {"message": f"✓ {supplier.get('name', 'Supplier')} verified with {verification['confidence']:.0%} confidence"})
                else:
                    self.log_execution("thinking", {"message": f"⚠️ {supplier.get('name', 'Supplier')} failed verification (confidence: {verification['confidence']:.0%})"})

            all_suppliers.extend(verified_suppliers)
        
        # Count India vs global suppliers
        india_count = sum(1 for s in all_suppliers if s.get("location", {}).get("country") == "India")
        global_count = len(all_suppliers) - india_count
        
        self.log_execution("complete", {
            "total_found": len(all_suppliers),
            "india_suppliers": india_count,
            "global_suppliers": global_count
        })
        
        return {
            "suppliers": all_suppliers,
            "search_logs": search_logs,
            "total_suppliers_found": len(all_suppliers),
            "india_suppliers": india_count,
            "global_suppliers": global_count,
            "execution_logs": self.get_logs()
        }
    
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
            f"{craft_type} {supply_name} wholesale {state}",
            f"buy {supply_name} for {craft_type} {city}",
            f"{supply_name} manufacturers India {state}"
        ]
        
        all_results = []
        search_logs = []
        
        for query in queries:
            self.log_execution("web_search", {"query": query, "region": "India"})

            # Call scraper service to search
            results = await self.scraper.search(
                query=query,
                region="in",  # India
                num_results=10
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
                supplier_data = await self._parse_supplier_page(result)
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
                return None

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

            result = await self.ollama.reasoning_task(extraction_prompt)
            
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
            except:
                logger.error(f"Failed to parse supplier data from {url}")
                return None
        
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return None
    
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


# Test the Supply Hunter Agent
async def test_supply_hunter():
    from backend.core.ollama_client import OllamaClient
    from backend.core.vector_store import ArtisanVectorStore
    from backend.scraping.web_scraper import WebScraperService
    
    ollama = OllamaClient()
    vector_store = ArtisanVectorStore()
    scraper = WebScraperService()
    
    agent = SupplyHunterAgent(ollama, vector_store, scraper)
    
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
