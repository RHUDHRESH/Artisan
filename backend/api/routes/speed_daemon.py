"""
Speed Daemon API Routes - AI Acceleration Service
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from typing import Optional, List
from datetime import datetime, timedelta
import uuid
import asyncio

from backend.models.muse_api import (
    SpeedTaskRequest, SpeedTaskResponse, SpeedTaskStatusResponse,
    SuccessResponse
)
from backend.models.muse import SpeedDaemonTask
from backend.core.database import get_db
from backend.core.caching import cache_manager
from loguru import logger

router = APIRouter(prefix="/v1/speed", tags=["speed-daemon"])

# Dependency to get tenant and user context
async def get_user_context() -> tuple:
    """Get current tenant and user IDs - in production from JWT/auth"""
    return "default_tenant", "default_user"


# Speed Daemon Task Endpoints
@router.post("/tasks", response_model=SpeedTaskResponse)
async def submit_speed_task(
    request: SpeedTaskRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    context: tuple = Depends(get_user_context)
):
    """
    Submit a task to the Speed Daemon for accelerated AI processing
    """
    try:
        tenant_id, user_id = context
        
        # Validate task type
        valid_task_types = [
            "content_generation",
            "summarization", 
            "copywriting",
            "analysis",
            "translation",
            "optimization"
        ]
        
        if request.task_type not in valid_task_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid task type. Must be one of: {valid_task_types}"
            )
        
        # Estimate duration based on task type and input size
        estimated_duration = estimate_task_duration(request.task_type, request.input_data)
        
        # Create task
        task = SpeedDaemonTask(
            tenant_id=tenant_id,
            user_id=user_id,
            task_type=request.task_type,
            input_data=request.input_data,
            priority=request.priority,
            estimated_duration_seconds=estimated_duration,
            callback_url=request.callback_url,
            webhook_secret=request.webhook_secret,
            status="queued",
            expires_at=datetime.utcnow() + timedelta(hours=24)  # Tasks expire after 24 hours
        )
        
        db.add(task)
        db.commit()
        db.refresh(task)
        
        # Queue task for processing
        background_tasks.add_task(
            process_speed_daemon_task,
            task.id,
            request.task_type,
            request.input_data,
            request.priority
        )
        
        logger.info(f"Submitted Speed Daemon task {task.id} of type {request.task_type}")
        
        return SpeedTaskResponse(
            task_id=task.id,
            status=task.status,
            task_type=task.task_type,
            priority=task.priority,
            estimated_duration_seconds=estimated_duration,
            created_at=task.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Speed Daemon task submission failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}", response_model=SpeedTaskStatusResponse)
async def get_task_status(
    task_id: str,
    db: Session = Depends(get_db),
    context: tuple = Depends(get_user_context)
):
    """
    Get the status and result of a Speed Daemon task
    """
    try:
        tenant_id, user_id = context
        
        task = db.query(SpeedDaemonTask).filter(
            and_(
                SpeedDaemonTask.id == task_id,
                SpeedDaemonTask.tenant_id == tenant_id,
                SpeedDaemonTask.user_id == user_id
            )
        ).first()
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Check if task has expired
        if task.expires_at and datetime.utcnow() > task.expires_at:
            task.status = "failed"
            task.error_message = "Task expired"
            db.commit()
        
        return SpeedTaskStatusResponse(
            task_id=task.id,
            status=task.status,
            progress=task.progress,
            task_type=task.task_type,
            input_data=task.input_data,
            output_data=task.output_data,
            priority=task.priority,
            estimated_duration_seconds=task.estimated_duration_seconds,
            actual_duration_seconds=task.actual_duration_seconds,
            error_message=task.error_message,
            created_at=task.created_at,
            started_at=task.started_at,
            completed_at=task.completed_at,
            expires_at=task.expires_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Task status retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/tasks/{task_id}", response_model=SuccessResponse)
async def cancel_task(
    task_id: str,
    db: Session = Depends(get_db),
    context: tuple = Depends(get_user_context)
):
    """
    Cancel a queued or running Speed Daemon task
    """
    try:
        tenant_id, user_id = context
        
        task = db.query(SpeedDaemonTask).filter(
            and_(
                SpeedDaemonTask.id == task_id,
                SpeedDaemonTask.tenant_id == tenant_id,
                SpeedDaemonTask.user_id == user_id,
                SpeedDaemonTask.status.in_(["queued", "processing"])
            )
        ).first()
        
        if not task:
            raise HTTPException(
                status_code=404,
                detail="Task not found or cannot be cancelled"
            )
        
        # Update task status
        task.status = "cancelled"
        task.completed_at = datetime.utcnow()
        
        if task.started_at:
            task.actual_duration_seconds = (task.completed_at - task.started_at).total_seconds()
        
        db.commit()
        
        logger.info(f"Cancelled Speed Daemon task {task_id}")
        return SuccessResponse(message="Task cancelled successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Task cancellation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks", response_model=list[SpeedTaskStatusResponse])
async def list_tasks(
    status: Optional[str] = Query(None, description="Filter by status"),
    task_type: Optional[str] = Query(None, description="Filter by task type"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of tasks"),
    db: Session = Depends(get_db),
    context: tuple = Depends(get_user_context)
):
    """
    List user's Speed Daemon tasks
    """
    try:
        tenant_id, user_id = context
        
        query = db.query(SpeedDaemonTask).filter(
            and_(
                SpeedDaemonTask.tenant_id == tenant_id,
                SpeedDaemonTask.user_id == user_id
            )
        )
        
        if status:
            query = query.filter(SpeedDaemonTask.status == status)
        if task_type:
            query = query.filter(SpeedDaemonTask.task_type == task_type)
        
        tasks = query.order_by(desc(SpeedDaemonTask.created_at)).limit(limit).all()
        
        return [
            SpeedTaskStatusResponse(
                task_id=task.id,
                status=task.status,
                progress=task.progress,
                task_type=task.task_type,
                input_data=task.input_data,
                output_data=task.output_data,
                priority=task.priority,
                estimated_duration_seconds=task.estimated_duration_seconds,
                actual_duration_seconds=task.actual_duration_seconds,
                error_message=task.error_message,
                created_at=task.created_at,
                started_at=task.started_at,
                completed_at=task.completed_at,
                expires_at=task.expires_at
            )
            for task in tasks
        ]
        
    except Exception as e:
        logger.error(f"Task listing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=dict)
async def get_speed_daemon_status(
    db: Session = Depends(get_db)
):
    """
    Get Speed Daemon service status and statistics
    """
    try:
        # Get task statistics
        total_tasks = db.query(SpeedDaemonTask).count()
        queued_tasks = db.query(SpeedDaemonTask).filter(SpeedDaemonTask.status == "queued").count()
        processing_tasks = db.query(SpeedDaemonTask).filter(SpeedDaemonTask.status == "processing").count()
        completed_tasks = db.query(SpeedDaemonTask).filter(SpeedDaemonTask.status == "completed").count()
        failed_tasks = db.query(SpeedDaemonTask).filter(SpeedDaemonTask.status == "failed").count()
        
        # Get recent performance metrics
        recent_tasks = db.query(SpeedDaemonTask).filter(
            and_(
                SpeedDaemonTask.status == "completed",
                SpeedDaemonTask.completed_at >= datetime.utcnow() - timedelta(hours=24)
            )
        ).all()
        
        avg_duration = 0
        if recent_tasks:
            avg_duration = sum(t.actual_duration_seconds or 0 for t in recent_tasks) / len(recent_tasks)
        
        return {
            "service_status": "running",
            "version": "1.5.0",
            "uptime_seconds": 86400.0,  # Placeholder
            "statistics": {
                "total_tasks": total_tasks,
                "queued_tasks": queued_tasks,
                "processing_tasks": processing_tasks,
                "completed_tasks": completed_tasks,
                "failed_tasks": failed_tasks,
                "success_rate": completed_tasks / max(total_tasks, 1),
                "avg_duration_seconds_24h": avg_duration
            },
            "gpu_status": "available",  # Placeholder
            "queue_depth": queued_tasks,
            "estimated_wait_time": max(queued_tasks * 30, 0)  # 30 seconds per task estimate
        }
        
    except Exception as e:
        logger.error(f"Speed Daemon status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Background task processing
async def process_speed_daemon_task(
    task_id: str,
    task_type: str,
    input_data: dict,
    priority: str
):
    """
    Background task to process Speed Daemon requests
    """
    db = get_db().__next__()
    
    try:
        # Get task
        task = db.query(SpeedDaemonTask).filter(SpeedDaemonTask.id == task_id).first()
        if not task:
            logger.error(f"Task {task_id} not found for processing")
            return
        
        # Update task status to processing
        task.status = "processing"
        task.started_at = datetime.utcnow()
        db.commit()
        
        # Simulate processing time based on task complexity
        processing_time = estimate_task_duration(task_type, input_data)
        await asyncio.sleep(processing_time)
        
        # Generate output based on task type
        output_data = await generate_task_output(task_type, input_data)
        
        # Update task with results
        task.status = "completed"
        task.progress = 1.0
        task.output_data = output_data
        task.completed_at = datetime.utcnow()
        task.actual_duration_seconds = (task.completed_at - task.started_at).total_seconds()
        
        db.commit()
        
        # Send webhook callback if provided
        if task.callback_url:
            await send_webhook_callback(task.callback_url, task.id, output_data, task.webhook_secret)
        
        logger.info(f"Speed Daemon task {task_id} completed successfully")
        
    except Exception as e:
        # Update task with error
        task.status = "failed"
        task.error_message = str(e)
        task.completed_at = datetime.utcnow()
        if task.started_at:
            task.actual_duration_seconds = (task.completed_at - task.started_at).total_seconds()
        
        db.commit()
        logger.error(f"Speed Daemon task {task_id} failed: {e}")
        
    finally:
        db.close()


# Helper functions
def estimate_task_duration(task_type: str, input_data: dict) -> int:
    """
    Estimate task processing duration in seconds
    """
    base_durations = {
        "content_generation": 30,
        "summarization": 20,
        "copywriting": 25,
        "analysis": 35,
        "translation": 15,
        "optimization": 40
    }
    
    base_duration = base_durations.get(task_type, 30)
    
    # Adjust based on input size
    input_size = len(str(input_data))
    size_multiplier = max(1, input_size / 1000)  # Adjust for larger inputs
    
    # Adjust based on priority
    priority_multipliers = {
        "high": 0.5,    # High priority tasks are processed faster
        "normal": 1.0,
        "low": 1.5      # Low priority tasks may take longer
    }
    
    priority_multiplier = priority_multipliers.get("normal", 1.0)
    
    return int(base_duration * size_multiplier * priority_multiplier)


async def generate_task_output(task_type: str, input_data: dict) -> dict:
    """
    Generate output for different task types
    In production, this would call actual AI models
    """
    if task_type == "content_generation":
        return {
            "generated_content": f"AI-generated content based on: {input_data.get('prompt', 'No prompt')}",
            "word_count": 150,
            "readability_score": 8.5,
            "suggestions": ["Consider adding more examples", "Add a stronger call-to-action"]
        }
    
    elif task_type == "summarization":
        return {
            "summary": f"Summary of the provided content: {input_data.get('text', 'No text')[:100]}...",
            "key_points": ["Point 1", "Point 2", "Point 3"],
            "sentiment": "neutral",
            "compression_ratio": 0.3
        }
    
    elif task_type == "copywriting":
        return {
            "headline": "Compelling headline generated by AI",
            "subheadline": "Supporting subheadline",
            "body_copy": "Engaging body copy that drives action",
            "cta": "Clear call-to-action",
            "variants": ["Variant A", "Variant B", "Variant C"]
        }
    
    else:
        return {
            "result": f"Processed {task_type} task",
            "confidence": 0.95,
            "processing_time": "fast"
        }


async def send_webhook_callback(
    callback_url: str,
    task_id: str,
    output_data: dict,
    webhook_secret: Optional[str]
):
    """
    Send webhook callback when task is completed
    """
    try:
        import httpx
        
        payload = {
            "task_id": task_id,
            "status": "completed",
            "output_data": output_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        headers = {}
        if webhook_secret:
            headers["Authorization"] = f"Bearer {webhook_secret}"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(callback_url, json=payload, headers=headers)
            response.raise_for_status()
        
        logger.info(f"Webhook callback sent for task {task_id}")
        
    except Exception as e:
        logger.error(f"Webhook callback failed for task {task_id}: {e}")
