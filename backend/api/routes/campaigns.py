"""
Campaign and Move CRUD API Routes
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import uuid
from loguru import logger

from backend.database_models import Campaign, Move, Task, DailyMetrics, CampaignStatus, MoveStatus
from backend.core.supabase_client import get_supabase_client


# Request/Response Models
class CampaignCreateRequest(BaseModel):
    workspace_id: str = Field(..., description="Workspace identifier")
    title: str = Field(..., description="Campaign title")
    objective: str = Field(..., description="Campaign objective")
    target_icp: Optional[str] = Field(None, description="Target Ideal Customer Profile")
    arc_data: Optional[Dict[str, Any]] = Field(None, description="90-day campaign arc data")


class CampaignUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, description="Campaign title")
    objective: Optional[str] = Field(None, description="Campaign objective")
    status: Optional[CampaignStatus] = Field(None, description="Campaign status")
    target_icp: Optional[str] = Field(None, description="Target Ideal Customer Profile")
    arc_data: Optional[Dict[str, Any]] = Field(None, description="90-day campaign arc data")


class CampaignResponse(BaseModel):
    id: str
    workspace_id: str
    title: str
    objective: str
    status: str
    target_icp: Optional[str]
    arc_data: Optional[Dict[str, Any]]
    created_at: str
    updated_at: str
    completed_at: Optional[str]
    total_moves: int
    completed_moves: int
    success_rate: float
    moves_summary: List[Dict[str, Any]]  # Summary of moves


class CampaignListResponse(BaseModel):
    campaigns: List[CampaignResponse]
    total: int
    page: int
    per_page: int


class MoveCreateRequest(BaseModel):
    workspace_id: str = Field(..., description="Workspace identifier")
    campaign_id: Optional[str] = Field(None, description="Campaign ID (optional for standalone moves)")
    name: str = Field(..., description="Move name")
    description: str = Field(..., description="Move description")
    tool_requirements: Optional[List[str]] = Field(default_factory=list, description="Tool requirements")
    muse_prompt: Optional[str] = Field(None, description="MUSE prompt for execution")
    confidence: Optional[float] = Field(0.0, description="Confidence score")
    success_prediction: Optional[float] = Field(0.0, description="Success prediction")
    risk_score: Optional[float] = Field(0.0, description="Risk score")
    due_date: Optional[datetime] = Field(None, description="Due date")


class MoveUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, description="Move name")
    description: Optional[str] = Field(None, description="Move description")
    status: Optional[MoveStatus] = Field(None, description="Move status")
    confidence: Optional[float] = Field(None, description="Confidence score")
    tool_requirements: Optional[List[str]] = Field(None, description="Tool requirements")
    muse_prompt: Optional[str] = Field(None, description="MUSE prompt")
    success_prediction: Optional[float] = Field(None, description="Success prediction")
    risk_score: Optional[float] = Field(None, description="Risk score")
    due_date: Optional[datetime] = Field(None, description="Due date")
    started_at: Optional[datetime] = Field(None, description="Start date")
    completed_at: Optional[datetime] = Field(None, description="Completion date")


class MoveResponse(BaseModel):
    id: str
    workspace_id: str
    campaign_id: Optional[str]
    name: str
    description: str
    status: str
    confidence: float
    tool_requirements: List[str]
    muse_prompt: Optional[str]
    success_prediction: float
    risk_score: float
    reasoning_chain_id: Optional[str]
    refinement_data: Optional[Dict[str, Any]]
    assets: List[Dict[str, Any]]
    rag: Optional[Dict[str, Any]]
    started_at: Optional[str]
    completed_at: Optional[str]
    due_date: Optional[str]
    created_at: str
    updated_at: str
    created_by: Optional[str]
    proposed_by: Optional[str]
    order_index: int
    tasks: List[Dict[str, Any]]
    daily_metrics: List[Dict[str, Any]]
    campaign_tag: Optional[str]  # Generated tag for frontend display


class MoveListResponse(BaseModel):
    moves: List[MoveResponse]
    total: int
    page: int
    per_page: int


# Router setup
router = APIRouter(prefix="/campaigns", tags=["campaigns", "moves"])


# Helper functions
def generate_campaign_tag(campaign: Campaign) -> str:
    """Generate a unique tag for frontend display"""
    return f"#{campaign.id[:8].upper()}"


def generate_move_tag(move: Move) -> str:
    """Generate a unique tag for frontend display"""
    if move.campaign_id:
        return f"#{move.campaign_id[:4].upper()}-{move.id[:4].upper()}"
    return f"#{move.id[:8].upper()}"


async def verify_workspace_access(workspace_id: str, user_id: Optional[str] = None) -> bool:
    """Verify user has access to workspace"""
    # This would integrate with your auth system
    # For now, return True (no auth)
    return True


# Campaign Endpoints

@router.post("/", response_model=CampaignResponse)
async def create_campaign(
    request: CampaignCreateRequest,
    user_id: Optional[str] = None,
    supabase = Depends(get_supabase_client)
):
    """
    Create a new campaign
    
    Creates a campaign with the given details and returns the created campaign.
    """
    try:
        # Verify workspace access
        if not await verify_workspace_access(request.workspace_id, user_id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Create campaign
        campaign = Campaign(
            id=str(uuid.uuid4()),
            workspace_id=request.workspace_id,
            title=request.title,
            objective=request.objective,
            target_icp=request.target_icp,
            arc_data=request.arc_data,
            status=CampaignStatus.DRAFT,
            created_by=user_id
        )
        
        # Save to database
        if supabase.enabled:
            result = supabase.client.table('campaigns').insert(campaign.to_dict()).execute()
            if not result.data:
                raise HTTPException(status_code=500, detail="Failed to create campaign")
            
            campaign_data = result.data[0]
        else:
            # Local storage fallback
            campaign_data = campaign.to_dict()
        
        logger.info(f"Created campaign {campaign.id} for workspace {request.workspace_id}")
        
        # Format response
        response = CampaignResponse(
            **campaign_data,
            status=campaign_data['status'],
            moves_summary=[],
            created_at=campaign_data['created_at'],
            updated_at=campaign_data['updated_at'],
            completed_at=campaign_data.get('completed_at')
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating campaign: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating campaign: {str(e)}")


@router.get("/", response_model=CampaignListResponse)
async def list_campaigns(
    workspace_id: str = Query(..., description="Workspace ID"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[CampaignStatus] = Query(None, description="Filter by status"),
    user_id: Optional[str] = None,
    supabase = Depends(get_supabase_client)
):
    """
    List campaigns with summaries of moves
    
    Returns a paginated list of campaigns with move summaries.
    """
    try:
        # Verify workspace access
        if not await verify_workspace_access(workspace_id, user_id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Build query
        query = supabase.client.table('campaigns').select('*').eq('workspace_id', workspace_id)
        
        if status:
            query = query.eq('status', status.value)
        
        # Add pagination
        offset = (page - 1) * per_page
        query = query.order('created_at', desc=True).range(offset, offset + per_page - 1)
        
        # Execute query
        result = query.execute()
        campaigns_data = result.data if result.data else []
        
        # Get move summaries for each campaign
        campaigns_with_summaries = []
        for campaign in campaigns_data:
            # Get move count and summary
            moves_result = supabase.client.table('moves') \
                .select('id, name, status, created_at') \
                .eq('campaign_id', campaign['id']) \
                .order('order_index', desc=True) \
                .limit(5) \
                .execute()
            
            moves_summary = moves_result.data if moves_result.data else []
            
            campaign_response = CampaignResponse(
                **campaign,
                status=campaign['status'],
                moves_summary=moves_summary,
                created_at=campaign['created_at'],
                updated_at=campaign['updated_at'],
                completed_at=campaign.get('completed_at')
            )
            campaigns_with_summaries.append(campaign_response)
        
        # Get total count
        count_query = supabase.client.table('campaigns').select('id', count='exact').eq('workspace_id', workspace_id)
        if status:
            count_query = count_query.eq('status', status.value)
        
        count_result = count_query.execute()
        total = count_result.count if count_result.count else 0
        
        return CampaignListResponse(
            campaigns=campaigns_with_summaries,
            total=total,
            page=page,
            per_page=per_page
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing campaigns: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing campaigns: {str(e)}")


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: str,
    user_id: Optional[str] = None,
    supabase = Depends(get_supabase_client)
):
    """
    Get campaign details with all moves
    
    Returns detailed campaign information including all associated moves.
    """
    try:
        # Get campaign
        result = supabase.client.table('campaigns').select('*').eq('id', campaign_id).execute()
        if not result.data or len(result.data) == 0:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        campaign_data = result.data[0]
        
        # Verify workspace access
        if not await verify_workspace_access(campaign_data['workspace_id'], user_id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get all moves for this campaign
        moves_result = supabase.client.table('moves') \
            .select('*') \
            .eq('campaign_id', campaign_id) \
            .order('order_index', desc=True) \
            .execute()
        
        moves_summary = moves_result.data if moves_result.data else []
        
        return CampaignResponse(
            **campaign_data,
            status=campaign_data['status'],
            moves_summary=moves_summary,
            created_at=campaign_data['created_at'],
            updated_at=campaign_data['updated_at'],
            completed_at=campaign_data.get('completed_at')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting campaign: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting campaign: {str(e)}")


@router.put("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: str,
    request: CampaignUpdateRequest,
    user_id: Optional[str] = None,
    supabase = Depends(get_supabase_client)
):
    """
    Update campaign details
    
    Updates campaign title, objective, status, or phases.
    """
    try:
        # Get existing campaign
        result = supabase.client.table('campaigns').select('*').eq('id', campaign_id).execute()
        if not result.data or len(result.data) == 0:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        campaign_data = result.data[0]
        
        # Verify workspace access
        if not await verify_workspace_access(campaign_data['workspace_id'], user_id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Prepare update data
        update_data = {}
        if request.title is not None:
            update_data['title'] = request.title
        if request.objective is not None:
            update_data['objective'] = request.objective
        if request.status is not None:
            update_data['status'] = request.status.value
            if request.status == CampaignStatus.COMPLETED:
                update_data['completed_at'] = datetime.now().isoformat()
        if request.target_icp is not None:
            update_data['target_icp'] = request.target_icp
        if request.arc_data is not None:
            update_data['arc_data'] = request.arc_data
        
        update_data['updated_at'] = datetime.now().isoformat()
        
        # Update campaign
        update_result = supabase.client.table('campaigns').update(update_data).eq('id', campaign_id).execute()
        if not update_result.data:
            raise HTTPException(status_code=500, detail="Failed to update campaign")
        
        updated_campaign = update_result.data[0]
        
        # Get moves summary
        moves_result = supabase.client.table('moves') \
            .select('id, name, status, created_at') \
            .eq('campaign_id', campaign_id) \
            .order('order_index', desc=True) \
            .limit(5) \
            .execute()
        
        moves_summary = moves_result.data if moves_result.data else []
        
        logger.info(f"Updated campaign {campaign_id}")
        
        return CampaignResponse(
            **updated_campaign,
            status=updated_campaign['status'],
            moves_summary=moves_summary,
            created_at=updated_campaign['created_at'],
            updated_at=updated_campaign['updated_at'],
            completed_at=updated_campaign.get('completed_at')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating campaign: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating campaign: {str(e)}")


@router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: str,
    user_id: Optional[str] = None,
    supabase = Depends(get_supabase_client)
):
    """
    Soft delete campaign
    
    Marks the campaign as cancelled rather than permanently deleting it.
    """
    try:
        # Get existing campaign
        result = supabase.client.table('campaigns').select('*').eq('id', campaign_id).execute()
        if not result.data or len(result.data) == 0:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        campaign_data = result.data[0]
        
        # Verify workspace access
        if not await verify_workspace_access(campaign_data['workspace_id'], user_id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Soft delete by setting status to cancelled
        update_result = supabase.client.table('campaigns') \
            .update({
                'status': CampaignStatus.CANCELLED.value,
                'updated_at': datetime.now().isoformat()
            }) \
            .eq('id', campaign_id) \
            .execute()
        
        if not update_result.data:
            raise HTTPException(status_code=500, detail="Failed to delete campaign")
        
        logger.info(f"Deleted campaign {campaign_id}")
        
        return JSONResponse(content={
            "message": "Campaign deleted successfully",
            "campaign_id": campaign_id,
            "status": "cancelled"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting campaign: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting campaign: {str(e)}")


# Move Endpoints

@router.post("/moves/", response_model=MoveResponse)
async def create_move(
    request: MoveCreateRequest,
    user_id: Optional[str] = None,
    supabase = Depends(get_supabase_client)
):
    """
    Create a new move
    
    Creates a move and optionally associates it with a campaign.
    Generates a unique tag for frontend display.
    """
    try:
        # Verify workspace access
        if not await verify_workspace_access(request.workspace_id, user_id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # If campaign_id is provided, verify it exists
        if request.campaign_id:
            campaign_result = supabase.client.table('campaigns').select('id').eq('id', request.campaign_id).execute()
            if not campaign_result.data:
                raise HTTPException(status_code=404, detail="Campaign not found")
        
        # Create move
        move = Move(
            id=str(uuid.uuid4()),
            workspace_id=request.workspace_id,
            campaign_id=request.campaign_id,
            name=request.name,
            description=request.description,
            tool_requirements=request.tool_requirements,
            muse_prompt=request.muse_prompt,
            confidence=request.confidence,
            success_prediction=request.success_prediction,
            risk_score=request.risk_score,
            due_date=request.due_date,
            status=MoveStatus.PROPOSED,
            created_by=user_id,
            proposed_by="user"
        )
        
        # Save to database
        if supabase.enabled:
            result = supabase.client.table('moves').insert(move.to_dict()).execute()
            if not result.data:
                raise HTTPException(status_code=500, detail="Failed to create move")
            
            move_data = result.data[0]
        else:
            move_data = move.to_dict()
        
        # Generate campaign tag
        campaign_tag = generate_move_tag(move)
        
        logger.info(f"Created move {move.id} for workspace {request.workspace_id}")
        
        return MoveResponse(
            **move_data,
            status=move_data['status'],
            campaign_tag=campaign_tag,
            created_at=move_data['created_at'],
            updated_at=move_data['updated_at'],
            started_at=move_data.get('started_at'),
            completed_at=move_data.get('completed_at'),
            due_date=move_data.get('due_date')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating move: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating move: {str(e)}")


@router.get("/moves/", response_model=MoveListResponse)
async def list_moves(
    workspace_id: str = Query(..., description="Workspace ID"),
    campaign_id: Optional[str] = Query(None, description="Filter by campaign ID"),
    status: Optional[MoveStatus] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    user_id: Optional[str] = None,
    supabase = Depends(get_supabase_client)
):
    """
    List moves with filtering options
    
    Returns a paginated list of moves with optional filtering by campaign and status.
    """
    try:
        # Verify workspace access
        if not await verify_workspace_access(workspace_id, user_id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Build query
        query = supabase.client.table('moves').select('*').eq('workspace_id', workspace_id)
        
        if campaign_id:
            query = query.eq('campaign_id', campaign_id)
        
        if status:
            query = query.eq('status', status.value)
        
        # Add pagination
        offset = (page - 1) * per_page
        query = query.order('order_index', desc=True).range(offset, offset + per_page - 1)
        
        # Execute query
        result = query.execute()
        moves_data = result.data if result.data else []
        
        # Format moves with campaign tags
        formatted_moves = []
        for move_data in moves_data:
            campaign_tag = generate_move_tag(move_data)
            
            # Get tasks and metrics (simplified for list view)
            move_data['tasks'] = []
            move_data['daily_metrics'] = []
            
            formatted_move = MoveResponse(
                **move_data,
                status=move_data['status'],
                campaign_tag=campaign_tag,
                created_at=move_data['created_at'],
                updated_at=move_data['updated_at'],
                started_at=move_data.get('started_at'),
                completed_at=move_data.get('completed_at'),
                due_date=move_data.get('due_date')
            )
            formatted_moves.append(formatted_move)
        
        # Get total count
        count_query = supabase.client.table('moves').select('id', count='exact').eq('workspace_id', workspace_id)
        if campaign_id:
            count_query = count_query.eq('campaign_id', campaign_id)
        if status:
            count_query = count_query.eq('status', status.value)
        
        count_result = count_query.execute()
        total = count_result.count if count_result.count else 0
        
        return MoveListResponse(
            moves=formatted_moves,
            total=total,
            page=page,
            per_page=per_page
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing moves: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing moves: {str(e)}")


@router.put("/moves/{move_id}", response_model=MoveResponse)
async def update_move(
    move_id: str,
    request: MoveUpdateRequest,
    user_id: Optional[str] = None,
    supabase = Depends(get_supabase_client)
):
    """
    Update move details
    
    Updates move name, status, confidence, dates, and other fields.
    """
    try:
        # Get existing move
        result = supabase.client.table('moves').select('*').eq('id', move_id).execute()
        if not result.data or len(result.data) == 0:
            raise HTTPException(status_code=404, detail="Move not found")
        
        move_data = result.data[0]
        
        # Verify workspace access
        if not await verify_workspace_access(move_data['workspace_id'], user_id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Prepare update data
        update_data = {}
        if request.name is not None:
            update_data['name'] = request.name
        if request.description is not None:
            update_data['description'] = request.description
        if request.status is not None:
            update_data['status'] = request.status.value
            # Auto-set dates based on status
            if request.status == MoveStatus.IN_PROGRESS and not move_data.get('started_at'):
                update_data['started_at'] = datetime.now().isoformat()
            elif request.status == MoveStatus.COMPLETED and not move_data.get('completed_at'):
                update_data['completed_at'] = datetime.now().isoformat()
        if request.confidence is not None:
            update_data['confidence'] = request.confidence
        if request.tool_requirements is not None:
            update_data['tool_requirements'] = request.tool_requirements
        if request.muse_prompt is not None:
            update_data['muse_prompt'] = request.muse_prompt
        if request.success_prediction is not None:
            update_data['success_prediction'] = request.success_prediction
        if request.risk_score is not None:
            update_data['risk_score'] = request.risk_score
        if request.due_date is not None:
            update_data['due_date'] = request.due_date.isoformat()
        if request.started_at is not None:
            update_data['started_at'] = request.started_at.isoformat()
        if request.completed_at is not None:
            update_data['completed_at'] = request.completed_at.isoformat()
        
        update_data['updated_at'] = datetime.now().isoformat()
        
        # Update move
        update_result = supabase.client.table('moves').update(update_data).eq('id', move_id).execute()
        if not update_result.data:
            raise HTTPException(status_code=500, detail="Failed to update move")
        
        updated_move = update_result.data[0]
        
        # Generate campaign tag
        campaign_tag = generate_move_tag(updated_move)
        
        logger.info(f"Updated move {move_id}")
        
        return MoveResponse(
            **updated_move,
            status=updated_move['status'],
            campaign_tag=campaign_tag,
            created_at=updated_move['created_at'],
            updated_at=updated_move['updated_at'],
            started_at=updated_move.get('started_at'),
            completed_at=updated_move.get('completed_at'),
            due_date=updated_move.get('due_date')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating move: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating move: {str(e)}")


@router.get("/health")
async def campaigns_health():
    """
    Health check for campaigns and moves service
    """
    return JSONResponse(content={
        "status": "healthy",
        "service": "campaigns_moves",
        "timestamp": datetime.now().isoformat(),
        "features": {
            "campaign_crud": True,
            "move_crud": True,
            "filtering": True,
            "pagination": True,
            "tags": True,
            "workspace_isolation": True
        }
    })
