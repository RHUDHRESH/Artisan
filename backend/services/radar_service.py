"""
Radar Service - Business logic for signal intelligence system
"""
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from loguru import logger
import json

from backend.models.radar import (
    RadarSignal, RadarDossier, DossierSignal, SchedulerTask, 
    SchedulerExecution, RadarNotification, AnalyticsSnapshot,
    CompetitorAnalysis, MarketIntelligence, RecommendedOpportunity
)
from backend.models.radar_api import (
    SignalModel, DossierModel, TrendData, 
    CompetitorMetrics, MarketIntelligenceModel, OpportunityModel
)
from backend.core.caching import cache_manager


class RadarSignalService:
    """Service for managing radar signals"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    async def create_signal(
        self,
        tenant_id: str,
        signal_type: str,
        source: str,
        content: str,
        confidence: float = 0.0,
        strength: str = "low",
        freshness: float = 1.0,
        action_suggestion: Optional[str] = None,
        evidence_count: int = 0,
        signal_timestamp: Optional[datetime] = None
    ) -> RadarSignal:
        """Create a new radar signal"""
        signal = RadarSignal(
            tenant_id=tenant_id,
            signal_type=signal_type,
            source=source,
            content=content,
            confidence=confidence,
            strength=strength,
            freshness=freshness,
            action_suggestion=action_suggestion,
            evidence_count=evidence_count,
            signal_timestamp=signal_timestamp or datetime.utcnow(),
            processing_status="processed"
        )
        
        self.db.add(signal)
        self.db.commit()
        self.db.refresh(signal)
        
        logger.info(f"Created signal {signal.id} of type {signal_type}")
        return signal
    
    def get_signals(
        self,
        tenant_id: str,
        signal_type: Optional[str] = None,
        strength: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[RadarSignal]:
        """Get signals with optional filters"""
        query = self.db.query(RadarSignal).filter(RadarSignal.tenant_id == tenant_id)
        
        if signal_type:
            query = query.filter(RadarSignal.signal_type == signal_type)
        if strength:
            query = query.filter(RadarSignal.strength == strength)
        
        return query.order_by(desc(RadarSignal.created_at)).offset(offset).limit(limit).all()
    
    def get_signal_by_id(self, signal_id: str) -> Optional[RadarSignal]:
        """Get a specific signal by ID"""
        return self.db.query(RadarSignal).filter(RadarSignal.id == signal_id).first()
    
    async def update_signal_strength(self, signal_id: str, new_strength: str) -> bool:
        """Update signal strength"""
        signal = self.get_signal_by_id(signal_id)
        if not signal:
            return False
        
        signal.strength = new_strength
        signal.updated_at = datetime.utcnow()
        self.db.commit()
        
        logger.info(f"Updated signal {signal_id} strength to {new_strength}")
        return True


class RadarDossierService:
    """Service for managing intelligence dossiers"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    async def create_dossier(
        self,
        tenant_id: str,
        campaign_id: str,
        title: str,
        signal_ids: List[str],
        summary: str,
        hypotheses: Optional[List[Dict]] = None,
        experiments: Optional[List[Dict]] = None,
        copy_snippets: Optional[List[str]] = None,
        market_narrative: Optional[str] = None
    ) -> RadarDossier:
        """Create a new intelligence dossier"""
        dossier = RadarDossier(
            tenant_id=tenant_id,
            campaign_id=campaign_id,
            title=title,
            summary=summary,
            hypotheses=hypotheses or [],
            experiments=experiments or [],
            copy_snippets=copy_snippets or [],
            market_narrative=market_narrative,
            signal_count=len(signal_ids),
            status="draft"
        )
        
        self.db.add(dossier)
        self.db.commit()
        self.db.refresh(dossier)
        
        # Link signals to dossier
        for signal_id in signal_ids:
            dossier_signal = DossierSignal(
                dossier_id=dossier.id,
                signal_id=signal_id,
                relevance_score=0.8,  # Default relevance
                included_in_summary=True
            )
            self.db.add(dossier_signal)
        
        self.db.commit()
        logger.info(f"Created dossier {dossier.id} with {len(signal_ids)} signals")
        return dossier
    
    def get_dossier_by_id(self, dossier_id: str) -> Optional[RadarDossier]:
        """Get a specific dossier by ID"""
        return self.db.query(RadarDossier).filter(RadarDossier.id == dossier_id).first()
    
    def get_dossiers_by_campaign(self, tenant_id: str, campaign_id: str) -> List[RadarDossier]:
        """Get all dossiers for a campaign"""
        return self.db.query(RadarDossier).filter(
            and_(RadarDossier.tenant_id == tenant_id, RadarDossier.campaign_id == campaign_id)
        ).order_by(desc(RadarDossier.created_at)).all()


