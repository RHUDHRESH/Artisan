"""
Abstract base class for all agents
"""
from abc import ABC, abstractmethod
from typing import Dict, List
from backend.core.ollama_client import OllamaClient
from backend.core.vector_store import ArtisanVectorStore
from loguru import logger


class BaseAgent(ABC):
    """
    Abstract base class for all agents
    All agents must implement: analyze() method
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        ollama_client: OllamaClient,
        vector_store: ArtisanVectorStore
    ):
        self.name = name
        self.description = description
        self.ollama = ollama_client
        self.vector_store = vector_store
        self.execution_logs: List[Dict] = []
        
        logger.info(f"Initialized {self.name} agent")
    
    @abstractmethod
    async def analyze(self, user_profile: Dict) -> Dict:
        """
        Main analysis method - must be implemented by each agent
        
        Args:
            user_profile: User profile dictionary containing:
                - craft_type: Type of craft
                - location: User location
                - story: User's story
                - context: Additional context
        
        Returns:
            Dictionary containing agent's analysis and recommendations
        """
        pass
    
    def log_execution(self, step: str, data: Dict):
        """Log execution step for audit trail and broadcast via WebSocket"""
        log_entry = {
            "agent": self.name,
            "step": step,
            "data": data,
            "timestamp": self._get_timestamp()
        }
        self.execution_logs.append(log_entry)
        logger.debug(f"[{self.name}] {step}: {data}")
        
        # Broadcast via WebSocket for real-time updates
        try:
            from backend.api.websocket import manager
            import json
            import asyncio
            message = {
                "type": "agent_progress",
                "agent": self.name,
                "step": step,
                "data": data,
                "timestamp": log_entry["timestamp"],
                "message": self._format_progress_message(step, data)
            }
            # Try to broadcast - handle both sync and async contexts
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Already in async context, schedule task
                    asyncio.create_task(manager.broadcast(message))
                else:
                    # No running loop, run it
                    loop.run_until_complete(manager.broadcast(message))
            except RuntimeError:
                # No event loop at all, skip broadcast (shouldn't happen in async context)
                logger.debug(f"Skipping WebSocket broadcast - no event loop available")
        except Exception as e:
            logger.debug(f"Could not broadcast progress: {e}")
    
    def _format_progress_message(self, step: str, data: Dict) -> str:
        """Format a human-readable progress message"""
        if step == "start":
            supplies = data.get("supplies_needed", [])
            if supplies:
                return f"Starting search for: {', '.join(supplies[:3])}{'...' if len(supplies) > 3 else ''}"
            return "Starting analysis..."
        elif step == "searching_supply":
            return f"🔍 Searching for suppliers of: {data.get('supply', 'supplies')}"
        elif step == "web_search":
            return f"🌐 Web search: {data.get('query', 'searching')}"
        elif step == "scraping_page":
            return f"📄 Scraping page: {data.get('url', 'unknown')}"
        elif step == "verifying_supplier":
            return f"✓ Verifying supplier: {data.get('name', 'unknown')}"
        elif step == "expanding_search":
            return f"🔎 Expanding search (insufficient results found)"
        elif step == "verification_complete":
            conf = data.get('confidence', 0)
            return f"✓ Verification complete (confidence: {conf:.0%})"
        elif step == "complete":
            total = data.get('total_found', 0)
            return f"✅ Complete! Found {total} suppliers"
        else:
            return f"{step}: {str(data)[:100]}"
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_logs(self) -> List[Dict]:
        """Get execution logs"""
        return self.execution_logs
    
    def clear_logs(self):
        """Clear execution logs"""
        self.execution_logs = []
