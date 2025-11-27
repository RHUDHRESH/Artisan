"""
Agent API endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List
from backend.core.ollama_client import OllamaClient
from backend.core.vector_store import ArtisanVectorStore
from backend.agents.profile_analyst import ProfileAnalystAgent
from backend.agents.supply_hunter import SupplyHunterAgent
from backend.agents.growth_marketer import GrowthMarketerAgent
from backend.agents.event_scout import EventScoutAgent
from backend.scraping.web_scraper import WebScraperService
from backend.services.maps_service import MapsService
from backend.agents.supervisor import SupervisorAgent
from backend.agents.framework.tools import default_tool_registry
from backend.services.local_store import LocalStore
from backend.constants import (
    MIN_QUERY_LENGTH, MAX_QUERY_LENGTH,
    MIN_PROFILE_NAME_LENGTH, MAX_PROFILE_NAME_LENGTH
)
from backend.config import settings
from backend.core.supabase_client import get_supabase_client
from loguru import logger

router = APIRouter(prefix="/agents", tags=["agents"])
local_store = LocalStore()
supabase_client = (
    get_supabase_client(settings.supabase_url, settings.supabase_key)
    if settings.supabase_url and settings.supabase_key
    else None
)


async def persist_results(search_type: str, user_id: str, results: List[Dict]):
    """Mirror recent items into Supabase when configured."""
    if not results or not supabase_client or not getattr(supabase_client, "enabled", False):
        return
    try:
        await supabase_client.save_search_results(user_id, search_type, results)
        if search_type == "suppliers":
            for supplier in results:
                await supabase_client.save_supplier(supplier)
    except Exception as exc:
        logger.debug(f"Supabase persistence skipped ({search_type}): {exc}")


async def fetch_recent_results(search_type: str, user_id: str, limit: int = 25) -> Optional[List[Dict]]:
    """Fetch recent search results from Supabase if available."""
    if not supabase_client or not getattr(supabase_client, "enabled", False):
        return None
    try:
        rows = await supabase_client.get_recent_searches(user_id, limit=limit)
        for row in rows:
            if row.get("search_type") == search_type:
                return row.get("results") or []
    except Exception as exc:
        logger.debug(f"Supabase fetch failed ({search_type}): {exc}")
    return None


async def ensure_llm_available() -> Dict[str, bool]:
    """Ensure at least one LLM provider is ready before dispatching agents."""
    async with OllamaClient() as client:
        statuses = await client.ensure_available()
    return statuses


class ProfileAnalysisRequest(BaseModel):
    """Request model for profile analysis with validation"""
    input_text: str = Field(
        ...,
        min_length=MIN_QUERY_LENGTH,
        max_length=MAX_QUERY_LENGTH,
        description="Profile information text from user"
    )
    user_id: Optional[str] = Field(
        None,
        min_length=MIN_PROFILE_NAME_LENGTH,
        max_length=MAX_PROFILE_NAME_LENGTH,
        description="Optional user identifier"
    )

    @field_validator('input_text')
    def validate_input_text(cls, v):
        """Ensure input_text is not empty after stripping"""
        if not v.strip():
            raise ValueError('input_text cannot be empty or whitespace only')
        return v


class SupplySearchRequest(BaseModel):
    """Request model for supply search with validation"""
    craft_type: str = Field(
        ...,
        min_length=MIN_PROFILE_NAME_LENGTH,
        max_length=MAX_PROFILE_NAME_LENGTH,
        description="Type of craft"
    )
    supplies_needed: Optional[List[str]] = Field(
        None,
        min_items=1,
        max_items=20,
        description="List of supplies needed. If not provided, will use crafts default supplies"
    )
    inferred_supplies: Optional[List[str]] = Field(
        None,
        description="Alternative field for supplies from profile analysis"
    )
    location: Dict[str, Any] = Field(
        ...,
        description="Location information (must contain 'city' or 'region')"
    )
    user_id: Optional[str] = Field(
        None,
        min_length=MIN_PROFILE_NAME_LENGTH,
        max_length=MAX_PROFILE_NAME_LENGTH
    )

    @field_validator('supplies_needed', mode='before')
    def normalize_supplies(cls, v):
        """Handle supplies_needed validation and normalization"""
        if v is None:
            return None
        if not isinstance(v, list):
            raise ValueError('supplies_needed must be a list')
        cleaned = []
        for supply in v:
            if isinstance(supply, str) and supply.strip():
                cleaned.append(supply.strip())
        if not cleaned and v:  # Had items but all empty
            raise ValueError('All supplies must be non-empty strings')
        return cleaned if cleaned else None

    @field_validator('craft_type', mode='before')
    def normalize_craft_type(cls, v):
        """Provide a safe default craft type when user input is too short."""
        if not isinstance(v, str) or len(v.strip()) < MIN_PROFILE_NAME_LENGTH:
            return "general craft"
        return v.strip()

    @field_validator('location')
    def validate_location(cls, v):
        """Ensure location has required fields"""
        if not isinstance(v, dict):
            return {"city": "Unknown", "country": "Unknown"}
        if not any(key in v for key in ['city', 'region', 'state']):
            return {**v, "city": v.get("city") or "Unknown"}
        return v

    def get_supplies_list(self) -> List[str]:
        """Get the supplies to use, with fallbacks"""
        supplies = self.supplies_needed or self.inferred_supplies
        if not supplies:
            # Default supplies based on craft_type
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
            supplies = craft_defaults.get(self.craft_type.lower(), ["raw materials", "tools", "supplies"])
        return supplies[:10]  # Limit to first 10


class GrowthAnalysisRequest(BaseModel):
    """Request model for growth analysis with validation"""
    craft_type: str = Field(
        ...,
        min_length=MIN_PROFILE_NAME_LENGTH,
        max_length=MAX_PROFILE_NAME_LENGTH
    )
    specialization: str = Field(
        ...,
        min_length=MIN_PROFILE_NAME_LENGTH,
        max_length=MAX_PROFILE_NAME_LENGTH
    )
    current_products: List[str] = Field(
        ...,
        min_items=1,
        max_items=20
    )
    location: Dict[str, Any] = Field(...)
    user_id: Optional[str] = Field(None)

    @field_validator('current_products')
    def validate_products(cls, v):
        """Ensure all products are non-empty strings"""
        for product in v:
            if not isinstance(product, str) or not product.strip():
                raise ValueError('All products must be non-empty strings')
        return v

    @field_validator('craft_type', 'specialization', mode='before')
    def normalize_text_fields(cls, v):
        """Coerce too-short text fields to a safe default to avoid 422s."""
        if not isinstance(v, str) or len(v.strip()) < MIN_PROFILE_NAME_LENGTH:
            return "general craft"
        return v.strip()

    @field_validator('location', mode='before')
    def normalize_location(cls, v):
        """Ensure location always contains a usable city/state payload."""
        if not isinstance(v, dict):
            return {"city": "Unknown", "state": "Unknown", "country": "Unknown"}
        if not any(key in v for key in ['city', 'region', 'state']):
            return {**v, "city": v.get("city") or "Unknown"}
        return v

    @field_validator('current_products', mode='before')
    def normalize_products(cls, v):
        """Provide fallback products when the list is missing or empty."""
        if not isinstance(v, list) or not v:
            return ["handmade items"]
        cleaned = [item.strip() for item in v if isinstance(item, str) and item.strip()]
        return cleaned or ["handmade items"]


class EventSearchRequest(BaseModel):
    """Request model for event search with validation"""
    craft_type: str = Field(
        ...,
        min_length=MIN_PROFILE_NAME_LENGTH,
        max_length=MAX_PROFILE_NAME_LENGTH
    )
    location: Dict[str, Any] = Field(...)
    travel_radius_km: Optional[int] = Field(
        100,
        ge=1,
        le=500,
        description="Travel radius in kilometers (1-500)"
    )
    user_id: Optional[str] = Field(None)


class SupervisedMissionRequest(BaseModel):
    """Request model for supervised mission with validation"""
    goal: str = Field(
        ...,
        min_length=MIN_QUERY_LENGTH,
        max_length=MAX_QUERY_LENGTH,
        description="Mission goal"
    )
    context: Optional[Dict[str, Any]] = Field(None)
    constraints: Optional[Dict[str, Any]] = Field(
        None,
        description="Constraints like max_steps and region_priority"
    )
    capabilities: Optional[List[str]] = Field(
        None,
        max_items=4,
        description="Subset of available agents to use"
    )

    @field_validator('goal')
    def validate_goal(cls, v):
        """Ensure goal is not empty after stripping"""
        if not v.strip():
            raise ValueError('goal cannot be empty or whitespace only')
        return v

    @field_validator('capabilities')
    def validate_capabilities(cls, v):
        """Ensure capabilities are valid agent names"""
        valid_agents = {
            'profile_analyst', 'supply_hunter',
            'growth_marketer', 'event_scout'
        }
        if v is not None:
            for cap in v:
                if cap not in valid_agents:
                    raise ValueError(
                        f"Invalid capability '{cap}'. "
                        f"Must be one of: {', '.join(valid_agents)}"
                    )
        return v


@router.post("/profile/analyze")
async def analyze_profile(request: ProfileAnalysisRequest):
    """
    Analyze artisan profile and infer needs
    """
    try:
        await ensure_llm_available()
        ollama = OllamaClient()
        vector_store = ArtisanVectorStore()
        
        agent = ProfileAnalystAgent(ollama, vector_store)
        
        result = await agent.analyze({
            "input_text": request.input_text,
            "user_id": request.user_id
        })
        
        return result
    except RuntimeError as e:
        logger.error(f"Profile analysis error: {e}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Profile analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/supply/search")
async def search_suppliers(request: SupplySearchRequest):
    """
    Search for suppliers based on artisan needs
    """
    try:
        await ensure_llm_available()
        ollama = OllamaClient()
        vector_store = ArtisanVectorStore()
        scraper = WebScraperService()
        
        agent = SupplyHunterAgent(ollama, vector_store, scraper)
        
        result = await agent.analyze({
            "craft_type": request.craft_type,
            "supplies_needed": request.get_supplies_list(),
            "location": request.location,
            "user_id": request.user_id
        })
        if isinstance(result, dict) and result.get("error"):
            raise HTTPException(
                status_code=400,
                detail=result
            )
        # Persist and normalize shape for UI
        try:
            user_id = request.user_id or "anonymous"
            suppliers = result.get("suppliers", [])
            local_store.save_suppliers(user_id, suppliers, context={
                "craft_type": request.craft_type,
                "location": request.location,
                "supplies_needed": request.supplies_needed,
            })
            # Also mirror into materials bucket for the Materials view
            local_store.save_materials(user_id, suppliers, context={
                "craft_type": request.craft_type,
                "location": request.location,
                "supplies_needed": request.supplies_needed,
            })
            await persist_results("suppliers", user_id, suppliers)
            await persist_results("materials", user_id, suppliers)
        except Exception as persist_err:
            logger.debug(f"Failed to persist suppliers: {persist_err}")

        # Also include a generic 'results' array for the generic view
        normalized = dict(result)
        normalized["results"] = result.get("suppliers", [])
        return normalized
    except RuntimeError as e:
        logger.error(f"Supply search error: {e}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Supply search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/growth/analyze")
async def analyze_growth(request: GrowthAnalysisRequest):
    """
    Analyze growth opportunities and market trends
    """
    try:
        await ensure_llm_available()
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
        if isinstance(result, dict) and result.get("error"):
            raise HTTPException(
                status_code=400,
                detail=result
            )
        # Normalize to a generic list and persist as opportunities
        try:
            # Build a list of highlights for UI
            combined: list = []
            for key in ("trends", "product_innovations", "marketing_channels"):
                val = result.get(key)
                if isinstance(val, list):
                    combined.extend(val)
            user_id = request.user_id or "anonymous"
            local_store.save_opportunities(user_id, combined, context={
                "craft_type": request.craft_type,
                "specialization": request.specialization,
                "location": request.location,
            })
            normalized = dict(result)
            normalized.setdefault("opportunities", combined)
            normalized.setdefault("results", combined)
            await persist_results("opportunities", user_id, combined)
            return normalized
        except Exception as persist_err:
            logger.debug(f"Failed to persist opportunities: {persist_err}")
            normalized = dict(result)
            normalized.setdefault("results", [])
            return normalized
    except RuntimeError as e:
        logger.error(f"Growth analysis error: {e}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Growth analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/events/search")
async def search_events(request: EventSearchRequest):
    """
    Search for events and opportunities
    """
    try:
        await ensure_llm_available()
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
        if isinstance(result, dict) and result.get("error"):
            raise HTTPException(
                status_code=400,
                detail=result
            )
        # Persist and normalize shape for UI
        try:
            events = result.get("upcoming_events", [])
            user_id = request.user_id or "anonymous"
            local_store.save_events(user_id, events, context={
                "craft_type": request.craft_type,
                "location": request.location,
                "travel_radius_km": request.travel_radius_km or 100,
            })
            normalized = dict(result)
            normalized.setdefault("events", events)
            normalized.setdefault("results", events)
            await persist_results("events", user_id, events)
            return normalized
        except Exception as persist_err:
            logger.debug(f"Failed to persist events: {persist_err}")
            normalized = dict(result)
            normalized.setdefault("results", [])
            return normalized
    except RuntimeError as e:
        logger.error(f"Event search error: {e}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Event search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/god-mode/intelligence")
async def god_mode_intelligence(request: SupervisedMissionRequest):
    """
    GOD MODE: Activate maximum intelligence - Full spectrum business analysis and automation

    Returns complete intelligence package including:
    - Market forecasting with predictive models
    - Competitive intelligence analysis
    - Automated workflow designs
    - Strategic recommendations with 3-year roadmap
    - Risk assessment and mitigation strategies
    - Performance optimization frameworks
    """
    try:
        await ensure_llm_available()
        ollama = OllamaClient()
        vector_store = ArtisanVectorStore()
        scraper = WebScraperService()
        maps = MapsService()

        supervisor = SupervisorAgent(ollama, vector_store, scraper, maps)

        result = await supervisor.analyze({
            "goal": request.goal,
            "context": request.context or {},
            "constraints": {
                **(request.constraints or {}),
                "max_steps": 10,  # Allow more complex operations
                "retries": 3,     # Higher reliability
                "step_timeout_s": 120  # More time for deep analysis
            },
            "capabilities": request.capabilities or ["profile_analyst", "supply_hunter", "growth_marketer", "event_scout"],
        })

        # Add GOD MODE branding to response
        god_response = {
            **result,
            "intelligence_mode": "GOD_MODE_OMEGA",
            "capabilities_engaged": [
                "Real-time market forecasting",
                "Competitive intelligence gathering",
                "Automated workflow design",
                "Predictive analytics modeling",
                "Strategic roadmap development",
                "Risk assessment & mitigation",
                "Performance optimization",
                "Business intelligence automation"
            ],
            "processing_time_god_units": "MAXIMUM",
            "confidence_level": "OMEGA_SUPREME"
        }

        return god_response
    except RuntimeError as e:
        logger.error(f"GOD MODE intelligence error: {e}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"GOD MODE intelligence error: {e}")
        raise HTTPException(status_code=500, detail=f"GOD MODE FAILURE: {str(e)}")

@router.post("/supervise/run")
async def run_supervised_mission(request: SupervisedMissionRequest):
    """
    Run a supervised mission: supervisor plans steps and dispatches to workers within constraints
    """
    try:
        await ensure_llm_available()
        ollama = OllamaClient()
        vector_store = ArtisanVectorStore()
        scraper = WebScraperService()
        maps = MapsService()

        supervisor = SupervisorAgent(ollama, vector_store, scraper, maps)

        result = await supervisor.analyze({
            "goal": request.goal,
            "context": request.context or {},
            "constraints": request.constraints or {},
            "capabilities": request.capabilities,
        })

        return result
    except RuntimeError as e:
        logger.error(f"Supervised mission error: {e}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Supervised mission error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools")
async def list_tools():
    """List available tools with input/output schemas"""
    try:
        registry = default_tool_registry()
        return {"tools": registry.list_tools()}
    except Exception as e:
        logger.error(f"List tools error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------- Recent items (local store) ----------------------

@router.get("/suppliers/recent")
async def get_recent_suppliers(user_id: Optional[str] = Query(None)):
    try:
        user = user_id or "anonymous"
        supabase_items = await fetch_recent_results("suppliers", user)
        items = supabase_items if supabase_items is not None else local_store.get_suppliers(user)
        return {"suppliers": items, "results": items}
    except Exception as e:
        logger.error(f"Get recent suppliers error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/opportunities/recent")
async def get_recent_opportunities(user_id: Optional[str] = Query(None)):
    try:
        user = user_id or "anonymous"
        supabase_items = await fetch_recent_results("opportunities", user)
        items = supabase_items if supabase_items is not None else local_store.get_opportunities(user)
        return {"opportunities": items, "results": items}
    except Exception as e:
        logger.error(f"Get recent opportunities error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events/recent")
async def get_recent_events(
    user_id: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None, description="YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="YYYY-MM-DD"),
):
    try:
        user = user_id or "anonymous"
        supabase_items = None
        if not any([city, date_from, date_to]):
            supabase_items = await fetch_recent_results("events", user)
        items = supabase_items if supabase_items is not None else local_store.get_events(user, city=city, date_from=date_from, date_to=date_to)
        return {"events": items, "results": items}
    except Exception as e:
        logger.error(f"Get recent events error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/materials/recent")
async def get_recent_materials(user_id: Optional[str] = Query(None)):
    try:
        user = user_id or "anonymous"
        supabase_items = await fetch_recent_results("materials", user)
        items = supabase_items if supabase_items is not None else local_store.get_materials(user)
        return {"materials": items, "results": items}
    except Exception as e:
        logger.error(f"Get recent materials error: {e}")
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
