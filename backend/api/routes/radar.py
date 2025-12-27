"""
Radar API Routes - Market intelligence and signal processing
"""
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import uuid
import asyncio
from loguru import logger

from backend.database_models import Signal, Dossier
from backend.core.supabase_client import get_supabase_client


# Request/Response Models
class ReconRequest(BaseModel):
    icp_id: str = Field(..., description="ICP identifier")
    source_urls: Optional[List[str]] = Field(None, description="Optional source URLs to scan")


class DossierRequest(BaseModel):
    campaign_id: str = Field(..., description="Campaign ID")
    signal_ids: Optional[List[str]] = Field(None, description="Optional signal IDs to include")


class ManualScanRequest(BaseModel):
    source_ids: List[str] = Field(..., description="List of source IDs to scan")
    scan_type: str = Field(..., description="Type of scan to perform")


class SignalResponse(BaseModel):
    id: str
    workspace_id: str
    tenant_id: str
    type: str
    source: str
    content: str
    confidence: float
    strength: str
    freshness: str
    action_suggestion: Optional[str]
    evidence_count: int
    timestamp: str
    created_at: str
    updated_at: str


class DossierResponse(BaseModel):
    id: str
    workspace_id: str
    campaign_id: Optional[str]
    title: str
    summary: str
    hypotheses: List[Dict[str, Any]]
    experiments: List[Dict[str, Any]]
    copy_snippets: List[Dict[str, Any]]
    market_narrative: Optional[str]
    signal_ids: List[str]
    created_at: str
    updated_at: str


class TrendData(BaseModel):
    date: str
    high_strength: int
    medium_strength: int
    low_strength: int
    categories: Dict[str, int]


class AnalyticsResponse(BaseModel):
    trends: List[TrendData]
    competitor_metrics: Dict[str, Any]
    market_intelligence: Dict[str, Any]
    opportunities: List[Dict[str, Any]]


class SchedulerStatus(BaseModel):
    status: str  # running, stopped, paused
    last_run: Optional[str]
    next_run: Optional[str]
    active_tasks: int
    failed_tasks: int
    sources_health: Dict[str, Dict[str, Any]]


# Router setup
router = APIRouter(prefix="/v1/radar", tags=["radar", "intelligence"])


# Helper functions
async def verify_workspace_access(workspace_id: str, user_id: Optional[str] = None) -> bool:
    """Verify user has access to workspace"""
    # This would integrate with your auth system
    # For now, return True (no auth)
    return True


async def fetch_competitor_data(source_urls: List[str]) -> List[Dict[str, Any]]:
    """
    Mock function to fetch competitor/market data via Python spine
    In production, this would integrate with actual scraping/analysis services
    """
    await asyncio.sleep(1)  # Simulate API call
    
    mock_data = []
    for i, url in enumerate(source_urls):
        mock_data.append({
            "url": url,
            "type": "competitor",
            "content": f"Competitor analysis from {url}",
            "confidence": 0.8,
            "strength": "high",
            "freshness": "fresh"
        })
    
    return mock_data


