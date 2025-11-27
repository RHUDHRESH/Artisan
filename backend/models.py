"""
Pydantic models for API requests and responses
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class HealthResponse(BaseModel):
    status: str
    message: str
    llm_connected: Optional[bool]
    providers: Optional[Dict[str, bool]] = None


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[ChatMessage]] = []
    user_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    model_used: str
    processing_time: float

