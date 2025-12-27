"""
Muse Assets API Routes - Creative Asset Management
"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from typing import List, Optional
from datetime import datetime

from backend.models.muse_api import (
    AssetCreateRequest, AssetUpdateRequest, AssetResponse, AssetListResponse,
    ThemeSettingsUpdate, ThemeSettingsResponse, SuccessResponse
)
from backend.models.muse import MuseAsset, WorkspaceSettings
from backend.core.database import get_db
from backend.core.caching import cache_manager
from loguru import logger

router = APIRouter(prefix="/v1/muse", tags=["muse"])

# Dependency to get tenant_id and workspace_id
async def get_current_context() -> tuple:
    """Get current tenant and workspace IDs - in production from JWT/auth"""
    return "default_tenant", "default_workspace"


# Assets CRUD Endpoints
@router.post("/assets", response_model=AssetResponse)
async def create_asset(
    request: AssetCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    context: tuple = Depends(get_current_context)
):
    """
    Create a new Muse asset
    """
    try:
        tenant_id, workspace_id = context
        
        # Validate asset type
        valid_types = ["email", "tagline", "social-post", "ad-copy", "blog-post", 
                      "product-desc", "landing-page", "video-script", "press-release"]
        if request.type.value not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid asset type. Must be one of: {valid_types}"
            )
        
        # Handle speed daemon generation if requested
        content = request.content
        generated_by = "human"
        generation_time_ms = None
        
        if request.use_speed_daemon and not content:
            # Queue for speed daemon generation
            background_tasks.add_task(
                generate_content_with_speed_daemon,
                tenant_id,
                workspace_id,
                request.type.value,
                request.prompt or request.title
            )
            content = {"message": "Content generation queued with Speed Daemon"}
            generated_by = "speed_daemon"
        elif not content:
            # Generate basic content structure
            content = generate_basic_content(request.type.value, request.prompt or request.title)
            generated_by = "ai"
        
        # Create asset
        asset = MuseAsset(
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            asset_type=request.type.value,
            title=request.title,
            content=content,
            prompt=request.prompt,
            folder=request.folder,
            tags=request.tags or [],
            generated_by=generated_by,
            generation_time_ms=generation_time_ms
        )
        
        db.add(asset)
        db.commit()
        db.refresh(asset)
        
        logger.info(f"Created asset {asset.id} of type {request.type.value}")
        return asset
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Asset creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assets", response_model=AssetListResponse)
async def list_assets(
    type: Optional[str] = Query(None, description="Filter by asset type"),
    folder: Optional[str] = Query(None, description="Filter by folder"),
    status: Optional[str] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search in title and content"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    context: tuple = Depends(get_current_context)
):
    """
    List assets with filtering and pagination
    """
    try:
        tenant_id, workspace_id = context
        
        # Build query
        query = db.query(MuseAsset).filter(
            and_(
                MuseAsset.tenant_id == tenant_id,
                MuseAsset.workspace_id == workspace_id,
                MuseAsset.status != "deleted"
            )
        )
        
        # Apply filters
        if type:
            query = query.filter(MuseAsset.asset_type == type)
        if folder:
            query = query.filter(MuseAsset.folder == folder)
        if status:
            query = query.filter(MuseAsset.status == status)
        if search:
            query = query.filter(
                or_(
                    MuseAsset.title.contains(search),
                    MuseAsset.prompt.contains(search)
                )
            )
        
        # Count total
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * per_page
        assets = query.order_by(desc(MuseAsset.updated_at)).offset(offset).limit(per_page).all()
        
        return AssetListResponse(
            assets=assets,
            total=total,
            page=page,
            per_page=per_page,
            has_next=offset + per_page < total,
            has_prev=page > 1
        )
        
    except Exception as e:
        logger.error(f"Asset listing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assets/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: str,
    db: Session = Depends(get_db),
    context: tuple = Depends(get_current_context)
):
    """
    Get a specific asset
    """
    try:
        tenant_id, workspace_id = context
        
        asset = db.query(MuseAsset).filter(
            and_(
                MuseAsset.id == asset_id,
                MuseAsset.tenant_id == tenant_id,
                MuseAsset.workspace_id == workspace_id,
                MuseAsset.status != "deleted"
            )
        ).first()
        
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        # Increment view count
        asset.views += 1
        db.commit()
        
        return asset
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Asset retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/assets/{asset_id}", response_model=AssetResponse)
async def update_asset(
    asset_id: str,
    request: AssetUpdateRequest,
    db: Session = Depends(get_db),
    context: tuple = Depends(get_current_context)
):
    """
    Update an asset with optimistic locking
    """
    try:
        tenant_id, workspace_id = context
        
        asset = db.query(MuseAsset).filter(
            and_(
                MuseAsset.id == asset_id,
                MuseAsset.tenant_id == tenant_id,
                MuseAsset.workspace_id == workspace_id,
                MuseAsset.status != "deleted"
            )
        ).first()
        
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        # Check optimistic lock
        if asset.lock_version != request.lock_version:
            raise HTTPException(
                status_code=409,
                detail="Asset has been modified by another user. Please refresh and try again."
            )
        
        # Update fields
        if request.title is not None:
            asset.title = request.title
        if request.content is not None:
            asset.content = request.content
        if request.folder is not None:
            asset.folder = request.folder
        if request.tags is not None:
            asset.tags = request.tags
        if request.status is not None:
            asset.status = request.status.value
        
        # Increment lock version and update timestamp
        asset.lock_version += 1
        asset.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(asset)
        
        logger.info(f"Updated asset {asset_id} to version {asset.lock_version}")
        return asset
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Asset update failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/assets/{asset_id}", response_model=SuccessResponse)
async def delete_asset(
    asset_id: str,
    db: Session = Depends(get_db),
    context: tuple = Depends(get_current_context)
):
    """
    Soft delete an asset
    """
    try:
        tenant_id, workspace_id = context
        
        asset = db.query(MuseAsset).filter(
            and_(
                MuseAsset.id == asset_id,
                MuseAsset.tenant_id == tenant_id,
                MuseAsset.workspace_id == workspace_id,
                MuseAsset.status != "deleted"
            )
        ).first()
        
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        # Soft delete
        asset.status = "deleted"
        asset.deleted_at = datetime.utcnow()
        asset.updated_at = datetime.utcnow()
        
        db.commit()
        
        logger.info(f"Soft deleted asset {asset_id}")
        return SuccessResponse(message="Asset deleted successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Asset deletion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/assets/{asset_id}/duplicate", response_model=AssetResponse)
async def duplicate_asset(
    asset_id: str,
    db: Session = Depends(get_db),
    context: tuple = Depends(get_current_context)
):
    """
    Duplicate an asset with "(Copy)" appended to title
    """
    try:
        tenant_id, workspace_id = context
        
        original = db.query(MuseAsset).filter(
            and_(
                MuseAsset.id == asset_id,
                MuseAsset.tenant_id == tenant_id,
                MuseAsset.workspace_id == workspace_id,
                MuseAsset.status != "deleted"
            )
        ).first()
        
        if not original:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        # Create duplicate
        duplicate = MuseAsset(
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            asset_type=original.asset_type,
            title=f"{original.title} (Copy)",
            content=original.content.copy() if original.content else None,
            prompt=original.prompt,
            folder=original.folder,
            tags=original.tags.copy() if original.tags else [],
            generated_by="human",  # Duplicates are human-created
            status="draft"
        )
        
        db.add(duplicate)
        db.commit()
        db.refresh(duplicate)
        
        logger.info(f"Duplicated asset {asset_id} to {duplicate.id}")
        return duplicate
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Asset duplication failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Theme Settings Endpoints
@router.get("/settings/theme", response_model=ThemeSettingsResponse)
async def get_theme_settings(
    db: Session = Depends(get_db),
    context: tuple = Depends(get_current_context)
):
    """
    Get workspace theme settings
    """
    try:
        tenant_id, workspace_id = context
        
        settings = db.query(WorkspaceSettings).filter(
            WorkspaceSettings.workspace_id == workspace_id
        ).first()
        
        if not settings:
            # Create default settings
            settings = WorkspaceSettings(
                workspace_id=workspace_id,
                theme_mode="auto",
                accent_color="#6366f1"
            )
            db.add(settings)
            db.commit()
            db.refresh(settings)
        
        return settings
        
    except Exception as e:
        logger.error(f"Theme settings retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/settings/theme", response_model=ThemeSettingsResponse)
async def update_theme_settings(
    request: ThemeSettingsUpdate,
    db: Session = Depends(get_db),
    context: tuple = Depends(get_current_context)
):
    """
    Update workspace theme settings
    """
    try:
        tenant_id, workspace_id = context
        
        settings = db.query(WorkspaceSettings).filter(
            WorkspaceSettings.workspace_id == workspace_id
        ).first()
        
        if not settings:
            # Create settings if they don't exist
            settings = WorkspaceSettings(workspace_id=workspace_id)
            db.add(settings)
        
        # Update fields
        if request.theme_mode is not None:
            settings.theme_mode = request.theme_mode.value
        if request.accent_color is not None:
            settings.accent_color = request.accent_color
        if request.primary_color is not None:
            settings.primary_color = request.primary_color
        if request.secondary_color is not None:
            settings.secondary_color = request.secondary_color
        if request.background_color is not None:
            settings.background_color = request.background_color
        if request.text_color is not None:
            settings.text_color = request.text_color
        if request.font_family is not None:
            settings.font_family = request.font_family
        if request.font_size is not None:
            settings.font_size = request.font_size
        if request.border_radius is not None:
            settings.border_radius = request.border_radius
        
        settings.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(settings)
        
        logger.info(f"Updated theme settings for workspace {workspace_id}")
        return settings
        
    except Exception as e:
        logger.error(f"Theme settings update failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Helper functions
def generate_basic_content(asset_type: str, prompt: str) -> dict:
    """Generate basic content structure for different asset types"""
    base_content = {
        "prompt": prompt,
        "generated_at": datetime.utcnow().isoformat()
    }
    
    if asset_type == "email":
        base_content.update({
            "subject": f"Subject: {prompt}",
            "body": f"Email body content for: {prompt}",
            "cta": "Call to action text"
        })
    elif asset_type == "tagline":
        base_content.update({
            "tagline": f"Tagline for: {prompt}",
            "variations": [
                f"Option 1: {prompt}",
                f"Option 2: {prompt} - Enhanced",
                f"Option 3: {prompt} - Premium"
            ]
        })
    elif asset_type == "social-post":
        base_content.update({
            "content": f"Social media post about: {prompt}",
            "hashtags": ["#artisan", "#creative", "#handmade"],
            "media_suggestions": "Image/video suggestions"
        })
    else:
        base_content.update({
            "content": f"Content for {asset_type}: {prompt}"
        })
    
    return base_content


async def generate_content_with_speed_daemon(
    tenant_id: str,
    workspace_id: str,
    asset_type: str,
    prompt: str
):
    """Background task to generate content using Speed Daemon"""
    try:
        # This would integrate with the Speed Daemon service
        # For now, we'll simulate the process
        import asyncio
        await asyncio.sleep(2)  # Simulate processing time
        
        logger.info(f"Speed Daemon content generation completed for {asset_type}: {prompt}")
        
    except Exception as e:
        logger.error(f"Speed Daemon generation failed: {e}")
