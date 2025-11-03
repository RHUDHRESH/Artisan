"""
Agent API endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from backend.core.ollama_client import OllamaClient
from backend.core.vector_store import ArtisanVectorStore
from backend.agents.profile_analyst import ProfileAnalystAgent
from backend.agents.supply_hunter import SupplyHunterAgent
from backend.agents.growth_marketer import GrowthMarketerAgent
from backend.agents.event_scout import EventScoutAgent
from backend.scraping.web_scraper import WebScraperService
from backend.services.maps_service import MapsService
from loguru import logger

router = APIRouter(prefix="/agents", tags=["agents"])


class ProfileAnalysisRequest(BaseModel):
    input_text: str
    user_id: Optional[str] = None


class SupplySearchRequest(BaseModel):
    craft_type: str
    supplies_needed: List[str]
    location: Dict[str, Any]
    user_id: Optional[str] = None


class GrowthAnalysisRequest(BaseModel):
    craft_type: str
    specialization: str
    current_products: List[str]
    location: Dict[str, Any]
    user_id: Optional[str] = None


class EventSearchRequest(BaseModel):
    craft_type: str
    location: Dict[str, Any]
    travel_radius_km: Optional[int] = 100
    user_id: Optional[str] = None


@router.post("/profile/analyze")
async def analyze_profile(request: ProfileAnalysisRequest):
    """
    Analyze artisan profile and infer needs
    """
    try:
        ollama = OllamaClient()
        vector_store = ArtisanVectorStore()
        
        agent = ProfileAnalystAgent(ollama, vector_store)
        
        result = await agent.analyze({
            "input_text": request.input_text,
            "user_id": request.user_id
        })
        
        return result
    except Exception as e:
        logger.error(f"Profile analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/supply/search")
async def search_suppliers(request: SupplySearchRequest):
    """
    Search for suppliers based on artisan needs
    """
    try:
        ollama = OllamaClient()
        vector_store = ArtisanVectorStore()
        scraper = WebScraperService()
        
        agent = SupplyHunterAgent(ollama, vector_store, scraper)
        
        result = await agent.analyze({
            "craft_type": request.craft_type,
            "supplies_needed": request.supplies_needed,
            "location": request.location,
            "user_id": request.user_id
        })
        
        return result
    except Exception as e:
        logger.error(f"Supply search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/growth/analyze")
async def analyze_growth(request: GrowthAnalysisRequest):
    """
    Analyze growth opportunities and market trends
    """
    try:
        ollama = OllamaClient()
        vector_store = ArtisanVectorStore()
        scraper = WebScraperService()
        
        agent = GrowthMarketerAgent(ollama, vector_store, scraper)
        
        result = await agent.analyze({
            "craft_type": request.craft_type,
            "specialization": request.specialization,
            "current_products": request.current_products,
            "location": request.location,
            "user_id": request.user_id
        })
        
        return result
    except Exception as e:
        logger.error(f"Growth analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/events/search")
async def search_events(request: EventSearchRequest):
    """
    Search for events and opportunities
    """
    try:
        ollama = OllamaClient()
        vector_store = ArtisanVectorStore()
        scraper = WebScraperService()
        maps = MapsService()
        
        agent = EventScoutAgent(ollama, vector_store, scraper, maps)
        
        result = await agent.analyze({
            "craft_type": request.craft_type,
            "location": request.location,
            "travel_radius_km": request.travel_radius_km or 100,
            "user_id": request.user_id
        })
        
        return result
    except Exception as e:
        logger.error(f"Event search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Alternative endpoints matching next.md specification
@router.post("/profile-analyst")
async def profile_analyst(request: ProfileAnalysisRequest):
    """Alternative endpoint matching next.md"""
    return await analyze_profile(request)


@router.post("/supply-hunter")
async def supply_hunter(request: SupplySearchRequest):
    """Alternative endpoint matching next.md"""
    return await search_suppliers(request)


@router.post("/growth-marketer")
async def growth_marketer(request: GrowthAnalysisRequest):
    """Alternative endpoint matching next.md"""
    return await analyze_growth(request)