class RadarAnalyticsService:
    """Service for radar analytics and insights"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    async def get_signal_trends(
        self, 
        tenant_id: str, 
        window_days: int = 30
    ) -> List[TrendData]:
        """Get signal trends over time"""
        start_date = datetime.utcnow() - timedelta(days=window_days)
        
        # Group signals by date and strength
        query = self.db.query(
            func.date(RadarSignal.created_at).label('date'),
            RadarSignal.strength,
            func.count(RadarSignal.id).label('count')
        ).filter(
            and_(
                RadarSignal.tenant_id == tenant_id,
                RadarSignal.created_at >= start_date
            )
        ).group_by(
            func.date(RadarSignal.created_at),
            RadarSignal.strength
        ).all()
        
        # Organize data by date
        daily_data = {}
        for date, strength, count in query:
            if date not in daily_data:
                daily_data[date] = {"high": 0, "medium": 0, "low": 0, "total": 0}
            daily_data[date][strength] = count
            daily_data[date]["total"] += count
        
        # Convert to TrendData objects
        trend_data = []
        for date in sorted(daily_data.keys()):
            data = daily_data[date]
            trend_data.append(TrendData(
                date=datetime.combine(date, datetime.min.time()),
                high_strength=data["high"],
                medium_strength=data["medium"],
                low_strength=data["low"],
                total_signals=data["total"],
                categories={}  # TODO: Add category breakdown
            ))
        
        return trend_data
    
    async def get_competitor_metrics(self, tenant_id: str) -> List[CompetitorMetrics]:
        """Get competitor analysis metrics"""
        competitors = self.db.query(CompetitorAnalysis).filter(
            CompetitorAnalysis.tenant_id == tenant_id
        ).all()
        
        metrics = []
        for comp in competitors:
            metrics.append(CompetitorMetrics(
                competitor_name=comp.competitor_name,
                market_position=comp.market_position,
                market_share_estimate=comp.market_share_estimate,
                traffic_estimate=comp.traffic_estimate,
                sentiment_score=comp.sentiment_score,
                strengths=comp.strengths or [],
                weaknesses=comp.weaknesses or [],
                last_analyzed=comp.last_analyzed_at
            ))
        
        return metrics
    
    async def get_market_intelligence(self, tenant_id: str) -> List[MarketIntelligenceModel]:
        """Get market intelligence data"""
        intelligence = self.db.query(MarketIntelligence).filter(
            MarketIntelligence.tenant_id == tenant_id
        ).order_by(desc(MarketIntelligence.created_at)).limit(10).all()
        
        models = []
        for intel in intelligence:
            models.append(MarketIntelligenceModel(
                market_segment=intel.market_segment,
                geographic_focus=intel.geographic_focus,
                growth_rate=intel.growth_rate,
                market_size_estimate=intel.market_size_estimate,
                trend_indicators=intel.trend_indicators or {},
                key_insights=intel.key_insights or [],
                emerging_opportunities=intel.emerging_opportunities or [],
                risk_factors=intel.risk_factors or [],
                confidence_level=intel.confidence_level,
                analysis_period={
                    "start": intel.analysis_period_start,
                    "end": intel.analysis_period_end
                }
            ))
        
        return models
    
    async def get_recommended_opportunities(self, tenant_id: str) -> List[OpportunityModel]:
        """Get recommended opportunities and experiments"""
        opportunities = self.db.query(RecommendedOpportunity).filter(
            and_(
                RecommendedOpportunity.tenant_id == tenant_id,
                RecommendedOpportunity.status.in_(["suggested", "accepted"])
            )
        ).order_by(desc(RecommendedOpportunity.confidence_score)).limit(20).all()
        
        models = []
        for opp in opportunities:
            models.append(OpportunityModel(
                id=opp.id,
                opportunity_type=opp.opportunity_type,
                title=opp.title,
                description=opp.description,
                confidence_score=opp.confidence_score,
                estimated_impact=opp.estimated_impact or "medium",
                effort_level=opp.effort_level or "medium",
                time_to_result=opp.time_to_result,
                hypothesis=opp.hypothesis,
                success_metrics=opp.success_metrics or [],
                status=opp.status,
                created_at=opp.created_at
            ))
        
        return models
    
    async def create_analytics_snapshot(self, tenant_id: str, window_days: int = 7):
        """Create an analytics snapshot for trend tracking"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=window_days)
        
        # Get signal metrics
        signals_query = self.db.query(RadarSignal).filter(
            and_(
                RadarSignal.tenant_id == tenant_id,
                RadarSignal.created_at >= start_date,
                RadarSignal.created_at <= end_date
            )
        )
        
        total_signals = signals_query.count()
        
        # Get signals by strength
        strength_counts = {}
        for strength in ["high", "medium", "low"]:
            count = signals_query.filter(RadarSignal.strength == strength).count()
            strength_counts[strength] = count
        
        # Get signals by type
        type_counts = {}
        signal_types = self.db.query(
            RadarSignal.signal_type,
            func.count(RadarSignal.id).label('count')
        ).filter(
            and_(
                RadarSignal.tenant_id == tenant_id,
                RadarSignal.created_at >= start_date
            )
        ).group_by(RadarSignal.signal_type).all()
        
        for signal_type, count in signal_types:
            type_counts[signal_type] = count
        
        # Calculate quality metrics
        avg_confidence = signals_query.with_entities(
            func.avg(RadarSignal.confidence)
        ).scalar() or 0.0
        
        avg_freshness = signals_query.with_entities(
            func.avg(RadarSignal.freshness)
        ).scalar() or 0.0
        
        # Create snapshot
        snapshot = AnalyticsSnapshot(
            tenant_id=tenant_id,
            snapshot_date=end_date,
            window_days=window_days,
            total_signals=total_signals,
            signals_by_strength=strength_counts,
            signals_by_type=type_counts,
            avg_confidence=avg_confidence,
            avg_freshness=avg_freshness,
            processing_success_rate=0.95  # TODO: Calculate actual success rate
        )
        
        self.db.add(snapshot)
        self.db.commit()
        
        logger.info(f"Created analytics snapshot for tenant {tenant_id}")


