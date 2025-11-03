"""
Notification Service - Alerts and notifications for users
"""
from typing import Dict, List, Optional
from loguru import logger
from datetime import datetime


class NotificationService:
    """
    Notification service for user alerts
    Can integrate with Firebase or use local storage
    """
    
    def __init__(self, firebase_service=None):
        self.firebase = firebase_service
        self.local_notifications: List[Dict] = []
    
    async def send_notification(
        self,
        user_id: str,
        title: str,
        message: str,
        notification_type: str = "info",
        data: Optional[Dict] = None
    ) -> bool:
        """
        Send notification to user
        
        Args:
            user_id: User identifier
            title: Notification title
            message: Notification message
            notification_type: Type (info, success, warning, error)
            data: Additional data
        
        Returns:
            Success status
        """
        notification = {
            "user_id": user_id,
            "title": title,
            "message": message,
            "type": notification_type,
            "data": data or {},
            "timestamp": datetime.now().isoformat(),
            "read": False
        }
        
        # Save to Firebase if available
        if self.firebase and self.firebase.is_enabled():
            await self.firebase.save_notification(user_id, notification)
        
        # Also store locally
        self.local_notifications.append(notification)
        
        logger.info(f"Sent notification to {user_id}: {title}")
        return True
    
    async def notify_supplier_found(self, user_id: str, supplier_name: str, location: str):
        """Notify user about new supplier"""
        await self.send_notification(
            user_id=user_id,
            title="New Supplier Found",
            message=f"Found supplier: {supplier_name} in {location}",
            notification_type="success",
            data={"supplier_name": supplier_name, "location": location}
        )
    
    async def notify_event_nearby(self, user_id: str, event_name: str, location: str, date: str):
        """Notify user about nearby event"""
        await self.send_notification(
            user_id=user_id,
            title="Upcoming Event",
            message=f"{event_name} in {location} on {date}",
            notification_type="info",
            data={"event_name": event_name, "location": location, "date": date}
        )
    
    async def notify_growth_opportunity(self, user_id: str, opportunity: str):
        """Notify user about growth opportunity"""
        await self.send_notification(
            user_id=user_id,
            title="Growth Opportunity",
            message=opportunity,
            notification_type="success",
            data={"opportunity": opportunity}
        )
    
    def get_user_notifications(self, user_id: str, unread_only: bool = False) -> List[Dict]:
        """Get notifications for user"""
        notifications = [
            n for n in self.local_notifications
            if n["user_id"] == user_id
        ]
        
        if unread_only:
            notifications = [n for n in notifications if not n.get("read", False)]
        
        # Sort by timestamp (newest first)
        notifications.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return notifications
    
    async def mark_as_read(self, user_id: str, notification_timestamp: str):
        """Mark notification as read"""
        for notification in self.local_notifications:
            if (notification["user_id"] == user_id and 
                notification["timestamp"] == notification_timestamp):
                notification["read"] = True
                break

