"""
Abstract base class for all agents
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from backend.core.cloud_llm_client import CloudLLMClient
from backend.core.vector_store import ArtisanVectorStore
from loguru import logger
from backend.agents.framework.tools import global_tool_registry


class BaseAgent(ABC):
    """
    Abstract base class for all agents
    All agents must implement: analyze() method
    """

    def __init__(
        self,
        name: str,
        description: str,
        llm_client: Optional[Union[CloudLLMClient, Any]] = None,  # Can be CloudLLMClient or LLMManager
        vector_store: Optional[ArtisanVectorStore] = None,
        cloud_llm_client: Optional[Union[CloudLLMClient, Any]] = None,
    ):
        resolved_llm = llm_client or cloud_llm_client

        if llm_client is not None and cloud_llm_client is not None and llm_client is not cloud_llm_client:
            logger.warning(
                f"Both 'llm_client' and 'cloud_llm_client' provided to {name}. Defaulting to 'llm_client'."
            )

        if resolved_llm is None:
            raise ValueError("BaseAgent requires either 'llm_client' or 'cloud_llm_client'")

        if vector_store is None:
            raise ValueError("BaseAgent requires a valid 'vector_store' instance")

        self.name = name
        self.description = description
        self.cloud_llm = resolved_llm
        self.llm = resolved_llm  # Use generic name 'llm' instead of 'ollama'
        self.ollama = resolved_llm  # Keep backward compatibility
        self.vector_store = vector_store
        self.execution_logs: List[Dict] = []
        # Shared tool registry for the whole agent team
        self.tools = global_tool_registry()

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
        """
        Format a human-readable progress message with detailed thinking
        Similar to ChatGPT/Gemini's thinking display
        """
        if step == "start":
            supplies = data.get("supplies_needed", [])
            if supplies:
                supply_list = ', '.join(supplies[:3])
                if len(supplies) > 3:
                    supply_list += f" and {len(supplies) - 3} more"
                return f"💭 Starting intelligent search for: {supply_list}. I'll search India first, then expand if needed..."
            return "💭 Analyzing your requirements and planning my search strategy..."

        elif step == "thinking":
            return f"💭 {data.get('message', 'Thinking...')}"

        elif step == "searching_supply":
            supply = data.get('supply', 'supplies')
            return f"🔍 Now searching for: **{supply}**. Let me find the best suppliers for you..."

        elif step == "web_search":
            query = data.get('query', 'searching')
            region = data.get('region', 'India')
            return f"🌐 Searching: \"{query}\" in {region}. Analyzing search results..."

        elif step == "search_results":
            count = data.get('results_count', 0)
            return f"📊 Found {count} potential suppliers. Now analyzing each one in detail..."

        elif step == "scraping_page":
            url = data.get('url', 'unknown')
            domain = url.split('/')[2] if '/' in url else url
            return f"📄 Extracting detailed information from {domain}..."

        elif step == "extracting_data":
            return f"🤖 Using AI to extract structured supplier information from webpage..."

        elif step == "verifying_supplier":
            name = data.get('name', 'supplier')
            return f"✓ Verifying **{name}**. Checking legitimacy, reviews, and contact information..."

        elif step == "expanding_search":
            reason = data.get('reason', 'insufficient results')
            return f"🔎 Expanding search to broader regions - {reason}. I want to find you the best options..."

        elif step == "verification_complete":
            conf = data.get('confidence', 0)
            name = data.get('name', 'Supplier')
            if conf > 0.8:
                status = "High confidence ✅"
            elif conf > 0.6:
                status = "Good confidence ✓"
            else:
                status = "Low confidence ⚠️"
            return f"✓ {name}: {status} ({conf:.0%})"

        elif step == "cross_referencing":
            return f"🔄 Cross-referencing suppliers to remove duplicates and verify consistency..."

        elif step == "analyzing_pricing":
            return f"💰 Analyzing pricing information and budget compatibility..."

        elif step == "complete":
            total = data.get('total_found', 0)
            india = data.get('india_suppliers', 0)
            if total > 0:
                return f"✅ Search complete! Found {total} verified suppliers ({india} in India). Results ready!"
            else:
                return f"⚠️ Search complete but no suppliers found. Consider broadening your search criteria."

        elif step == "error":
            error = data.get('error', 'Unknown error')
            return f"❌ Error: {error}. Trying alternative approach..."

        else:
            # Generic fallback with emoji
            return f"⚙️ {step.replace('_', ' ').title()}: {str(data)[:100]}"
    
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
