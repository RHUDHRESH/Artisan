"""
Context API for reading/updating user context persisted in LocalStore
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from loguru import logger

from backend.services.local_store import LocalStore


router = APIRouter(prefix="/context", tags=["context"])
store = LocalStore()


class ContextUpdate(BaseModel):
    user_id: Optional[str] = Field(default=None, description="User identifier")
    context: Dict[str, Any] = Field(default_factory=dict)


@router.get("")
async def get_context(user_id: Optional[str] = Query(None)):
    try:
        ctx = store.get_user_context(user_id or "anonymous")
        return {"user_id": user_id or "anonymous", "context": ctx}
    except Exception as e:
        logger.error(f"Get context error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("")
async def update_context(payload: ContextUpdate):
    try:
        user = payload.user_id or "anonymous"
        store.update_user_context(user, payload.context)
        return {"status": "ok", "user_id": user}
    except Exception as e:
        logger.error(f"Update context error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