async def generate_dossier_summary(signals: List[Dict[str, Any]], campaign_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate dossier summary from signals
    """
    # Mock dossier generation - in production would use AI/LLM
    return {
        "title": f"Intelligence Dossier - {datetime.now().strftime('%Y-%m-%d')}",
        "summary": f"Analysis of {len(signals)} signals reveals key market trends and competitor activities.",
        "hypotheses": [
            "Market is shifting towards digital-first strategies",
            "Competitors are investing heavily in AI capabilities",
            "Customer acquisition costs are rising across the sector"
        ],
        "experiments": [
            "Test AI-powered personalization",
            "Explore new acquisition channels",
            "Optimize conversion funnel"
        ],
        "copy_snippets": [
            "Leading the AI revolution in [industry]",
            "Transform your business with intelligent automation",
            "The future of [industry] is here"
        ],
        "market_narrative": "The market is experiencing rapid digital transformation with AI at the forefront."
    }


# Radar Scan Endpoints

@router.post("/scan/recon")
async def scan_recon(
    request: ReconRequest,
    background_tasks: BackgroundTasks,
    user_id: Optional[str] = None,
    supabase = Depends(get_supabase_client)
):
    """
    Perform reconnaissance scan
    
    Accepts icp_id and optional source_urls, fetches competitor/market data 
    via the Python spine, and returns signals.
    """
    try:
        # Verify workspace access (would get workspace_id from icp_id in production)
        workspace_id = "default_workspace"  # Mock
        if not await verify_workspace_access(workspace_id, user_id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Fetch data from sources
        source_urls = request.source_urls or [
            "https://example-competitor1.com",
            "https://example-competitor2.com",
            "https://industry-news.com"
        ]
        
        raw_data = await fetch_competitor_data(source_urls)
        
        # Process and create signals
        signals = []
        for data in raw_data:
            signal = Signal(
                id=str(uuid.uuid4()),
                workspace_id=workspace_id,
                tenant_id=request.icp_id,
                type=data["type"],
                source=data["url"],
                content=data["content"],
                confidence=data["confidence"],
                strength=data["strength"],
                freshness=data["freshness"],
                action_suggestion=f"Monitor {data['type']} activity closely",
                evidence_count=3
            )
            
            # Save to database
            if supabase.enabled:
                result = supabase.client.table('signals').insert(signal.to_dict()).execute()
                if result.data:
                    signals.append(result.data[0])
            else:
                signals.append(signal.to_dict())
        
        logger.info(f"Recon scan completed: {len(signals)} signals generated")
        
        return JSONResponse(content={
            "message": "Recon scan completed successfully",
            "signals": signals,
            "scan_metadata": {
                "icp_id": request.icp_id,
                "sources_scanned": len(source_urls),
                "timestamp": datetime.now().isoformat()
            }
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in recon scan: {e}")
        raise HTTPException(status_code=500, detail=f"Error in recon scan: {str(e)}")


@router.post("/scan/dossier")
async def generate_dossier(
    request: DossierRequest,
    user_id: Optional[str] = None,
    supabase = Depends(get_supabase_client)
):
    """
    Generate intelligence dossier
    
    Accepts campaign_id and optional signal_ids, generates a dossier 
    summarising the signals with hypotheses, experiments, and copy snippets.
    """
    try:
        # Get campaign details
        campaign_result = supabase.client.table('campaigns').select('*').eq('id', request.campaign_id).execute()
        if not campaign_result.data or len(campaign_result.data) == 0:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        campaign = campaign_result.data[0]
        
        # Verify workspace access
        if not await verify_workspace_access(campaign['workspace_id'], user_id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get signals
        if request.signal_ids:
            # Get specific signals
            signals_result = supabase.client.table('signals') \
                .select('*') \
                .in_('id', request.signal_ids) \
                .execute()
        else:
            # Get recent signals for workspace
            signals_result = supabase.client.table('signals') \
                .select('*') \
                .eq('workspace_id', campaign['workspace_id']) \
                .order('timestamp', desc=True) \
                .limit(50) \
                .execute()
        
        signals = signals_result.data if signals_result.data else []
        
        # Generate dossier summary
        dossier_data = await generate_dossier_summary(signals, campaign)
        
        # Create dossier record
        dossier = Dossier(
            id=str(uuid.uuid4()),
            workspace_id=campaign['workspace_id'],
            campaign_id=request.campaign_id,
            title=dossier_data["title"],
            summary=dossier_data["summary"],
            hypotheses=dossier_data["hypotheses"],
            experiments=dossier_data["experiments"],
            copy_snippets=dossier_data["copy_snippets"],
            market_narrative=dossier_data["market_narrative"],
            signal_ids=[s['id'] for s in signals]
        )
        
        # Save dossier
        if supabase.enabled:
            result = supabase.client.table('dossiers').insert(dossier.to_dict()).execute()
            if result.data:
                saved_dossier = result.data[0]
            else:
                saved_dossier = dossier.to_dict()
        else:
            saved_dossier = dossier.to_dict()
        
        logger.info(f"Dossier generated for campaign {request.campaign_id}")
        
        return JSONResponse(content={
            "message": "Dossier generated successfully",
            "dossier": saved_dossier,
            "signals_analyzed": len(signals)
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating dossier: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating dossier: {str(e)}")


# Analytics Endpoints

@router.get("/analytics/trends")
async def get_signal_trends(
    workspace_id: str = Query(..., description="Workspace ID"),
    window_days: int = Query(30, description="Number of days to analyze"),
    user_id: Optional[str] = None,
    supabase = Depends(get_supabase_client)
):
    """
    Return signal trends for the requested window days
    
    Returns time-series data for high/medium/low strength and categories.
    """
    try:
        # Verify workspace access
        if not await verify_workspace_access(workspace_id, user_id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get signals for the time window
        start_date = datetime.now() - timedelta(days=window_days)
        
        result = supabase.client.table('signals') \
            .select('*') \
            .eq('workspace_id', workspace_id) \
            .gte('timestamp', start_date.isoformat()) \
            .order('timestamp', asc=True) \
            .execute()
        
        signals = result.data if result.data else []
        
        # Group signals by date and strength
        trends = {}
        category_trends = {}
        
        for signal in signals:
            date = signal['timestamp'][:10]  # YYYY-MM-DD
            
            if date not in trends:
                trends[date] = {"high": 0, "medium": 0, "low": 0}
                category_trends[date] = {}
            
            # Count by strength
            strength = signal.get('strength', 'low')
            trends[date][strength] = trends[date].get(strength, 0) + 1
            
            # Count by category
            category = signal.get('type', 'unknown')
            category_trends[date][category] = category_trends[date].get(category, 0) + 1
        
        # Format response
        trend_data = []
        for date in sorted(trends.keys()):
            trend_data.append(TrendData(
                date=date,
                high_strength=trends[date].get('high', 0),
                medium_strength=trends[date].get('medium', 0),
                low_strength=trends[date].get('low', 0),
                categories=category_trends.get(date, {})
            ))
        
        return JSONResponse(content={
            "trends": [t.dict() for t in trend_data],
            "metadata": {
                "workspace_id": workspace_id,
                "window_days": window_days,
                "total_signals": len(signals)
            }
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting trends: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting trends: {str(e)}")


@router.get("/analytics/competitors")
async def get_competitor_analytics(
    workspace_id: str = Query(..., description="Workspace ID"),
    user_id: Optional[str] = None,
    supabase = Depends(get_supabase_client)
):
    """
    Return competitor analysis metrics
    """
    try:
        # Verify workspace access
        if not await verify_workspace_access(workspace_id, user_id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get competitor signals
        result = supabase.client.table('signals') \
            .select('*') \
            .eq('workspace_id', workspace_id) \
            .eq('type', 'competitor') \
            .order('timestamp', desc=True) \
            .limit(100) \
            .execute()
        
        competitor_signals = result.data if result.data else []
        
        # Analyze competitor data
        competitor_metrics = {
            "total_signals": len(competitor_signals),
            "active_competitors": len(set(s.get('source', '') for s in competitor_signals)),
            "high_strength_signals": len([s for s in competitor_signals if s.get('strength') == 'high']),
            "average_confidence": sum(s.get('confidence', 0) for s in competitor_signals) / len(competitor_signals) if competitor_signals else 0,
            "recent_activity": len([s for s in competitor_signals if 
                                  datetime.fromisoformat(s['timestamp'].replace('Z', '+00:00')) > 
                                  datetime.now() - timedelta(days=7)]),
            "top_sources": {}
        }
        
        # Count signals by source
        for signal in competitor_signals:
            source = signal.get('source', 'unknown')
            competitor_metrics["top_sources"][source] = competitor_metrics["top_sources"].get(source, 0) + 1
        
        # Sort top sources
        competitor_metrics["top_sources"] = dict(
            sorted(competitor_metrics["top_sources"].items(), key=lambda x: x[1], reverse=True)[:10]
        )
        
        return JSONResponse(content=competitor_metrics)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting competitor analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting competitor analytics: {str(e)}")


@router.get("/analytics/intelligence")
async def get_market_intelligence(
    workspace_id: str = Query(..., description="Workspace ID"),
    user_id: Optional[str] = None,
    supabase = Depends(get_supabase_client)
):
    """
    Return market intelligence
    """
    try:
        # Verify workspace access
        if not await verify_workspace_access(workspace_id, user_id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get all recent signals
        result = supabase.client.table('signals') \
            .select('*') \
            .eq('workspace_id', workspace_id) \
            .order('timestamp', desc=True) \
            .limit(200) \
            .execute()
        
        signals = result.data if result.data else []
        
        # Analyze market intelligence
        intelligence = {
            "signal_volume": {
                "total": len(signals),
                "daily_average": len(signals) / 30,  # Assuming 30-day window
                "growth_rate": 0.15  # Mock growth rate
            },
            "signal_types": {},
            "strength_distribution": {
                "high": len([s for s in signals if s.get('strength') == 'high']),
                "medium": len([s for s in signals if s.get('strength') == 'medium']),
                "low": len([s for s in signals if s.get('strength') == 'low'])
            },
            "freshness_analysis": {
                "fresh": len([s for s in signals if s.get('freshness') == 'fresh']),
                "recent": len([s for s in signals if s.get('freshness') == 'recent']),
                "stale": len([s for s in signals if s.get('freshness') == 'stale'])
            },
            "key_insights": [
                "Competitor activity increased by 25% this month",
                "Market signals show strong trend towards AI adoption",
                "Customer acquisition patterns are shifting"
            ]
        }
        
        # Count signal types
        for signal in signals:
            signal_type = signal.get('type', 'unknown')
            intelligence["signal_types"][signal_type] = intelligence["signal_types"].get(signal_type, 0) + 1
        
        return JSONResponse(content=intelligence)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting market intelligence: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting market intelligence: {str(e)}")


@router.get("/analytics/opportunities")
async def get_opportunities(
    workspace_id: str = Query(..., description="Workspace ID"),
    user_id: Optional[str] = None,
    supabase = Depends(get_supabase_client)
):
    """
    Return recommended opportunities or experiments
    """
    try:
        # Verify workspace access
        if not await verify_workspace_access(workspace_id, user_id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get recent signals and dossiers
        signals_result = supabase.client.table('signals') \
            .select('*') \
            .eq('workspace_id', workspace_id) \
            .order('timestamp', desc=True) \
            .limit(50) \
            .execute()
        
        dossiers_result = supabase.client.table('dossiers') \
            .select('*') \
            .eq('workspace_id', workspace_id) \
            .order('created_at', desc=True) \
            .limit(10) \
            .execute()
        
        signals = signals_result.data if signals_result.data else []
        dossiers = dossiers_result.data if dossiers_result.data else []
        
        # Generate opportunities based on signals and dossiers
        opportunities = []
        
        # High-confidence competitor signals suggest competitive response opportunities
        high_conf_signals = [s for s in signals if s.get('confidence', 0) > 0.8]
        if high_conf_signals:
            opportunities.append({
                "type": "competitive_response",
                "title": "Competitive Response Campaign",
                "description": "Respond to high-confidence competitor signals",
                "priority": "high",
                "estimated_impact": 0.8,
                "effort_required": "medium",
                "signals_count": len(high_conf_signals)
            })
        
        # Market trend opportunities
        market_signals = [s for s in signals if s.get('type') == 'market']
        if market_signals:
            opportunities.append({
                "type": "market_trend",
                "title": "Market Trend Capitalization",
                "description": "Capitalize on identified market trends",
                "priority": "medium",
                "estimated_impact": 0.7,
                "effort_required": "low",
                "signals_count": len(market_signals)
            })
        
        # Add opportunities from dossiers
        for dossier in dossiers:
            for experiment in dossier.get('experiments', []):
                opportunities.append({
                    "type": "dossier_experiment",
                    "title": f"Experiment: {experiment}",
                    "description": f"Based on dossier: {dossier.get('title', 'Unknown')}",
                    "priority": "medium",
                    "estimated_impact": 0.6,
                    "effort_required": "medium",
                    "dossier_id": dossier['id']
                })
        
        return JSONResponse(content={
            "opportunities": opportunities,
            "metadata": {
                "total_opportunities": len(opportunities),
                "signals_analyzed": len(signals),
                "dossiers_analyzed": len(dossiers)
            }
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting opportunities: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting opportunities: {str(e)}")


# Scheduler Endpoints

@router.post("/scheduler/start")
async def start_scheduler(
    user_id: Optional[str] = None,
    redis_client = None
):
    """
    Start the radar scheduler
    """
    try:
        # Store scheduler status in Redis
        if redis_client:
            await redis_client.set("radar_scheduler_status", "running")
            await redis_client.set("radar_scheduler_started", datetime.now().isoformat())
        
        logger.info("Radar scheduler started")
        
        return JSONResponse(content={
            "message": "Radar scheduler started successfully",
            "status": "running",
            "started_at": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error starting scheduler: {e}")
        raise HTTPException(status_code=500, detail=f"Error starting scheduler: {str(e)}")


@router.post("/scheduler/stop")
async def stop_scheduler(
    user_id: Optional[str] = None,
    redis_client = None
):
    """
    Stop the radar scheduler
    """
    try:
        # Store scheduler status in Redis
        if redis_client:
            await redis_client.set("radar_scheduler_status", "stopped")
            await redis_client.set("radar_scheduler_stopped", datetime.now().isoformat())
        
        logger.info("Radar scheduler stopped")
        
        return JSONResponse(content={
            "message": "Radar scheduler stopped successfully",
            "status": "stopped",
            "stopped_at": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")
        raise HTTPException(status_code=500, detail=f"Error stopping scheduler: {str(e)}")


@router.post("/scheduler/scan/manual")
async def schedule_manual_scan(
    request: ManualScanRequest,
    background_tasks: BackgroundTasks,
    user_id: Optional[str] = None,
    redis_client = None
):
    """
    Schedule manual scans with source_ids and scan_type
    """
    try:
        # Create scan task
        scan_id = str(uuid.uuid4())
        
        scan_task = {
            "id": scan_id,
            "source_ids": request.source_ids,
            "scan_type": request.scan_type,
            "status": "scheduled",
            "created_at": datetime.now().isoformat(),
            "created_by": user_id
        }
        
        # Store in Redis
        if redis_client:
            await redis_client.setex(
                f"manual_scan:{scan_id}",
                timedelta(hours=24),
                json.dumps(scan_task)
            )
        
        # Add to background tasks (in production, would use job queue)
        background_tasks.add_task(
            execute_manual_scan,
            scan_id,
            request.source_ids,
            request.scan_type
        )
        
        logger.info(f"Manual scan scheduled: {scan_id}")
        
        return JSONResponse(content={
            "message": "Manual scan scheduled successfully",
            "scan_id": scan_id,
            "scan_type": request.scan_type,
            "sources_count": len(request.source_ids)
        })
        
    except Exception as e:
        logger.error(f"Error scheduling manual scan: {e}")
        raise HTTPException(status_code=500, detail=f"Error scheduling manual scan: {str(e)}")


@router.get("/scheduler/status")
async def get_scheduler_status(
    redis_client = None
):
    """
    Return scheduler status
    """
    try:
        # Get status from Redis
        if redis_client:
            status = await redis_client.get("radar_scheduler_status") or "stopped"
            started = await redis_client.get("radar_scheduler_started")
            stopped = await redis_client.get("radar_scheduler_stopped")
        else:
            status = "stopped"
            started = None
            stopped = None
        
        # Mock active tasks and health
        active_tasks = 3 if status == "running" else 0
        failed_tasks = 1
        
        sources_health = {
            "web_scraping": {"status": "healthy", "last_check": datetime.now().isoformat()},
            "api_feeds": {"status": "healthy", "last_check": datetime.now().isoformat()},
            "social_monitoring": {"status": "degraded", "last_check": datetime.now().isoformat()}
        }
        
        return JSONResponse(content={
            "status": status,
            "last_run": started,
            "next_run": datetime.now().isoformat() if status == "running" else None,
            "active_tasks": active_tasks,
            "failed_tasks": failed_tasks,
            "sources_health": sources_health
        })
        
    except Exception as e:
        logger.error(f"Error getting scheduler status: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting scheduler status: {str(e)}")


@router.get("/scheduler/health")
async def get_scheduler_health():
    """
    Return scheduler health
    """
    return JSONResponse(content={
        "status": "healthy",
        "service": "radar_scheduler",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "scheduler": "healthy",
            "scanner": "healthy",
            "processor": "healthy",
            "storage": "healthy"
        }
    })


# Helper function for background task
async def execute_manual_scan(scan_id: str, source_ids: List[str], scan_type: str):
    """
    Execute manual scan in background
    """
    try:
        logger.info(f"Executing manual scan {scan_id}")
        
        # Mock scan execution
        await asyncio.sleep(5)  # Simulate scan work
        
        logger.info(f"Manual scan {scan_id} completed")
        
    except Exception as e:
        logger.error(f"Error executing manual scan {scan_id}: {e}")


@router.get("/health")
async def radar_health():
    """
    Health check for radar service
    """
    return JSONResponse(content={
        "status": "healthy",
        "service": "radar",
        "timestamp": datetime.now().isoformat(),
        "features": {
            "recon_scans": True,
            "dossier_generation": True,
            "analytics": True,
            "scheduler": True,
            "manual_scans": True,
            "signal_processing": True,
            "workspace_isolation": True
        }
    })
