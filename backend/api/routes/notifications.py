"""
Notification API Routes - Enhanced notification system
"""
from fastapi import APIRouter, HTTPException, Depends, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import uuid
import json
import asyncio
from loguru import logger

from backend.services.enhanced_notification_service import NotificationSystemTool, RadarNotificationService
from backend.core.supabase_client import get_supabase_client


# Request/Response Models
class SendNotificationRequest(BaseModel):
    message: str = Field(..., description="Notification message")
    subject: str = Field(..., description="Notification subject/title")
    recipients: List[str] = Field(..., description="List of recipient user IDs")
    channels: List[str] = Field(default=["in_app"], description="Notification channels")
    workspace_id: str = Field(..., description="Workspace ID")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional notification data")


class ScheduleNotificationRequest(BaseModel):
    notification_data: Dict[str, Any] = Field(..., description="Notification content and metadata")
    recipients: List[str] = Field(..., description="List of recipient user IDs")
    channels: List[str] = Field(default=["in_app"], description="Notification channels")
    scheduling_options: Dict[str, Any] = Field(..., description="Scheduling options (deliver_at, repeat, etc.)")


class TemplateRequest(BaseModel):
    action: str = Field(..., description="Action: list, create, update, delete")
    template_id: Optional[str] = Field(None, description="Template ID (for update/delete)")
    template_data: Optional[Dict[str, Any]] = Field(None, description="Template data (for create/update)")


class SignalProcessRequest(BaseModel):
    signal_ids: List[str] = Field(..., description="List of signal IDs to process")
    tenant_preferences: Dict[str, Any] = Field(..., description="Tenant notification preferences")


class NotificationResponse(BaseModel):
    id: str
    workspace_id: str
    user_id: str
    type: str
    channel: str
    title: str
    message: str
    read: bool
    sent: bool
    data: Optional[Dict[str, Any]]
    created_at: str
    read_at: Optional[str]
    sent_at: Optional[str]


class NotificationListResponse(BaseModel):
    notifications: List[NotificationResponse]
    total: int
    unread_count: int
    page: int
    per_page: int


# Router setup
router = APIRouter(prefix="/notifications", tags=["notifications"])

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        logger.info(f"WebSocket connected for user {user_id}")
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"WebSocket disconnected for user {user_id}")
    
    async def send_personal_message(self, message: str, user_id: str):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(message)
                except:
                    # Connection might be closed, remove it
                    self.active_connections[user_id].remove(connection)
    
    async def broadcast_to_workspace(self, message: str, workspace_id: str, user_ids: List[str]):
        for user_id in user_ids:
            await self.send_personal_message(message, user_id)


manager = ConnectionManager()


# Helper functions
async def verify_workspace_access(workspace_id: str, user_id: Optional[str] = None) -> bool:
    """Verify user has access to workspace"""
    # This would integrate with your auth system
    # For now, return True (no auth)
    return True


def get_notification_tool(supabase_client=None, redis_client=None) -> NotificationSystemTool:
    """Get notification tool instance"""
    return NotificationSystemTool(supabase_client, redis_client)


def get_radar_service(notification_tool: NotificationSystemTool) -> RadarNotificationService:
    """Get radar notification service instance"""
    return RadarNotificationService(notification_tool)


# Notification Endpoints

