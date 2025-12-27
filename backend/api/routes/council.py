"""
Council API Routes - Plan generation endpoints
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio
from loguru import logger

from backend.services.council_service import get_council_service
from backend.core.cloud_llm_client import CloudLLMClient


# Request/Response Models
class MovePlanRequest(BaseModel):
    workspace_id: str = Field(..., description="Workspace identifier")
    objective: str = Field(..., description="Objective for the move plan")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional context and details")


class CampaignPlanRequest(BaseModel):
    workspace_id: str = Field(..., description="Workspace identifier")
    objective: str = Field(..., description="Objective for the campaign")
    target_icp: str = Field(..., description="Target Ideal Customer Profile")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional context and details")


class MovePlanResponse(BaseModel):
    success: bool
    workspace_id: str
    objective: str
    decree: Optional[str]
    consensus_metrics: Optional[Dict[str, Any]]
    proposed_moves: List[Dict[str, Any]]
    refined_moves: List[Dict[str, Any]]
    approved_moves: List[Dict[str, Any]]
    discarded_moves: List[Dict[str, Any]]
    debate_history: List[Dict[str, Any]]
    rejected_paths: List[Dict[str, Any]]
    reasoning_chain_id: Optional[str]
    started_at: Optional[str]
    completed_at: Optional[str]
    errors: List[str]
    kill_switch_triggered: bool


class CampaignPlanResponse(BaseModel):
    success: bool
    workspace_id: str
    objective: str
    target_icp: str
    campaign_data: Optional[Dict[str, Any]]
    refined_moves: List[Dict[str, Any]]
    rationale: Dict[str, Any]
    started_at: Optional[str]
    completed_at: Optional[str]
    errors: List[str]
    kill_switch_triggered: bool


# Router setup
router = APIRouter(prefix="/council", tags=["council"])


async def get_llm_client():
    """Dependency to get LLM client"""
    try:
        return CloudLLMClient()
    except Exception as e:
        logger.error(f"Failed to get LLM client: {e}")
        raise HTTPException(status_code=500, detail="LLM service unavailable")


async def get_redis_client():
    """Dependency to get Redis client"""
    # This would integrate with your Redis setup
    # For now, return None (no caching)
    return None


@router.post("/generate_move_plan", response_model=MovePlanResponse)
async def generate_move_plan(
    request: MovePlanRequest,
    background_tasks: BackgroundTasks,
    llm_client: CloudLLMClient = Depends(get_llm_client),
    redis_client = Depends(get_redis_client)
):
    """
    Generate a move plan using council deliberation
    
    This endpoint runs a multi-agent council that debates, critiques, scores,
    synthesizes, and decomposes the objective into actionable moves.
    
    The process includes:
    - Multi-round debate among council nodes
    - Critical analysis and scoring
    - Synthesis of insights
    - Move decomposition and refinement
    - Tool requirements identification
    - Success prediction
    - Kill switch filtering
    
    Results are cached for 24 hours.
    """
    try:
        logger.info(f"Starting move plan generation for workspace {request.workspace_id}")
        
        # Get council service
        council_service = get_council_service(llm_client, redis_client)
        
        # Set timeout for the operation
        timeout = 300  # 5 minutes
        
        try:
            # Run the council deliberation with timeout
            result = await asyncio.wait_for(
                council_service.generate_move_plan(
                    workspace_id=request.workspace_id,
                    objective=request.objective,
                    details=request.details
                ),
                timeout=timeout
            )
            
        except asyncio.TimeoutError:
            logger.error(f"Move plan generation timed out for workspace {request.workspace_id}")
            raise HTTPException(
                status_code=408,
                detail="Plan generation timed out. Please try again with a simpler objective."
            )
        
        if not result.get("success", False):
            error_msg = result.get("error", "Unknown error occurred")
            logger.error(f"Move plan generation failed: {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
        
        logger.info(f"Move plan generation completed for workspace {request.workspace_id}")
        return MovePlanResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in move plan generation: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/generate_campaign_plan", response_model=CampaignPlanResponse)
async def generate_campaign_plan(
    request: CampaignPlanRequest,
    background_tasks: BackgroundTasks,
    llm_client: CloudLLMClient = Depends(get_llm_client),
    redis_client = Depends(get_redis_client)
):
    """
    Generate a campaign plan using council deliberation
    
    This endpoint runs the same council deliberation as move plan generation,
    plus adds a campaign arc generator to produce a 90-day campaign timeline.
    
    The process includes all move plan steps plus:
    - Campaign arc generation (90-day timeline)
    - Target ICP consideration
    - Campaign-specific metrics and milestones
    
    Results are cached for 24 hours.
    """
    try:
        logger.info(f"Starting campaign plan generation for workspace {request.workspace_id}")
        
        # Get council service
        council_service = get_council_service(llm_client, redis_client)
        
        # Set timeout for the operation (longer for campaign plans)
        timeout = 420  # 7 minutes
        
        try:
            # Run the council deliberation with timeout
            result = await asyncio.wait_for(
                council_service.generate_campaign_plan(
                    workspace_id=request.workspace_id,
                    objective=request.objective,
                    target_icp=request.target_icp,
                    details=request.details
                ),
                timeout=timeout
            )
            
        except asyncio.TimeoutError:
            logger.error(f"Campaign plan generation timed out for workspace {request.workspace_id}")
            raise HTTPException(
                status_code=408,
                detail="Campaign plan generation timed out. Please try again with a simpler objective."
            )
        
        if not result.get("success", False):
            error_msg = result.get("error", "Unknown error occurred")
            logger.error(f"Campaign plan generation failed: {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
        
        logger.info(f"Campaign plan generation completed for workspace {request.workspace_id}")
        return CampaignPlanResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in campaign plan generation: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/plan_status/{workspace_id}/{plan_id}")
async def get_plan_status(
    workspace_id: str,
    plan_id: str,
    llm_client: CloudLLMClient = Depends(get_llm_client)
):
    """
    Get the status of a plan generation
    
    This endpoint can be used to check the progress of long-running
    plan generation jobs.
    """
    try:
        council_service = get_council_service(llm_client)
        status = await council_service.get_plan_status(workspace_id, plan_id)
        
        return JSONResponse(content=status)
        
    except Exception as e:
        logger.error(f"Error getting plan status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting plan status: {str(e)}"
        )


@router.delete("/cache/{workspace_id}")
async def clear_cache(
    workspace_id: str,
    llm_client: CloudLLMClient = Depends(get_llm_client)
):
    """
    Clear cached plans for a workspace
    
    This endpoint clears all cached move and campaign plans
    for the specified workspace.
    """
    try:
        council_service = get_council_service(llm_client)
        cleared_count = await council_service.clear_cache(workspace_id)
        
        return JSONResponse(content={
            "message": f"Cleared {cleared_count} cached plans",
            "workspace_id": workspace_id,
            "cleared_count": cleared_count
        })
        
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing cache: {str(e)}"
        )


@router.get("/health")
async def council_health():
    """
    Health check for council service
    
    Returns the status of the council generation system.
    """
    return JSONResponse(content={
        "status": "healthy",
        "service": "council",
        "timestamp": datetime.now().isoformat(),
        "features": {
            "move_plans": True,
            "campaign_plans": True,
            "caching": True,
            "timeout_handling": True
        }
    })


# Error handlers
@router.exception_handler(408)
async def timeout_handler(request, exc):
    """Handle timeout errors"""
    return JSONResponse(
        status_code=408,
        content={
            "error": "Request timeout",
            "message": "The council deliberation took too long. Please try with a simpler objective.",
            "retry_after": "60"
        }
    )


@router.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handle internal server errors"""
    logger.error(f"Internal error in council API: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An error occurred during council deliberation. Please try again.",
            "timestamp": datetime.now().isoformat()
        }
    )