class RadarSchedulerService:
    """Service for managing radar scheduler tasks"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    async def create_scheduled_task(
        self,
        tenant_id: str,
        task_name: str,
        scan_type: str,
        schedule_expression: str,
        source_ids: List[str],
        parameters: Optional[Dict] = None
    ) -> SchedulerTask:
        """Create a new scheduled task"""
        task = SchedulerTask(
            tenant_id=tenant_id,
            task_name=task_name,
            scan_type=scan_type,
            schedule_expression=schedule_expression,
            source_ids=source_ids,
            status="scheduled"
        )
        
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        
        logger.info(f"Created scheduled task {task.id}: {task_name}")
        return task
    
    def get_active_tasks(self, tenant_id: str) -> List[SchedulerTask]:
        """Get all active scheduled tasks"""
        return self.db.query(SchedulerTask).filter(
            and_(
                SchedulerTask.tenant_id == tenant_id,
                SchedulerTask.is_active == True
            )
        ).all()
    
    async def update_task_status(self, task_id: str, status: str) -> bool:
        """Update task status"""
        task = self.db.query(SchedulerTask).filter(SchedulerTask.id == task_id).first()
        if not task:
            return False
        
        task.status = status
        task.updated_at = datetime.utcnow()
        
        if status == "completed":
            task.success_count += 1
            task.last_run_at = datetime.utcnow()
        elif status == "failed":
            task.failure_count += 1
            task.last_run_at = datetime.utcnow()
        
        self.db.commit()
        return True


class RadarNotificationService:
    """Service for managing radar notifications"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    async def create_notification(
        self,
        tenant_id: str,
        user_id: str,
        notification_type: str,
        title: str,
        message: str,
        signal_id: Optional[str] = None,
        dossier_id: Optional[str] = None
    ) -> RadarNotification:
        """Create a new notification"""
        notification = RadarNotification(
            tenant_id=tenant_id,
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            signal_id=signal_id,
            dossier_id=dossier_id
        )
        
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        
        return notification
    
    async def get_user_notifications(
        self,
        tenant_id: str,
        user_id: str,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[RadarNotification]:
        """Get notifications for a user"""
        query = self.db.query(RadarNotification).filter(
            and_(
                RadarNotification.tenant_id == tenant_id,
                RadarNotification.user_id == user_id
            )
        )
        
        if unread_only:
            query = query.filter(RadarNotification.is_read == False)
        
        return query.order_by(desc(RadarNotification.created_at)).limit(limit).all()
    
    async def create_daily_digest(self, tenant_id: str, user_id: str) -> Dict[str, Any]:
        """Create a daily notification digest"""
        # Get recent notifications
        start_date = datetime.utcnow() - timedelta(days=1)
        notifications = self.db.query(RadarNotification).filter(
            and_(
                RadarNotification.tenant_id == tenant_id,
                RadarNotification.user_id == user_id,
                RadarNotification.created_at >= start_date
            )
        ).all()
        
        # Get recent signals
        recent_signals = self.db.query(RadarSignal).filter(
            and_(
                RadarSignal.tenant_id == tenant_id,
                RadarSignal.created_at >= start_date,
                RadarSignal.strength == "high"
            )
        ).limit(5).all()
        
        # Create digest
        digest = {
            "date": datetime.utcnow(),
            "total_notifications": len(notifications),
            "unread_notifications": len([n for n in notifications if not n.is_read]),
            "notifications_by_type": {},
            "highlights": notifications[:3],
            "recent_signals": recent_signals,
            "recommended_actions": [
                "Review high-confidence signals",
                "Consider updating competitor analysis",
                "Check for new market opportunities"
            ]
        }
        
        # Count by type
        for notification in notifications:
            digest["notifications_by_type"][notification.notification_type] = \
                digest["notifications_by_type"].get(notification.notification_type, 0) + 1
        
        return digest
