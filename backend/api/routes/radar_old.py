"""
Radar API Routes - Signal Intelligence System Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import uuid
import asyncio

from backend.models.radar_api import (
    ScanReconRequest, ScanReconResponse, ScanDossierRequest, ScanDossierResponse,
    TrendsAnalyticsResponse, CompetitorsAnalyticsResponse, IntelligenceAnalyticsResponse,
    OpportunitiesAnalyticsResponse, SchedulerStatusResponse, SchedulerHealthResponse,
    NotificationDigestResponse, NotificationProcessResponse, ErrorResponse,
    ManualScanRequest, SchedulerStartRequest, NotificationProcessRequest
)
from backend.models.radar import RadarSignal, RadarDossier
from backend.services.radar_service import (
    RadarSignalService, RadarDossierService, RadarAnalyticsService,
    RadarSchedulerService, RadarNotificationService
)
from backend.core.database import get_db
from backend.core.caching import cache_manager
from loguru import logger

router = APIRouter(prefix="/v1/radar", tags=["radar"])

# Dependency to get tenant_id from request (simplified for now)
async def get_current_tenant() -> str:
    """Get current tenant ID - in production this would come from JWT/auth"""
    return "default_tenant"  # Placeholder


# Scan Endpoints
@router.post("/scan/recon", response_model=ScanReconResponse)
async def scan_recon(
    request: ScanReconRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant)
):
    """
    Perform reconnaissance scan for competitor/market data
    """
    try:
        scan_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        # Initialize services
        signal_service = RadarSignalService(db)
        
        # Start async scan in background
        background_tasks.add_task(
            perform_recon_scan,
            tenant_id,
            scan_id,
            request.icp_id,
            request.source_urls,
            request.scan_depth,
            signal_service
        )
        
        # Return immediate response with scan ID
        return ScanReconResponse(
            success=True,
            signals_found=0,  # Will be updated by background task
            signals=[],
            scan_id=scan_id,
            processing_time_seconds=0.0
        )
        
    except Exception as e:
        logger.error(f"Recon scan failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scan/dossier", response_model=ScanDossierResponse)
async def scan_dossier(
    request: ScanDossierRequest,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant)
):
    """
    Generate intelligence dossier for a campaign
    """
    try:
        start_time = datetime.utcnow()
        
        # Initialize services
        dossier_service = RadarDossierService(db)
        signal_service = RadarSignalService(db)
        
        # Get signals to include
        if request.signal_ids:
            signals = []
            for signal_id in request.signal_ids:
                signal = signal_service.get_signal_by_id(signal_id)
                if signal and signal.tenant_id == tenant_id:
                    signals.append(signal)
        else:
            # Get recent high-confidence signals for the campaign
            signals = signal_service.get_signals(
                tenant_id=tenant_id,
                strength="high",
                limit=20
            )
        
        if not signals:
            raise HTTPException(
                status_code=404,
                detail="No signals found for dossier generation"
            )
        
        # Generate dossier content (simplified for now)
        title = request.title or f"Intelligence Dossier for {request.campaign_id}"
        summary = f"Analysis of {len(signals)} intelligence signals for campaign {request.campaign_id}"
        
        hypotheses = []
        experiments = []
        copy_snippets = []
        
        if request.include_hypotheses:
            hypotheses = generate_hypotheses(signals)
        
        if request.include_experiments:
            experiments = generate_experiments(signals)
        
        copy_snippets = generate_copy_snippets(signals)
        
        # Create dossier
        dossier = await dossier_service.create_dossier(
            tenant_id=tenant_id,
            campaign_id=request.campaign_id,
            title=title,
            signal_ids=[s.id for s in signals],
            summary=summary,
            hypotheses=hypotheses,
            experiments=experiments,
            copy_snippets=copy_snippets
        )
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        return ScanDossierResponse(
            success=True,
            dossier=dossier,
            processing_time_seconds=processing_time,
            signals_included=len(signals)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Dossier generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Analytics Endpoints
@router.get("/analytics/trends", response_model=TrendsAnalyticsResponse)
async def get_trends(
    window_days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant)
):
    """
    Get signal trends for the requested time window
    """
    try:
        analytics_service = RadarAnalyticsService(db)
        
        trend_data = await analytics_service.get_signal_trends(tenant_id, window_days)
        
        total_signals = sum(t.total_signals for t in trend_data)
        avg_daily = total_signals / max(window_days, 1)
        
        summary = {
            "total_signals": total_signals,
            "avg_daily_signals": avg_daily,
            "peak_day": max(trend_data, key=lambda x: x.total_signals).date if trend_data else None,
            "trend_direction": "up" if len(trend_data) > 1 and trend_data[-1].total_signals > trend_data[0].total_signals else "down"
        }
        
        return TrendsAnalyticsResponse(
            window_days=window_days,
            data=trend_data,
            summary=summary,
            total_signals=total_signals,
            avg_daily_signals=avg_daily
        )
        
    except Exception as e:
        logger.error(f"Trends analytics failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/competitors", response_model=CompetitorsAnalyticsResponse)
async def get_competitors(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant)
):
    """
    Get competitor analysis metrics
    """
    try:
        analytics_service = RadarAnalyticsService(db)
        
        competitor_metrics = await analytics_service.get_competitor_metrics(tenant_id)
        
        market_overview = {
            "total_competitors": len(competitor_metrics),
            "avg_sentiment": sum(c.sentiment_score or 0 for c in competitor_metrics) / max(len(competitor_metrics), 1),
            "market_leaders": [c.competitor_name for c in competitor_metrics if c.market_position == "leader"],
            "emerging_threats": [c.competitor_name for c in competitor_metrics if c.market_position == "challenger"]
        }
        
        return CompetitorsAnalyticsResponse(
            competitors=competitor_metrics,
            total_competitors=len(competitor_metrics),
            analysis_date=datetime.utcnow(),
            market_overview=market_overview
        )
        
    except Exception as e:
        logger.error(f"Competitor analytics failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/intelligence", response_model=IntelligenceAnalyticsResponse)
async def get_intelligence(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant)
):
    """
    Get market intelligence
    """
    try:
        analytics_service = RadarAnalyticsService(db)
        
        intelligence_data = await analytics_service.get_market_intelligence(tenant_id)
        
        total_segments = len(intelligence_data)
        overall_growth = sum(i.growth_rate or 0 for i in intelligence_data) / max(total_segments, 1)
        
        key_trends = []
        for intel in intelligence_data:
            key_trends.extend(intel.key_insights[:2])  # Top 2 insights per segment
        
        return IntelligenceAnalyticsResponse(
            intelligence=intelligence_data,
            total_segments=total_segments,
            overall_growth_rate=overall_growth,
            key_trends=key_trends[:10],  # Top 10 trends
            analysis_date=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Intelligence analytics failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/opportunities", response_model=OpportunitiesAnalyticsResponse)
async def get_opportunities(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant)
):
    """
    Get recommended opportunities and experiments
    """
    try:
        analytics_service = RadarAnalyticsService(db)
        
        opportunities = await analytics_service.get_recommended_opportunities(tenant_id)
        
        # Group by type and impact
        by_type = {}
        by_impact = {}
        
        for opp in opportunities:
            by_type[opp.opportunity_type] = by_type.get(opp.opportunity_type, 0) + 1
            by_impact[opp.estimated_impact] = by_impact.get(opp.estimated_impact, 0) + 1
        
        avg_confidence = sum(opp.confidence_score for opp in opportunities) / max(len(opportunities), 1)
        
        return OpportunitiesAnalyticsResponse(
            opportunities=opportunities,
            total_opportunities=len(opportunities),
            by_type=by_type,
            by_impact=by_impact,
            avg_confidence=avg_confidence
        )
        
    except Exception as e:
        logger.error(f"Opportunities analytics failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Scheduler Endpoints
@router.post("/scheduler/start")
async def start_scheduler(
    request: SchedulerStartRequest,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant)
):
    """
    Start a new scheduled radar scan
    """
    try:
        scheduler_service = RadarSchedulerService(db)
        
        task = await scheduler_service.create_scheduled_task(
            tenant_id=tenant_id,
            task_name=request.task_name,
            scan_type=request.scan_type.value,
            schedule_expression=request.schedule_expression,
            source_ids=request.source_ids,
            parameters=request.parameters
        )
        
        # Store scheduler status in Redis
        await cache_manager.set(f"scheduler:status:{tenant_id}", "running")
        
        return {
            "success": True,
            "task_id": task.id,
            "message": f"Scheduled task '{request.task_name}' created successfully"
        }
        
    except Exception as e:
        logger.error(f"Scheduler start failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scheduler/stop")
async def stop_scheduler(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant)
):
    """
    Stop the radar scheduler
    """
    try:
        # Update scheduler status in Redis
        await cache_manager.set(f"scheduler:status:{tenant_id}", "stopped")
        
        return {
            "success": True,
            "message": "Scheduler stopped successfully"
        }
        
    except Exception as e:
        logger.error(f"Scheduler stop failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scheduler/scan/manual")
async def schedule_manual_scan(
    request: ManualScanRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant)
):
    """
    Schedule a manual scan
    """
    try:
        scan_id = str(uuid.uuid4())
        
        # Queue the manual scan
        background_tasks.add_task(
            perform_manual_scan,
            tenant_id,
            scan_id,
            request.scan_type.value,
            request.source_ids,
            request.parameters or {}
        )
        
        return {
            "success": True,
            "scan_id": scan_id,
            "message": f"Manual {request.scan_type.value} scan queued successfully"
        }
        
    except Exception as e:
        logger.error(f"Manual scan scheduling failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scheduler/status", response_model=SchedulerStatusResponse)
async def get_scheduler_status(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant)
):
    """
    Get scheduler status and active tasks
    """
    try:
        scheduler_service = RadarSchedulerService(db)
        
        # Get status from Redis
        status = await cache_manager.get(f"scheduler:status:{tenant_id}") or "stopped"
        
        is_running = status == "running"
        
        # Get active tasks
        active_tasks = scheduler_service.get_active_tasks(tenant_id)
        
        scheduler_status = {
            "is_running": is_running,
            "active_tasks": len(active_tasks),
            "total_tasks": len(active_tasks),
            "uptime_seconds": 3600.0,  # Placeholder
            "version": "1.0.0"
        }
        
        return SchedulerStatusResponse(
            scheduler=scheduler_status,
            tasks=active_tasks,
            recent_executions=[]  # TODO: Get recent executions
        )
        
    except Exception as e:
        logger.error(f"Scheduler status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scheduler/health", response_model=SchedulerHealthResponse)
async def get_scheduler_health(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant)
):
    """
    Get scheduler and source health status
    """
    try:
        # Placeholder health check
        sources = [
            {
                "source_id": "web_scanner",
                "source_name": "Web Scanner",
                "is_healthy": True,
                "last_check": datetime.utcnow(),
                "response_time_ms": 150.0,
                "error_rate": 0.02,
                "signals_last_24h": 45,
                "status_message": "Operating normally"
            }
        ]
        
        return SchedulerHealthResponse(
            overall_health="healthy",
            sources=sources,
            scheduler_uptime=86400.0,
            last_restart=datetime.utcnow() - timedelta(days=1)
        )
        
    except Exception as e:
        logger.error(f"Scheduler health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Notification Endpoints
@router.post("/notifications/process", response_model=NotificationProcessResponse)
async def process_notifications(
    request: NotificationProcessRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant)
):
    """
    Process signal notifications
    """
    try:
        notification_service = RadarNotificationService(db)
        
        # Queue notification processing
        background_tasks.add_task(
            process_user_notifications,
            tenant_id,
            request.user_id,
            request.notification_types,
            request.mark_as_read,
            notification_service
        )
        
        return NotificationProcessResponse(
            success=True,
            notifications_processed=0,  # Will be updated by background task
            notifications_sent=0
        )
        
    except Exception as e:
        logger.error(f"Notification processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notifications/digest/daily", response_model=NotificationDigestResponse)
async def get_daily_digest(
    user_id: str = Query(...),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant)
):
    """
    Get daily notification digest
    """
    try:
        notification_service = RadarNotificationService(db)
        
        digest = await notification_service.create_daily_digest(tenant_id, user_id)
        
        return NotificationDigestResponse(
            digest=digest,
            success=True
        )
        
    except Exception as e:
        logger.error(f"Daily digest generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Helper functions for background tasks
async def perform_recon_scan(
    tenant_id: str,
    scan_id: str,
    icp_id: str,
    source_urls: Optional[List[str]],
    scan_depth: str,
    signal_service: RadarSignalService
):
    """Background task to perform reconnaissance scan"""
    try:
        # Simulate scanning process
        await asyncio.sleep(2)  # Simulate API calls
        
        # Create sample signals (in production, this would be real data)
        sample_signals = [
            {
                "type": "competitor",
                "source": "https://example-competitor.com",
                "content": "Competitor launched new product feature targeting similar customer segment",
                "confidence": 0.85,
                "strength": "high",
                "action_suggestion": "Analyze competitor feature and consider differentiation strategy"
            },
            {
                "type": "market",
                "source": "https://industry-news.com",
                "content": "Market research shows growing demand for sustainable artisan products",
                "confidence": 0.75,
                "strength": "medium",
                "action_suggestion": "Consider highlighting sustainability in marketing campaigns"
            }
        ]
        
        created_signals = []
        for signal_data in sample_signals:
            signal = await signal_service.create_signal(
                tenant_id=tenant_id,
                **signal_data
            )
            created_signals.append(signal)
        
        logger.info(f"Recon scan {scan_id} completed with {len(created_signals)} signals")
        
    except Exception as e:
        logger.error(f"Recon scan {scan_id} failed: {e}")


async def perform_manual_scan(
    tenant_id: str,
    scan_id: str,
    scan_type: str,
    source_ids: List[str],
    parameters: Dict[str, Any]
):
    """Background task to perform manual scan"""
    try:
        # Simulate manual scanning
        await asyncio.sleep(1)
        
        logger.info(f"Manual scan {scan_id} of type {scan_type} completed")
        
    except Exception as e:
        logger.error(f"Manual scan {scan_id} failed: {e}")


async def process_user_notifications(
    tenant_id: str,
    user_id: str,
    notification_types: Optional[List[str]],
    mark_as_read: bool,
    notification_service: RadarNotificationService
):
    """Background task to process user notifications"""
    try:
        # Get notifications to process
        notifications = await notification_service.get_user_notifications(
            tenant_id, user_id, unread_only=True
        )
        
        processed_count = len(notifications)
        sent_count = 0
        
        # Process each notification
        for notification in notifications:
            # In production, this would send email/push notifications
            sent_count += 1
            
            if mark_as_read:
                notification.is_read = True
                notification.read_at = datetime.utcnow()
        
        logger.info(f"Processed {processed_count} notifications for user {user_id}")
        
    except Exception as e:
        logger.error(f"Notification processing failed for user {user_id}: {e}")


# Content generation helpers
def generate_hypotheses(signals: List[RadarSignal]) -> List[Dict[str, Any]]:
    """Generate hypotheses from signals"""
    return [
        {
            "hypothesis": "Competitors are focusing on sustainability features",
            "confidence": 0.8,
            "supporting_signals": [s.id for s in signals if "sustainability" in s.content.lower()],
            "test_method": "A/B test messaging with sustainability focus"
        },
        {
            "hypothesis": "Market demand for artisan products is growing",
            "confidence": 0.7,
            "supporting_signals": [s.id for s in signals if "demand" in s.content.lower()],
            "test_method": "Launch targeted campaign in new geographic region"
        }
    ]


def generate_experiments(signals: List[RadarSignal]) -> List[Dict[str, Any]]:
    """Generate experiment suggestions from signals"""
    return [
        {
            "title": "Sustainability Messaging Test",
            "description": "Test different sustainability-focused messaging variants",
            "expected_outcome": "Higher engagement from environmentally conscious customers",
            "duration_days": 14,
            "success_metrics": ["Click-through rate", "Conversion rate", "Engagement time"]
        },
        {
            "title": "Competitor Feature Response",
            "description": "Develop and test response to competitor's new features",
            "expected_outcome": "Maintain competitive positioning",
            "duration_days": 21,
            "success_metrics": ["Market share retention", "Customer satisfaction"]
        }
    ]


def generate_copy_snippets(signals: List[RadarSignal]) -> List[str]:
    """Generate marketing copy snippets from signals"""
    return [
        "Handcrafted with sustainability in mind - join the eco-conscious movement",
        "Discover why artisans are choosing our platform over competitors",
        "The market is shifting - be ahead of the trend with artisan products"
    ]
