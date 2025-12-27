"""
Database initialization script for Artisan Hub
Creates initial tables and sample data
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.core.database import get_db, create_tables
from backend.models.muse import Plan, WorkspaceSettings
from backend.models.radar import CompetitorAnalysis, MarketIntelligence, RecommendedOpportunity
from backend.core.caching import cache_manager
from loguru import logger


async def initialize_database():
    """Initialize database with tables and sample data"""
    try:
        logger.info("Starting database initialization...")
        
        # Create tables
        create_tables()
        logger.info("Database tables created successfully")
        
        # Initialize cache
        await cache_manager.initialize()
        logger.info("Cache initialized successfully")
        
        # Get database session
        db = next(get_db())
        
        try:
            # Create sample subscription plans
            await create_sample_plans(db)
            
            # Create sample workspace settings
            await create_sample_workspace_settings(db)
            
            # Create sample radar data
            await create_sample_radar_data(db)
            
            db.commit()
            logger.info("Sample data created successfully")
            
        finally:
            db.close()
        
        logger.info("Database initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


async def create_sample_plans(db: Session):
    """Create sample subscription plans"""
    plans_data = [
        {
            "plan_id": "starter",
            "name": "Starter Plan",
            "description": "Perfect for individual artisans and small teams",
            "price": 9.99,
            "currency": "USD",
            "billing_interval": "monthly",
            "features": [
                "Up to 50 creative assets",
                "Basic AI-powered content generation",
                "Email support",
                "Community access"
            ],
            "limits": {
                "assets": 50,
                "users": 2,
                "api_calls": 1000,
                "speed_daemon_tasks": 10
            }
        },
        {
            "plan_id": "professional",
            "name": "Professional Plan",
            "description": "Ideal for growing artisan businesses",
            "price": 29.99,
            "currency": "USD",
            "billing_interval": "monthly",
            "features": [
                "Unlimited creative assets",
                "Advanced AI content generation",
                "Priority support",
                "Advanced analytics",
                "Speed Daemon access",
                "Custom themes"
            ],
            "limits": {
                "assets": 500,
                "users": 10,
                "api_calls": 10000,
                "speed_daemon_tasks": 100
            }
        },
        {
            "plan_id": "enterprise",
            "name": "Enterprise Plan",
            "description": "Complete solution for large artisan organizations",
            "price": 99.99,
            "currency": "USD",
            "billing_interval": "monthly",
            "features": [
                "Unlimited everything",
                "Custom AI models",
                "Dedicated support",
                "White-label options",
                "Advanced integrations",
                "Custom analytics",
                "Priority Speed Daemon"
            ],
            "limits": {
                "assets": -1,  # Unlimited
                "users": -1,
                "api_calls": -1,
                "speed_daemon_tasks": -1
            }
        }
    ]
    
    for plan_data in plans_data:
        existing_plan = db.query(Plan).filter(Plan.plan_id == plan_data["plan_id"]).first()
        if not existing_plan:
            plan = Plan(**plan_data)
            db.add(plan)
            logger.info(f"Created plan: {plan_data['plan_id']}")


async def create_sample_workspace_settings(db: Session):
    """Create sample workspace settings"""
    workspace_id = "default_workspace"
    
    existing_settings = db.query(WorkspaceSettings).filter(
        WorkspaceSettings.workspace_id == workspace_id
    ).first()
    
    if not existing_settings:
        settings = WorkspaceSettings(
            workspace_id=workspace_id,
            theme_mode="auto",
            accent_color="#6366f1",
            primary_color="#6366f1",
            secondary_color="#8b5cf6",
            font_family="Inter",
            font_size="medium",
            border_radius="medium"
        )
        db.add(settings)
        logger.info(f"Created workspace settings for: {workspace_id}")


async def create_sample_radar_data(db: Session):
    """Create sample radar intelligence data"""
    tenant_id = "default_tenant"
    
    # Sample competitor analysis
    competitors_data = [
        {
            "competitor_name": "ArtisanCraft Pro",
            "competitor_domain": "artisancraftpro.com",
            "market_position": "leader",
            "strengths": ["Strong brand recognition", "Wide product range", "Good distribution"],
            "weaknesses": ["Higher pricing", "Slow innovation", "Limited customization"],
            "market_share_estimate": 25.5,
            "traffic_estimate": 150000,
            "sentiment_score": 0.65
        },
        {
            "competitor_name": "CraftHub",
            "competitor_domain": "crafthub.io",
            "market_position": "challenger",
            "strengths": ["Modern design", "Good pricing", "Fast delivery"],
            "weaknesses": ["Limited product range", "Newer brand", "Smaller market presence"],
            "market_share_estimate": 12.3,
            "traffic_estimate": 75000,
            "sentiment_score": 0.78
        }
    ]
    
    for comp_data in competitors_data:
        existing_comp = db.query(CompetitorAnalysis).filter(
            and_(
                CompetitorAnalysis.tenant_id == tenant_id,
                CompetitorAnalysis.competitor_name == comp_data["competitor_name"]
            )
        ).first()
        
        if not existing_comp:
            comp = CompetitorAnalysis(tenant_id=tenant_id, **comp_data)
            db.add(comp)
            logger.info(f"Created competitor analysis: {comp_data['competitor_name']}")
    
    # Sample market intelligence
    market_data = [
        {
            "market_segment": "Handmade Jewelry",
            "geographic_focus": "North America",
            "growth_rate": 15.2,
            "market_size_estimate": 2500000,
            "trend_indicators": {
                "sustainability_trend": 0.85,
                "personalization_demand": 0.92,
                "online_sales_growth": 0.78
            },
            "key_insights": [
                "Growing demand for sustainable materials",
                "Personalization is becoming standard expectation",
                "Online sales channels are primary growth driver"
            ],
            "emerging_opportunities": [
                "Eco-friendly packaging solutions",
                "Custom design platforms",
                "Virtual try-on technology"
            ],
            "risk_factors": [
                "Supply chain disruptions",
                "Increasing competition from mass market",
                "Raw material price volatility"
            ],
            "confidence_level": 0.82
        },
        {
            "market_segment": "Artisan Home Decor",
            "geographic_focus": "Europe",
            "growth_rate": 8.7,
            "market_size_estimate": 1800000,
            "trend_indicators": {
                "minimalist_design": 0.76,
                "local_production": 0.89,
                "digital_integration": 0.64
            },
            "key_insights": [
                "Minimalist aesthetic gaining popularity",
                "Local production emphasis growing",
                "Smart home integration emerging"
            ],
            "emerging_opportunities": [
                "IoT-enabled artisan products",
                "Local artisan marketplaces",
                "Sustainable material innovation"
            ],
            "risk_factors": [
                "Economic uncertainty affecting luxury spending",
                "Regulatory changes for materials",
                "Trade barriers"
            ],
            "confidence_level": 0.75
        }
    ]
    
    for market_info in market_data:
        existing_market = db.query(MarketIntelligence).filter(
            and_(
                MarketIntelligence.tenant_id == tenant_id,
                MarketIntelligence.market_segment == market_info["market_segment"]
            )
        ).first()
        
        if not existing_market:
            market = MarketIntelligence(
                tenant_id=tenant_id,
                analysis_period_start=datetime.utcnow() - timedelta(days=30),
                analysis_period_end=datetime.utcnow(),
                **market_info
            )
            db.add(market)
            logger.info(f"Created market intelligence: {market_info['market_segment']}")
    
    # Sample recommended opportunities
    opportunities_data = [
        {
            "opportunity_type": "campaign",
            "title": "Sustainability Spotlight Campaign",
            "description": "Launch a marketing campaign highlighting your sustainable practices and eco-friendly materials",
            "confidence_score": 0.89,
            "estimated_impact": "high",
            "effort_level": "medium",
            "time_to_result": 21,
            "hypothesis": "Customers are willing to pay premium for sustainably produced artisan goods",
            "success_metrics": [
                "Increase in website traffic",
                "Higher conversion rates",
                "Improved brand sentiment",
                "Social media engagement"
            ],
            "supporting_signals": ["signal_1", "signal_2"]  # Would reference actual signal IDs
        },
        {
            "opportunity_type": "experiment",
            "title": "Personalization A/B Test",
            "description": "Test different levels of product personalization to find the optimal balance",
            "confidence_score": 0.76,
            "estimated_impact": "medium",
            "effort_level": "low",
            "time_to_result": 14,
            "hypothesis": "Offering 3-5 personalization options maximizes conversion without overwhelming customers",
            "success_metrics": [
                "Conversion rate by personalization level",
                "Customer satisfaction scores",
                "Average order value",
                "Return on ad spend"
            ],
            "supporting_signals": ["signal_3", "signal_4"]
        },
        {
            "opportunity_type": "content",
            "title": "Artisan Story Video Series",
            "description": "Create a video series showcasing the stories behind your artisans and their craft",
            "confidence_score": 0.82,
            "estimated_impact": "high",
            "effort_level": "high",
            "time_to_result": 45,
            "hypothesis": "Storytelling content builds emotional connection and increases customer loyalty",
            "success_metrics": [
                "Video engagement metrics",
                "Brand awareness surveys",
                "Customer lifetime value",
                "Social sharing rates"
            ],
            "supporting_signals": ["signal_5", "signal_6"]
        }
    ]
    
    for opp_data in opportunities_data:
        existing_opp = db.query(RecommendedOpportunity).filter(
            and_(
                RecommendedOpportunity.tenant_id == tenant_id,
                RecommendedOpportunity.title == opp_data["title"]
            )
        ).first()
        
        if not existing_opp:
            opportunity = RecommendedOpportunity(
                tenant_id=tenant_id,
                expires_at=datetime.utcnow() + timedelta(days=90),
                **opp_data
            )
            db.add(opportunity)
            logger.info(f"Created recommended opportunity: {opp_data['title']}")


if __name__ == "__main__":
    asyncio.run(initialize_database())
