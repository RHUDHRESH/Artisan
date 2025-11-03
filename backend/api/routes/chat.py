"""
Chat API endpoints
"""
from fastapi import APIRouter, HTTPException
from backend.models import ChatRequest, ChatResponse, ChatMessage
from backend.core.ollama_client import OllamaClient
from loguru import logger
import time

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/send", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """
    Send a message to the AI assistant
    """
    start_time = time.time()
    
    try:
        # Build conversation context
        context = ""
        for msg in request.conversation_history[-5:]:  # Last 5 messages
            context += f"{msg.role}: {msg.content}\n"
        
        context += f"user: {request.message}\n"
        
        # Use fast model for simple queries, reasoning model for complex ones
        async with OllamaClient() as client:
            # Simple classification to route to correct model
            classification_prompt = f"Classify this query as 'simple' or 'complex': {request.message}"
            classification = await client.fast_task(classification_prompt)
            
            is_complex = "complex" in classification.lower()
            
            # Generate response
            system_prompt = """You are a helpful AI assistant for artisans and craftspeople.
Your role is to understand their craft, help them find suppliers, identify growth opportunities,
and connect them with relevant events. Be concise, helpful, and empathetic."""
            
            if is_complex:
                response = await client.reasoning_task(
                    prompt=context,
                    system=system_prompt
                )
                model_used = "gemma3:4b"
            else:
                response = await client.fast_task(
                    prompt=context,
                    system=system_prompt
                )
                model_used = "gemma3:1b"
        
        processing_time = time.time() - start_time
        
        logger.info(f"Chat response generated in {processing_time:.2f}s using {model_used}")
        
        return ChatResponse(
            response=response,
            model_used=model_used,
            processing_time=processing_time
        )
    
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

