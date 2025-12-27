"""
Move Detail and Tasks API Routes
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import uuid
import json
from loguru import logger

from backend.database_models import Move, Task, DailyMetrics, ReasoningChain, TaskStatus, MoveStatus
from backend.core.supabase_client import get_supabase_client


# Request/Response Models
class TaskCreateRequest(BaseModel):
    label: str = Field(..., description="Task label")
    instructions: Optional[str] = Field(None, description="Task instructions")
    due_date: Optional[datetime] = Field(None, description="Due date")
    estimated_minutes: Optional[int] = Field(None, description="Estimated time in minutes")
    proposed_by: Optional[str] = Field(None, description="Who proposed this task")
    assigned_to: Optional[str] = Field(None, description="Who this task is assigned to")


class TaskUpdateRequest(BaseModel):
    label: Optional[str] = Field(None, description="Task label")
    instructions: Optional[str] = Field(None, description="Task instructions")
    status: Optional[TaskStatus] = Field(None, description="Task status")
    due_date: Optional[datetime] = Field(None, description="Due date")
    estimated_minutes: Optional[int] = Field(None, description="Estimated time in minutes")
    assigned_to: Optional[str] = Field(None, description="Who this task is assigned to")
    completion_notes: Optional[str] = Field(None, description="Notes on completion")


class MetricsCreateRequest(BaseModel):
    leads: int = Field(0, description="Number of leads")
    replies: int = Field(0, description="Number of replies")
    calls: int = Field(0, description="Number of calls")
    confidence: float = Field(0.0, description="Confidence score")
    conversion_rate: Optional[float] = Field(0.0, description="Conversion rate")
    engagement_score: Optional[float] = Field(0.0, description="Engagement score")
    revenue: Optional[float] = Field(0.0, description="Revenue generated")


class MoveUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, description="Move name")
    status: Optional[MoveStatus] = Field(None, description="Move status")
    confidence: Optional[float] = Field(None, description="Confidence score")
    started_at: Optional[datetime] = Field(None, description="Start date")
    completed_at: Optional[datetime] = Field(None, description="Completion date")
    due_date: Optional[datetime] = Field(None, description="Due date")


class MoveDetailResponse(BaseModel):
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
    checklist: List[Dict[str, Any]]  # Tasks
    daily_metrics: List[Dict[str, Any]]
    campaign_id: Optional[str]


class MoveRationaleResponse(BaseModel):
    decree: Optional[str]
    consensus_alignment: Optional[float]
    confidence: Optional[float]
    risk: Optional[float]
    expert_thoughts: List[Dict[str, Any]]
    rejected_paths: List[Dict[str, Any]]
    historical_parallel: Optional[str]
    truncated_debate_rounds: List[Dict[str, Any]]
    reasoning_chain_id: str


# Router setup
router = APIRouter(prefix="/moves", tags=["moves", "tasks"])


# Helper functions
async def verify_workspace_access(workspace_id: str, user_id: Optional[str] = None) -> bool:
    """Verify user has access to workspace"""
    # This would integrate with your auth system
    # For now, return True (no auth)
    return True


def calculate_rag_status(move_data: Dict[str, Any], metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate RAG (Red-Amber-Green) status based on move data and metrics
    Reuses frontend RAG calculation logic
    """
    # Base status from confidence and risk
    confidence = move_data.get('confidence', 0.0)
    risk_score = move_data.get('risk_score', 0.0)
    
    # Calculate recent metrics (last 7 days)
    recent_metrics = [m for m in metrics if 
                      datetime.fromisoformat(m['date'].replace('Z', '+00:00')) > 
                      datetime.now() - timedelta(days=7)]
    
    # Calculate metrics score
    metrics_score = 0.0
    if recent_metrics:
        avg_leads = sum(m.get('leads', 0) for m in recent_metrics) / len(recent_metrics)
        avg_confidence = sum(m.get('confidence', 0) for m in recent_metrics) / len(recent_metrics)
        metrics_score = min(1.0, (avg_leads / 10) + avg_confidence / 2)
    
    # Calculate overall score
    overall_score = (confidence * 0.4) + ((1 - risk_score) * 0.3) + (metrics_score * 0.3)
    
    # Determine RAG status
    if overall_score >= 0.7:
        status = "green"
        status_text = "On Track"
    elif overall_score >= 0.4:
        status = "amber"
        status_text = "Needs Attention"
    else:
        status = "red"
        status_text = "At Risk"
    
    return {
        "status": status,
        "status_text": status_text,
        "score": overall_score,
        "confidence": confidence,
        "risk_score": risk_score,
        "metrics_score": metrics_score,
        "factors": {
            "confidence": confidence,
            "risk": 1 - risk_score,
            "performance": metrics_score
        }
    }


# Move Detail Endpoints

