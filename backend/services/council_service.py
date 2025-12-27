"""
Council Service - Encapsulates council deliberation pipeline
"""
from typing import Dict, List, Optional, Any
import hashlib
import json
from datetime import datetime, timedelta
from loguru import logger

from backend.graphs.council_blackboard import CouncilBlackboard
from backend.graphs.council import CouncilGraph


class CouncilService:
    """
    Service for running council deliberations
    Can be reused by API endpoints and cron jobs
    """
    
    def __init__(self, llm_client: Any, redis_client: Optional[Any] = None):
        self.llm = llm_client
        self.redis = redis_client
        self.council_graph = CouncilGraph(llm_client)
        
    async def generate_move_plan(
        self,
        workspace_id: str,
        objective: str,
        details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate a move plan using council deliberation
        """
        try:
            # Check cache first
            cache_key = self._get_cache_key("move_plan", workspace_id, objective, details)
            if self.redis:
                cached_result = await self.redis.get(cache_key)
                if cached_result:
                    logger.info(f"Returning cached move plan for workspace {workspace_id}")
                    return json.loads(cached_result)
            
            # Create blackboard
            blackboard = CouncilBlackboard(workspace_id, objective, details)
            
            # Run council deliberation
            result_blackboard = await self.council_graph.run_council(blackboard, include_campaign_arc=False)
            
            # Format response
            response = self._format_move_plan_response(result_blackboard)
            
            # Cache result
            if self.redis:
                await self.redis.setex(
                    cache_key,
                    timedelta(hours=24),
                    json.dumps(response)
                )
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating move plan: {e}")
            return {
                "success": False,
                "error": str(e),
                "workspace_id": workspace_id,
                "objective": objective
            }
    
    async def generate_campaign_plan(
        self,
        workspace_id: str,
        objective: str,
        target_icp: str,
        details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate a campaign plan using council deliberation
        """
        try:
            # Check cache first
            cache_key = self._get_cache_key("campaign_plan", workspace_id, objective, details, target_icp)
            if self.redis:
                cached_result = await self.redis.get(cache_key)
                if cached_result:
                    logger.info(f"Returning cached campaign plan for workspace {workspace_id}")
                    return json.loads(cached_result)
            
            # Create blackboard with target ICP
            blackboard = CouncilBlackboard(workspace_id, objective, details, target_icp)
            
            # Run council deliberation with campaign arc
            result_blackboard = await self.council_graph.run_council(blackboard, include_campaign_arc=True)
            
            # Format response
            response = self._format_campaign_plan_response(result_blackboard)
            
            # Cache result
            if self.redis:
                await self.redis.setex(
                    cache_key,
                    timedelta(hours=24),
                    json.dumps(response)
                )
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating campaign plan: {e}")
            return {
                "success": False,
                "error": str(e),
                "workspace_id": workspace_id,
                "objective": objective,
                "target_icp": target_icp
            }
    
    def _format_move_plan_response(self, blackboard: CouncilBlackboard) -> Dict[str, Any]:
        """Format move plan response from blackboard"""
        state = blackboard.state
        
        return {
            "success": True,
            "workspace_id": state["workspace_id"],
            "objective": state["objective"],
            "decree": state["decree"],
            "consensus_metrics": state["consensus_metrics"].dict() if state["consensus_metrics"] else None,
            "proposed_moves": [move.dict() for move in state["proposed_moves"]],
            "refined_moves": [move.dict() for move in state["refined_moves"]],
            "approved_moves": [move.dict() for move in state["approved_moves"]],
            "discarded_moves": [move.dict() for move in state["discarded_moves"]],
            "debate_history": [round.dict() for round in state["debate_history"][-3:]],  # Last 3 rounds
            "rejected_paths": [move.dict() for move in state["discarded_moves"]],
            "reasoning_chain_id": state["reasoning_chain_id"],
            "started_at": state["started_at"].isoformat(),
            "completed_at": state["completed_at"].isoformat() if state["completed_at"] else None,
            "errors": state["errors"],
            "kill_switch_triggered": state["kill_switch_triggered"]
        }
    
    def _format_campaign_plan_response(self, blackboard: CouncilBlackboard) -> Dict[str, Any]:
        """Format campaign plan response from blackboard"""
        state = blackboard.state
        
        return {
            "success": True,
            "workspace_id": state["workspace_id"],
            "objective": state["objective"],
            "target_icp": state["target_icp"],
            "campaign_data": state["campaign_arc"],
            "refined_moves": [move.dict() for move in state["refined_moves"]],
            "rationale": {
                "decree": state["decree"],
                "consensus_metrics": state["consensus_metrics"].dict() if state["consensus_metrics"] else None,
                "debate_summary": [round.dict() for round in state["debate_history"][-3:]],
                "reasoning_chain_id": state["reasoning_chain_id"]
            },
            "started_at": state["started_at"].isoformat(),
            "completed_at": state["completed_at"].isoformat() if state["completed_at"] else None,
            "errors": state["errors"],
            "kill_switch_triggered": state["kill_switch_triggered"]
        }
    
    def _get_cache_key(self, plan_type: str, workspace_id: str, objective: str, details: Dict[str, Any], target_icp: Optional[str] = None) -> str:
        """Generate cache key for council plans"""
        # Create hash of inputs for cache key
        cache_data = {
            "plan_type": plan_type,
            "workspace_id": workspace_id,
            "objective": objective,
            "details": details,
            "target_icp": target_icp
        }
        
        cache_string = json.dumps(cache_data, sort_keys=True)
        hash_key = hashlib.sha256(cache_string.encode()).hexdigest()[:16]
        
        return f"council:{plan_type}:{workspace_id}:{hash_key}"
    
    async def clear_cache(self, workspace_id: str) -> int:
        """Clear all cached plans for a workspace"""
        if not self.redis:
            return 0
        
        try:
            pattern = f"council:*:{workspace_id}:*"
            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)
                logger.info(f"Cleared {len(keys)} cached plans for workspace {workspace_id}")
                return len(keys)
            return 0
            
        except Exception as e:
            logger.error(f"Error clearing cache for workspace {workspace_id}: {e}")
            return 0
    
    async def get_plan_status(self, workspace_id: str, plan_id: str) -> Dict[str, Any]:
        """Get status of a plan generation"""
        # This would integrate with a job queue system in production
        # For now, return a simple status
        return {
            "workspace_id": workspace_id,
            "plan_id": plan_id,
            "status": "completed",
            "progress": 100,
            "estimated_completion": datetime.now().isoformat()
        }


# Global service instance
_council_service: Optional[CouncilService] = None


def get_council_service(llm_client: Any, redis_client: Optional[Any] = None) -> CouncilService:
    """Get or create council service instance"""
    global _council_service
    if _council_service is None:
        _council_service = CouncilService(llm_client, redis_client)
    return _council_service
