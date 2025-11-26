"""
Context API for reading/updating user context persisted in LocalStore
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from loguru import logger

from backend.services.local_store import LocalStore
from backend.config import settings
from backend.core.supabase_client import get_supabase_client


router = APIRouter(prefix="/context", tags=["context"])
store = LocalStore()
supabase_client = (
    get_supabase_client(settings.supabase_url, settings.supabase_key)
    if settings.supabase_url and settings.supabase_key
    else None
)


class ContextUpdate(BaseModel):
    user_id: Optional[str] = Field(default=None, description="User identifier")
    context: Dict[str, Any] = Field(default_factory=dict)


@router.get("")
async def get_context(user_id: Optional[str] = Query(None)):
    try:
        user = user_id or "anonymous"
        ctx = None
        if supabase_client and getattr(supabase_client, "enabled", False):
            try:
                record = await supabase_client.get_user_profile(user)
                if record:
                    ctx = record.get("context") or record
            except Exception as exc:
                logger.debug(f"Supabase context lookup failed: {exc}")
        if ctx is None:
            ctx = store.get_user_context(user)
        return {"user_id": user_id or "anonymous", "context": ctx}
    except Exception as e:
        logger.error(f"Get context error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("")
async def update_context(payload: ContextUpdate):
    try:
        user = payload.user_id or "anonymous"
        store.update_user_context(user, payload.context)
        if supabase_client and getattr(supabase_client, "enabled", False):
            try:
                await supabase_client.save_user_profile(user, {"context": payload.context})
            except Exception as exc:
                logger.debug(f"Supabase context update failed: {exc}")
        return {"status": "ok", "user_id": user}
    except Exception as e:
        logger.error(f"Update context error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