@router.get("/{move_id}", response_model=MoveDetailResponse)
async def get_move_detail(
    move_id: str,
    user_id: Optional[str] = None,
    supabase = Depends(get_supabase_client)
):
    """
    Get complete move details including tasks, metrics, and RAG status
    
    Returns the full Move object with checklist, assets, dailyMetrics,
    confidence, rag, refinement_data, tool_requirements, and campaign_id.
    """
    try:
        # Get move
        result = supabase.client.table('moves').select('*').eq('id', move_id).execute()
        if not result.data or len(result.data) == 0:
            raise HTTPException(status_code=404, detail="Move not found")
        
        move_data = result.data[0]
        
        # Verify workspace access
        if not await verify_workspace_access(move_data['workspace_id'], user_id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get tasks (checklist)
        tasks_result = supabase.client.table('tasks') \
            .select('*') \
            .eq('move_id', move_id) \
            .order('order_index', asc=True) \
            .execute()
        
        checklist = tasks_result.data if tasks_result.data else []
        
        # Get daily metrics
        metrics_result = supabase.client.table('daily_metrics') \
            .select('*') \
            .eq('move_id', move_id) \
            .order('date', desc=True) \
            .limit(30) \
            .execute()
        
        daily_metrics = metrics_result.data if metrics_result.data else []
        
        # Calculate RAG status
        rag_status = calculate_rag_status(move_data, daily_metrics)
        
        # Format response
        return MoveDetailResponse(
            **move_data,
            status=move_data['status'],
            checklist=checklist,
            daily_metrics=daily_metrics,
            rag=rag_status,
            created_at=move_data['created_at'],
            updated_at=move_data['updated_at'],
            started_at=move_data.get('started_at'),
            completed_at=move_data.get('completed_at'),
            due_date=move_data.get('due_date')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting move detail: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting move detail: {str(e)}")


@router.get("/{move_id}/rationale", response_model=MoveRationaleResponse)
async def get_move_rationale(
    move_id: str,
    user_id: Optional[str] = None,
    supabase = Depends(get_supabase_client),
    redis_client = None
):
    """
    Get move rationale and reasoning chain
    
    Retrieves the move's reasoning_chain_id, fetches the debate history,
    consensus metrics, and synthesis from the reasoning_chains table.
    Results are cached in Redis.
    """
    try:
        # Check cache first
        cache_key = f"move_rationale:{move_id}"
        if redis_client:
            cached_result = await redis_client.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
        
        # Get move
        result = supabase.client.table('moves').select('*').eq('id', move_id).execute()
        if not result.data or len(result.data) == 0:
            raise HTTPException(status_code=404, detail="Move not found")
        
        move_data = result.data[0]
        
        # Verify workspace access
        if not await verify_workspace_access(move_data['workspace_id'], user_id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        reasoning_chain_id = move_data.get('reasoning_chain_id')
        if not reasoning_chain_id:
            # Return minimal rationale if no reasoning chain
            return MoveRationaleResponse(
                decree=None,
                consensus_alignment=None,
                confidence=move_data.get('confidence', 0.0),
                risk=move_data.get('risk_score', 0.0),
                expert_thoughts=[],
                rejected_paths=[],
                historical_parallel=None,
                truncated_debate_rounds=[],
                reasoning_chain_id=reasoning_chain_id or ""
            )
        
        # Get reasoning chain
        reasoning_result = supabase.client.table('reasoning_chains') \
            .select('*') \
            .eq('id', reasoning_chain_id) \
            .execute()
        
        if not reasoning_result.data or len(reasoning_result.data) == 0:
            raise HTTPException(status_code=404, detail="Reasoning chain not found")
        
        reasoning_data = reasoning_result.data[0]
        
        # Parse debate history
        debate_history = reasoning_data.get('debate_history', [])
        consensus_metrics = reasoning_data.get('consensus_metrics', {})
        
        # Extract expert thoughts from debate rounds
        expert_thoughts = []
        rejected_paths = []
        truncated_debate_rounds = []
        
        for round_data in debate_history[-3:]:  # Last 3 rounds
            round_summary = {
                "round_number": round_data.get('round_number'),
                "topic": round_data.get('topic'),
                "participants": round_data.get('participants', []),
                "consensus_score": round_data.get('consensus_score', 0.0),
                "outcome": round_data.get('outcome', ''),
                "timestamp": round_data.get('timestamp')
            }
            truncated_debate_rounds.append(round_summary)
            
            # Extract expert thoughts
            arguments = round_data.get('arguments', {})
            for expert, argument in arguments.items():
                if '_critique' not in expert:
                    expert_thoughts.append({
                        "expert": expert,
                        "thought": argument,
                        "round": round_data.get('round_number')
                    })
        
        # Format response
        response = MoveRationaleResponse(
            decree=reasoning_data.get('decree'),
            consensus_alignment=consensus_metrics.get('consensus_alignment'),
            confidence=move_data.get('confidence', 0.0),
            risk=move_data.get('risk_score', 0.0),
            expert_thoughts=expert_thoughts,
            rejected_paths=rejected_paths,
            historical_parallel=reasoning_data.get('synthesis'),
            truncated_debate_rounds=truncated_debate_rounds,
            reasoning_chain_id=reasoning_chain_id
        )
        
        # Cache result
        if redis_client:
            await redis_client.setex(
                cache_key,
                timedelta(hours=1),
                json.dumps(response.dict())
            )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting move rationale: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting move rationale: {str(e)}")


# Task Management Endpoints

@router.post("/{move_id}/tasks")
async def create_task(
    move_id: str,
    request: TaskCreateRequest,
    user_id: Optional[str] = None,
    supabase = Depends(get_supabase_client)
):
    """
    Append a new task to the move's checklist
    
    Creates a new task with the provided details and adds it to the move.
    """
    try:
        # Verify move exists and access
        move_result = supabase.client.table('moves').select('*').eq('id', move_id).execute()
        if not move_result.data or len(move_result.data) == 0:
            raise HTTPException(status_code=404, detail="Move not found")
        
        move_data = move_result.data[0]
        
        if not await verify_workspace_access(move_data['workspace_id'], user_id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get next order index
        tasks_result = supabase.client.table('tasks') \
            .select('order_index') \
            .eq('move_id', move_id) \
            .order('order_index', desc=True) \
            .limit(1) \
            .execute()
        
        next_order = 0
        if tasks_result.data and len(tasks_result.data) > 0:
            next_order = tasks_result.data[0]['order_index'] + 1
        
        # Create task
        task = Task(
            id=str(uuid.uuid4()),
            move_id=move_id,
            label=request.label,
            instructions=request.instructions,
            due_date=request.due_date,
            estimated_minutes=request.estimated_minutes,
            proposed_by=request.proposed_by,
            assigned_to=request.assigned_to,
            status=TaskStatus.PENDING,
            order_index=next_order
        )
        
        # Save task
        task_result = supabase.client.table('tasks').insert(task.to_dict()).execute()
        if not task_result.data:
            raise HTTPException(status_code=500, detail="Failed to create task")
        
        created_task = task_result.data[0]
        
        logger.info(f"Created task {created_task['id']} for move {move_id}")
        
        return JSONResponse(content={
            "message": "Task created successfully",
            "task": created_task
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating task: {str(e)}")


@router.put("/{move_id}/tasks/{task_id}")
async def update_task(
    move_id: str,
    task_id: str,
    request: TaskUpdateRequest,
    user_id: Optional[str] = None,
    supabase = Depends(get_supabase_client)
):
    """
    Update a task or mark it complete
    
    Updates task details or marks it as complete.
    Returns the updated move with all tasks.
    """
    try:
        # Verify move exists and access
        move_result = supabase.client.table('moves').select('*').eq('id', move_id).execute()
        if not move_result.data or len(move_result.data) == 0:
            raise HTTPException(status_code=404, detail="Move not found")
        
        move_data = move_result.data[0]
        
        if not await verify_workspace_access(move_data['workspace_id'], user_id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get task
        task_result = supabase.client.table('tasks').select('*').eq('id', task_id).eq('move_id', move_id).execute()
        if not task_result.data or len(task_result.data) == 0:
            raise HTTPException(status_code=404, detail="Task not found")
        
        task_data = task_result.data[0]
        
        # Prepare update data
        update_data = {}
        if request.label is not None:
            update_data['label'] = request.label
        if request.instructions is not None:
            update_data['instructions'] = request.instructions
        if request.status is not None:
            update_data['status'] = request.status.value
            if request.status == TaskStatus.COMPLETED:
                update_data['completed_at'] = datetime.now().isoformat()
        if request.due_date is not None:
            update_data['due_date'] = request.due_date.isoformat()
        if request.estimated_minutes is not None:
            update_data['estimated_minutes'] = request.estimated_minutes
        if request.assigned_to is not None:
            update_data['assigned_to'] = request.assigned_to
        if request.completion_notes is not None:
            update_data['completion_notes'] = request.completion_notes
        
        update_data['updated_at'] = datetime.now().isoformat()
        
        # Update task
        update_result = supabase.client.table('tasks').update(update_data).eq('id', task_id).execute()
        if not update_result.data:
            raise HTTPException(status_code=500, detail="Failed to update task")
        
        # Get updated move with all tasks
        updated_move_result = supabase.client.table('moves').select('*').eq('id', move_id).execute()
        updated_move = updated_move_result.data[0]
        
        # Get all tasks for the move
        tasks_result = supabase.client.table('tasks') \
            .select('*') \
            .eq('move_id', move_id) \
            .order('order_index', asc=True) \
            .execute()
        
        checklist = tasks_result.data if tasks_result.data else []
        
        logger.info(f"Updated task {task_id} for move {move_id}")
        
        return JSONResponse(content={
            "message": "Task updated successfully",
            "move": {
                **updated_move,
                "checklist": checklist
            }
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating task: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating task: {str(e)}")


@router.put("/{move_id}")
async def update_move_fields(
    move_id: str,
    request: MoveUpdateRequest,
    user_id: Optional[str] = None,
    supabase = Depends(get_supabase_client)
):
    """
    Update top-level move fields
    
    Updates move name, status, confidence, and dates.
    """
    try:
        # Verify move exists and access
        move_result = supabase.client.table('moves').select('*').eq('id', move_id).execute()
        if not move_result.data or len(move_result.data) == 0:
            raise HTTPException(status_code=404, detail="Move not found")
        
        move_data = move_result.data[0]
        
        if not await verify_workspace_access(move_data['workspace_id'], user_id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Prepare update data
        update_data = {}
        if request.name is not None:
            update_data['name'] = request.name
        if request.status is not None:
            update_data['status'] = request.status.value
            # Auto-set dates based on status
            if request.status == MoveStatus.IN_PROGRESS and not move_data.get('started_at'):
                update_data['started_at'] = datetime.now().isoformat()
            elif request.status == MoveStatus.COMPLETED and not move_data.get('completed_at'):
                update_data['completed_at'] = datetime.now().isoformat()
        if request.confidence is not None:
            update_data['confidence'] = request.confidence
        if request.started_at is not None:
            update_data['started_at'] = request.started_at.isoformat()
        if request.completed_at is not None:
            update_data['completed_at'] = request.completed_at.isoformat()
        if request.due_date is not None:
            update_data['due_date'] = request.due_date.isoformat()
        
        update_data['updated_at'] = datetime.now().isoformat()
        
        # Update move
        update_result = supabase.client.table('moves').update(update_data).eq('id', move_id).execute()
        if not update_result.data:
            raise HTTPException(status_code=500, detail="Failed to update move")
        
        updated_move = update_result.data[0]
        
        logger.info(f"Updated move {move_id}")
        
        return JSONResponse(content={
            "message": "Move updated successfully",
            "move": updated_move
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating move: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating move: {str(e)}")


@router.post("/{move_id}/metrics")
async def add_daily_metrics(
    move_id: str,
    request: MetricsCreateRequest,
    user_id: Optional[str] = None,
    supabase = Depends(get_supabase_client)
):
    """
    Append a daily metrics entry
    
    Adds metrics for leads, replies, calls, and confidence.
    Optionally returns updated RAG status.
    """
    try:
        # Verify move exists and access
        move_result = supabase.client.table('moves').select('*').eq('id', move_id).execute()
        if not move_result.data or len(move_result.data) == 0:
            raise HTTPException(status_code=404, detail="Move not found")
        
        move_data = move_result.data[0]
        
        if not await verify_workspace_access(move_data['workspace_id'], user_id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Create metrics entry
        metrics = DailyMetrics(
            id=str(uuid.uuid4()),
            move_id=move_id,
            date=datetime.now(),
            leads=request.leads,
            replies=request.replies,
            calls=request.calls,
            confidence=request.confidence,
            conversion_rate=request.conversion_rate,
            engagement_score=request.engagement_score,
            revenue=request.revenue
        )
        
        # Save metrics
        metrics_result = supabase.client.table('daily_metrics').insert(metrics.to_dict()).execute()
        if not metrics_result.data:
            raise HTTPException(status_code=500, detail="Failed to create metrics")
        
        created_metrics = metrics_result.data[0]
        
        # Get updated metrics for RAG calculation
        all_metrics_result = supabase.client.table('daily_metrics') \
            .select('*') \
            .eq('move_id', move_id) \
            .order('date', desc=True) \
            .limit(30) \
            .execute()
        
        all_metrics = all_metrics_result.data if all_metrics_result.data else []
        
        # Calculate updated RAG status
        rag_status = calculate_rag_status(move_data, all_metrics)
        
        logger.info(f"Added metrics for move {move_id}")
        
        return JSONResponse(content={
            "message": "Metrics added successfully",
            "metrics": created_metrics,
            "rag_status": rag_status
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Error adding metrics: {str(e)}")


@router.get("/health")
async def moves_health():
    """
    Health check for moves and tasks service
    """
    return JSONResponse(content={
        "status": "healthy",
        "service": "moves_tasks",
        "timestamp": datetime.now().isoformat(),
        "features": {
            "move_details": True,
            "task_management": True,
            "metrics_tracking": True,
            "rag_calculation": True,
            "rationale_fetching": True,
            "caching": True,
            "workspace_isolation": True
        }
    })