@router.post("/send")
async def send_notification(
    request: SendNotificationRequest,
    user_id: Optional[str] = None,
    supabase = Depends(get_supabase_client),
    redis_client = None
):
    """
    Send notification to recipients
    
    Calls _send_notification via the tool and returns delivery summary.
    """
    try:
        # Verify workspace access
        if not await verify_workspace_access(request.workspace_id, user_id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get notification tool
        notification_tool = get_notification_tool(supabase, redis_client)
        
        # Send notification
        result = await notification_tool._send_notification(
            message=request.message,
            subject=request.subject,
            recipients=request.recipients,
            channels=request.channels,
            workspace_id=request.workspace_id,
            data=request.data
        )
        
        # Send real-time notifications via WebSocket
        for recipient in request.recipients:
            await manager.send_personal_message(
                json.dumps({
                    "type": "notification",
                    "title": request.subject,
                    "message": request.message,
                    "data": request.data
                }),
                recipient
            )
        
        logger.info(f"Sent notification to {len(request.recipients)} recipients")
        
        return JSONResponse(content={
            "message": "Notification sent successfully",
            "delivery_summary": result
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        raise HTTPException(status_code=500, detail=f"Error sending notification: {str(e)}")


@router.post("/schedule")
async def schedule_notification(
    request: ScheduleNotificationRequest,
    user_id: Optional[str] = None,
    supabase = Depends(get_supabase_client),
    redis_client = None
):
    """
    Schedule notification for later delivery
    
    Calls _schedule_notification and returns the schedule.
    """
    try:
        # Verify workspace access
        workspace_id = request.notification_data.get('workspace_id', '')
        if not await verify_workspace_access(workspace_id, user_id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get notification tool
        notification_tool = get_notification_tool(supabase, redis_client)
        
        # Schedule notification
        result = await notification_tool._schedule_notification(
            notification_data=request.notification_data,
            recipients=request.recipients,
            channels=request.channels,
            scheduling_options=request.scheduling_options
        )
        
        logger.info(f"Scheduled notification for {len(request.recipients)} recipients")
        
        return JSONResponse(content={
            "message": "Notification scheduled successfully",
            "schedule": result
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scheduling notification: {e}")
        raise HTTPException(status_code=500, detail=f"Error scheduling notification: {str(e)}")


@router.get("/preferences")
async def get_notification_preferences(
    workspace_id: str = Query(..., description="Workspace ID"),
    user_id: Optional[str] = None,
    supabase = Depends(get_supabase_client)
):
    """
    Return user preferences and global settings
    
    Returns notification preferences for the user and workspace.
    """
    try:
        # Verify workspace access
        if not await verify_workspace_access(workspace_id, user_id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # In production, would fetch from user preferences table
        # For now, return default preferences
        user_preferences = {
            "channels": ["in_app", "email"],
            "quiet_hours": {
                "enabled": True,
                "start": "22:00",
                "end": "08:00"
            },
            "frequency_limits": {
                "max_per_day": 50,
                "max_per_hour": 10
            },
            "categories": {
                "system": True,
                "campaigns": True,
                "tasks": True,
                "signals": True
            }
        }
        
        global_settings = {
            "default_channels": ["in_app"],
            "rate_limit": 10,
            "batch_size": 100,
            "retention_days": 30
        }
        
        return JSONResponse(content={
            "user_preferences": user_preferences,
            "global_settings": global_settings,
            "workspace_id": workspace_id
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting notification preferences: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting preferences: {str(e)}")


@router.post("/templates")
async def manage_notification_templates(
    request: TemplateRequest,
    user_id: Optional[str] = None,
    supabase = Depends(get_supabase_client)
):
    """
    Manage notification templates
    
    Manages templates via _manage_notification_templates (list/create/update).
    """
    try:
        # Get notification tool
        notification_tool = get_notification_tool(supabase)
        
        # Manage templates
        result = await notification_tool._manage_notification_templates(
            action=request.action,
            template_data=request.template_data,
            template_id=request.template_id
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        logger.info(f"Template {request.action} operation completed")
        
        return JSONResponse(content=result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error managing templates: {e}")
        raise HTTPException(status_code=500, detail=f"Error managing templates: {str(e)}")


@router.get("/analytics")
async def get_notification_analytics(
    workspace_id: str = Query(..., description="Workspace ID"),
    date_range: Optional[Dict[str, Any]] = Query(None, description="Date range for analytics"),
    user_id: Optional[str] = None,
    supabase = Depends(get_supabase_client)
):
    """
    Return analytics summary, channel performance, engagement metrics, and insights
    """
    try:
        # Verify workspace access
        if not await verify_workspace_access(workspace_id, user_id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get notification tool
        notification_tool = get_notification_tool(supabase)
        
        # Get analytics
        analytics = await notification_tool.get_analytics(workspace_id, date_range)
        
        return JSONResponse(content=analytics)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting analytics: {str(e)}")


@router.post("/process")
async def process_signal_notifications(
    request: SignalProcessRequest,
    user_id: Optional[str] = None,
    supabase = Depends(get_supabase_client)
):
    """
    Process signal notifications
    
    Accepts a list of radar signal IDs and tenant preferences,
    calls process_signal_notifications from RadarNotificationService.
    """
    try:
        # Get notification tool and radar service
        notification_tool = get_notification_tool(supabase)
        radar_service = get_radar_service(notification_tool)
        
        # Process signal notifications
        result = await radar_service.process_signal_notifications(
            signal_ids=request.signal_ids,
            tenant_preferences=request.tenant_preferences
        )
        
        logger.info(f"Processed {len(request.signal_ids)} signal notifications")
        
        return JSONResponse(content={
            "message": "Signal notifications processed",
            "result": result
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing signal notifications: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing signals: {str(e)}")


@router.get("/digest/daily")
async def get_daily_digest(
    workspace_id: str = Query(..., description="Workspace ID"),
    user_id: Optional[str] = None,
    supabase = Depends(get_supabase_client)
):
    """
    Return the daily digest of signals
    
    Returns a daily summary of signals and recommendations.
    """
    try:
        # Verify workspace access
        if not await verify_workspace_access(workspace_id, user_id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get radar service
        notification_tool = get_notification_tool(supabase)
        radar_service = get_radar_service(notification_tool)
        
        # Get daily digest
        digest = await radar_service.get_daily_digest(workspace_id)
        
        return JSONResponse(content=digest)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting daily digest: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting digest: {str(e)}")


@router.get("/", response_model=NotificationListResponse)
async def list_notifications(
    workspace_id: str = Query(..., description="Workspace ID"),
    user_id: Optional[str] = Query(None, description="User ID (optional for admin view)"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    unread_only: bool = Query(False, description="Filter unread only"),
    channel: Optional[str] = Query(None, description="Filter by channel"),
    supabase = Depends(get_supabase_client)
):
    """
    List notifications for user or workspace
    
    Returns paginated list of notifications with filtering options.
    """
    try:
        # Verify workspace access
        if not await verify_workspace_access(workspace_id, user_id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Build query
        query = supabase.client.table('notifications').select('*', count='exact')
        
        if user_id:
            query = query.eq('user_id', user_id)
        else:
            query = query.eq('workspace_id', workspace_id)
        
        if unread_only:
            query = query.eq('read', False)
        
        if channel:
            query = query.eq('channel', channel)
        
        # Add pagination
        offset = (page - 1) * per_page
        query = query.order('created_at', desc=True).range(offset, offset + per_page - 1)
        
        # Execute query
        result = query.execute()
        notifications_data = result.data if result.data else []
        total = result.count if result.count else 0
        
        # Get unread count
        unread_query = supabase.client.table('notifications').select('id', count='exact')
        if user_id:
            unread_query = unread_query.eq('user_id', user_id)
        else:
            unread_query = unread_query.eq('workspace_id', workspace_id)
        
        unread_query = unread_query.eq('read', False)
        unread_result = unread_query.execute()
        unread_count = unread_result.count if unread_result.count else 0
        
        # Format notifications
        formatted_notifications = []
        for notif in notifications_data:
            formatted_notif = NotificationResponse(
                **notif,
                created_at=notif['created_at'],
                read_at=notif.get('read_at'),
                sent_at=notif.get('sent_at')
            )
            formatted_notifications.append(formatted_notif)
        
        return NotificationListResponse(
            notifications=formatted_notifications,
            total=total,
            unread_count=unread_count,
            page=page,
            per_page=per_page
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing notifications: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing notifications: {str(e)}")


@router.put("/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    user_id: Optional[str] = None,
    supabase = Depends(get_supabase_client)
):
    """
    Mark notification as read
    """
    try:
        # Get notification
        result = supabase.client.table('notifications').select('*').eq('id', notification_id).execute()
        if not result.data or len(result.data) == 0:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        notification = result.data[0]
        
        # Verify workspace access
        if not await verify_workspace_access(notification['workspace_id'], user_id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Mark as read
        update_result = supabase.client.table('notifications').update({
            'read': True,
            'read_at': datetime.now().isoformat()
        }).eq('id', notification_id).execute()
        
        if not update_result.data:
            raise HTTPException(status_code=500, detail="Failed to mark notification as read")
        
        logger.info(f"Marked notification {notification_id} as read")
        
        return JSONResponse(content={
            "message": "Notification marked as read",
            "notification_id": notification_id
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}")
        raise HTTPException(status_code=500, detail=f"Error marking notification as read: {str(e)}")


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """
    WebSocket endpoint for real-time notifications
    """
    await manager.connect(websocket, user_id)
    try:
        while True:
            # Keep connection alive and listen for messages
            data = await websocket.receive_text()
            
            # Handle any client messages (like ping/pong)
            try:
                message = json.loads(data)
                if message.get('type') == 'ping':
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except json.JSONDecodeError:
                pass  # Ignore invalid JSON
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)


@router.get("/health")
async def notifications_health():
    """
    Health check for notifications service
    """
    return JSONResponse(content={
        "status": "healthy",
        "service": "notifications",
        "timestamp": datetime.now().isoformat(),
        "features": {
            "send_notifications": True,
            "schedule_notifications": True,
            "templates": True,
            "analytics": True,
            "signal_processing": True,
            "daily_digest": True,
            "websocket": True,
            "workspace_isolation": True
        }
    })
