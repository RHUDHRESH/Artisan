"""
Enhanced Notification System Tool Wrapper
Wraps the NotificationSystemTool for REST API integration
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import uuid
from loguru import logger

from backend.database_models import Notification


class NotificationSystemTool:
    """
    Enhanced notification system tool
    Supports multiple channels, scheduling, templates, and analytics
    """
    
    def __init__(self, supabase_client=None, redis_client=None):
        self.supabase = supabase_client
        self.redis = redis_client
        self.templates = {}
        self.global_settings = {
            "default_channels": ["in_app", "email"],
            "rate_limit": 10,  # notifications per minute
            "batch_size": 100
        }
        
    async def _send_notification(
        self,
        message: str,
        subject: str,
        recipients: List[str],
        channels: List[str],
        workspace_id: str,
        data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Internal method to send notifications
        """
        results = {
            "sent": 0,
            "failed": 0,
            "delivery_summary": {},
            "errors": []
        }
        
        for recipient in recipients:
            for channel in channels:
                try:
                    # Create notification record
                    notification = Notification(
                        id=str(uuid.uuid4()),
                        workspace_id=workspace_id,
                        user_id=recipient,
                        type="info",
                        channel=channel,
                        title=subject,
                        message=message,
                        data=data or {},
                        sent=False,
                        read=False
                    )
                    
                    # Save to database
                    if self.supabase and self.supabase.enabled:
                        notification_result = self.supabase.client.table('notifications') \
                            .insert(notification.to_dict()) \
                            .execute()
                        
                        if notification_result.data:
                            notification_id = notification_result.data[0]['id']
                            
                            # Send based on channel
                            sent_successfully = await self._send_to_channel(
                                channel, recipient, subject, message, data
                            )
                            
                            if sent_successfully:
                                # Mark as sent
                                await self.supabase.client.table('notifications') \
                                    .update({
                                        'sent': True,
                                        'sent_at': datetime.now().isoformat()
                                    }) \
                                    .eq('id', notification_id) \
                                    .execute()
                                
                                results["sent"] += 1
                                results["delivery_summary"][channel] = \
                                    results["delivery_summary"].get(channel, 0) + 1
                            else:
                                results["failed"] += 1
                                results["errors"].append(f"Failed to send to {recipient} via {channel}")
                        else:
                            results["failed"] += 1
                            results["errors"].append(f"Failed to create notification for {recipient}")
                    else:
                        # Fallback - just log
                        logger.info(f"Notification to {recipient} via {channel}: {subject}")
                        results["sent"] += 1
                        results["delivery_summary"][channel] = \
                            results["delivery_summary"].get(channel, 0) + 1
                        
                except Exception as e:
                    logger.error(f"Error sending notification to {recipient} via {channel}: {e}")
                    results["failed"] += 1
                    results["errors"].append(str(e))
        
        return results
    
    async def _send_to_channel(
        self,
        channel: str,
        recipient: str,
        subject: str,
        message: str,
        data: Optional[Dict] = None
    ) -> bool:
        """
        Send notification to specific channel
        """
        try:
            if channel == "in_app":
                # In-app notifications are stored in database, no external sending needed
                return True
            elif channel == "email":
                # Would integrate with email service (SendGrid, SES, etc.)
                logger.info(f"Email notification to {recipient}: {subject}")
                return True
            elif channel == "push":
                # Would integrate with push notification service (Firebase, OneSignal, etc.)
                logger.info(f"Push notification to {recipient}: {subject}")
                return True
            elif channel == "sms":
                # Would integrate with SMS service (Twilio, etc.)
                logger.info(f"SMS notification to {recipient}: {subject}")
                return True
            else:
                logger.warning(f"Unknown channel: {channel}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending to channel {channel}: {e}")
            return False
    
    async def _schedule_notification(
        self,
        notification_data: Dict[str, Any],
        recipients: List[str],
        channels: List[str],
        scheduling_options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Schedule notification for later delivery
        """
        try:
            # Create scheduled notification record
            scheduled_id = str(uuid.uuid4())
            
            schedule_data = {
                "id": scheduled_id,
                "notification_data": notification_data,
                "recipients": recipients,
                "channels": channels,
                "scheduling_options": scheduling_options,
                "created_at": datetime.now().isoformat(),
                "status": "scheduled"
            }
            
            # Store in Redis for scheduling (would use job queue in production)
            if self.redis:
                # Calculate delivery time
                deliver_at = scheduling_options.get('deliver_at')
                if isinstance(deliver_at, str):
                    deliver_at = datetime.fromisoformat(deliver_at.replace('Z', '+00:00'))
                elif isinstance(deliver_at, datetime):
                    pass  # Already datetime
                else:
                    # Default to 1 hour from now
                    deliver_at = datetime.now() + timedelta(hours=1)
                
                # Store in Redis with expiration
                await self.redis.setex(
                    f"scheduled_notification:{scheduled_id}",
                    timedelta(days=7),  # Keep for 7 days
                    json.dumps(schedule_data)
                )
                
                # In production, would add to job queue with delay
                logger.info(f"Scheduled notification {scheduled_id} for {deliver_at}")
                
                return {
                    "schedule_id": scheduled_id,
                    "status": "scheduled",
                    "deliver_at": deliver_at.isoformat(),
                    "recipients_count": len(recipients),
                    "channels": channels
                }
            else:
                # Fallback - send immediately
                return await self._send_notification(
                    message=notification_data.get('message', ''),
                    subject=notification_data.get('subject', ''),
                    recipients=recipients,
                    channels=channels,
                    workspace_id=notification_data.get('workspace_id', ''),
                    data=notification_data.get('data')
                )
                
        except Exception as e:
            logger.error(f"Error scheduling notification: {e}")
            return {
                "error": str(e),
                "status": "failed"
            }
    
    async def _manage_notification_templates(
        self,
        action: str,
        template_data: Optional[Dict[str, Any]] = None,
        template_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Manage notification templates
        """
        try:
            if action == "list":
                return {
                    "templates": self.templates,
                    "count": len(self.templates)
                }
            
            elif action == "create":
                if not template_data or not template_data.get('id'):
                    return {"error": "Template ID required"}
                
                template_id = template_data['id']
                self.templates[template_id] = template_data
                
                return {
                    "message": "Template created successfully",
                    "template_id": template_id
                }
            
            elif action == "update":
                if not template_id or template_id not in self.templates:
                    return {"error": "Template not found"}
                
                if template_data:
                    self.templates[template_id].update(template_data)
                
                return {
                    "message": "Template updated successfully",
                    "template_id": template_id
                }
            
            elif action == "delete":
                if not template_id or template_id not in self.templates:
                    return {"error": "Template not found"}
                
                del self.templates[template_id]
                
                return {
                    "message": "Template deleted successfully",
                    "template_id": template_id
                }
            
            else:
                return {"error": "Invalid action"}
                
        except Exception as e:
            logger.error(f"Error managing templates: {e}")
            return {"error": str(e)}
    
    async def get_analytics(
        self,
        workspace_id: str,
        date_range: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Return analytics summary, channel performance, engagement metrics
        """
        try:
            # Default to last 30 days
            if not date_range:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
            else:
                start_date = datetime.fromisoformat(date_range['start'])
                end_date = datetime.fromisoformat(date_range['end'])
            
            # Query notifications from database
            if self.supabase and self.supabase.enabled:
                result = self.supabase.client.table('notifications') \
                    .select('*') \
                    .eq('workspace_id', workspace_id) \
                    .gte('created_at', start_date.isoformat()) \
                    .lte('created_at', end_date.isoformat()) \
                    .execute()
                
                notifications = result.data if result.data; else []
            else:
                notifications = []
            
            # Calculate analytics
            total_sent = len(notifications)
            total_read = len([n for n in notifications if n.get('read', False)])
            
            # Channel performance
            channel_stats = {}
            for notification in notifications:
                channel = notification.get('channel', 'unknown')
                if channel not in channel_stats:
                    channel_stats[channel] = {"sent": 0, "read": 0}
                
                channel_stats[channel]["sent"] += 1
                if notification.get('read', False):
                    channel_stats[channel]["read"] += 1
            
            # Calculate engagement rates
            for channel in channel_stats:
                if channel_stats[channel]["sent"] > 0:
                    channel_stats[channel]["engagement_rate"] = \
                        channel_stats[channel]["read"] / channel_stats[channel]["sent"]
                else:
                    channel_stats[channel]["engagement_rate"] = 0.0
            
            # Type distribution
            type_stats = {}
            for notification in notifications:
                notif_type = notification.get('type', 'unknown')
                type_stats[notif_type] = type_stats.get(notif_type, 0) + 1
            
            # Generate insights
            insights = []
            if total_sent > 0:
                read_rate = total_read / total_sent
                if read_rate > 0.8:
                    insights.append("High engagement rate - users are actively reading notifications")
                elif read_rate < 0.3:
                    insights.append("Low engagement rate - consider improving notification content or timing")
                
                # Best performing channel
                best_channel = max(channel_stats.items(), 
                                key=lambda x: x[1].get('engagement_rate', 0))[0]
                insights.append(f"Best performing channel: {best_channel}")
            
            return {
                "summary": {
                    "total_sent": total_sent,
                    "total_read": total_read,
                    "read_rate": total_read / total_sent if total_sent > 0 else 0.0,
                    "date_range": {
                        "start": start_date.isoformat(),
                        "end": end_date.isoformat()
                    }
                },
                "channel_performance": channel_stats,
                "type_distribution": type_stats,
                "engagement_metrics": {
                    "daily_average": total_sent / 30 if total_sent > 0 else 0,
                    "peak_day": "Monday"  # Would calculate from data
                },
                "insights": insights
            }
            
        except Exception as e:
            logger.error(f"Error getting analytics: {e}")
            return {"error": str(e)}


class RadarNotificationService:
    """
    Service for processing radar signal notifications
    """
    
    def __init__(self, notification_tool: NotificationSystemTool):
        self.notification_tool = notification_tool
    
    async def process_signal_notifications(
        self,
        signal_ids: List[str],
        tenant_preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process signal notifications based on tenant preferences
        """
        try:
            processed_signals = []
            top_alerts = []
            
            # Get tenant notification rules
            rules = tenant_preferences.get('notification_rules', {})
            
            for signal_id in signal_ids:
                # In production, would fetch signal data from database
                signal_data = {
                    "id": signal_id,
                    "type": "competitor",
                    "strength": "high",
                    "content": f"Signal {signal_id} detected"
                }
                
                # Apply tenant rules
                should_notify = self._should_notify_signal(signal_data, rules)
                
                if should_notify:
                    processed_signals.append(signal_data)
                    
                    # Check if it's a top alert
                    if signal_data.get('strength') == 'high':
                        top_alerts.append({
                            "signal_id": signal_id,
                            "priority": "high",
                            "message": f"High priority signal: {signal_data.get('content', '')}"
                        })
            
            # Send notifications for processed signals
            if processed_signals:
                recipients = tenant_preferences.get('notification_recipients', [])
                channels = tenant_preferences.get('preferred_channels', ['in_app'])
                
                for signal in processed_signals:
                    await self.notification_tool._send_notification(
                        message=f"New signal detected: {signal.get('content', '')}",
                        subject=f"Signal Alert: {signal.get('type', 'Unknown').title()}",
                        recipients=recipients,
                        channels=channels,
                        workspace_id=tenant_preferences.get('workspace_id', ''),
                        data={"signal": signal}
                    )
            
            return {
                "processed_signals": len(processed_signals),
                "top_alerts": top_alerts,
                "notification_sent": len(processed_signals) > 0
            }
            
        except Exception as e:
            logger.error(f"Error processing signal notifications: {e}")
            return {"error": str(e)}
    
    def _should_notify_signal(self, signal_data: Dict[str, Any], rules: Dict[str, Any]) -> bool:
        """
        Check if signal should trigger notification based on tenant rules
        """
        # Check signal type preferences
        allowed_types = rules.get('allowed_signal_types', ['competitor', 'market'])
        if signal_data.get('type') not in allowed_types:
            return False
        
        # Check strength preferences
        min_strength = rules.get('minimum_strength', 'medium')
        strength_order = {'low': 0, 'medium': 1, 'high': 2}
        signal_strength = strength_order.get(signal_data.get('strength', 'medium'), 1)
        min_strength_level = strength_order.get(min_strength, 1)
        
        return signal_strength >= min_strength_level
    
    async def get_daily_digest(self, workspace_id: str) -> Dict[str, Any]:
        """
        Return daily digest of signals
        """
        try:
            # In production, would fetch today's signals from database
            # For now, return mock data
            return {
                "date": datetime.now().date().isoformat(),
                "workspace_id": workspace_id,
                "total_signals": 15,
                "high_priority": 3,
                "categories": {
                    "competitor": 8,
                    "market": 4,
                    "trend": 3
                },
                "top_signals": [
                    {
                        "id": "sig_1",
                        "type": "competitor",
                        "strength": "high",
                        "content": "Major competitor launched new product"
                    },
                    {
                        "id": "sig_2", 
                        "type": "market",
                        "strength": "high",
                        "content": "Market shift detected in target segment"
                    }
                ],
                "recommendations": [
                    "Monitor competitor product launch closely",
                    "Consider adjusting marketing strategy for market shift"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting daily digest: {e}")
            return {"error": str(e)}
