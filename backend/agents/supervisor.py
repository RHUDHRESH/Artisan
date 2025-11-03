"""
Supervisor Agent - Plans and orchestrates specialized worker agents
"""
from typing import Dict, Any, List, Optional, Callable
from loguru import logger

from backend.agents.base_agent import BaseAgent
from backend.agents.profile_analyst import ProfileAnalystAgent
from backend.agents.supply_hunter import SupplyHunterAgent
from backend.agents.growth_marketer import GrowthMarketerAgent
from backend.agents.event_scout import EventScoutAgent
from backend.agents.framework.tools import default_tool_registry
from backend.agents.framework.planner import Planner
from backend.agents.framework.executor import Executor
from backend.agents.framework.guardrails import Guardrails

from backend.core.ollama_client import OllamaClient
from backend.core.vector_store import ArtisanVectorStore
from backend.scraping.web_scraper import WebScraperService
from backend.services.maps_service import MapsService


class SupervisorAgent(BaseAgent):
    """
    Orchestrates a mission by:
    1) Planning steps
    2) Dispatching tasks to worker agents
    3) Enforcing constraints (max steps, region priority)
    4) Aggregating results
    """

    def __init__(
        self,
        ollama_client: OllamaClient,
        vector_store: ArtisanVectorStore,
        scraper_service: Optional[WebScraperService] = None,
        maps_service: Optional[MapsService] = None,
    ):
        super().__init__(
            name="Supervisor",
            description="Plans and coordinates specialized agents to achieve a goal",
            ollama_client=ollama_client,
            vector_store=vector_store,
        )
        self.scraper = scraper_service or WebScraperService()
        self.maps = maps_service or MapsService()
        self.tools = default_tool_registry()
        self.planner = Planner(self.ollama)
        self.guardrails = Guardrails()

        # Worker agent factories (lazy to avoid heavy setup when not used)
        self._workers: Dict[str, Callable[[], BaseAgent]] = {
            "profile_analyst": lambda: ProfileAnalystAgent(self.ollama, self.vector_store),
            "supply_hunter": lambda: SupplyHunterAgent(self.ollama, self.vector_store, self.scraper),
            "growth_marketer": lambda: GrowthMarketerAgent(self.ollama, self.vector_store, self.scraper),
            "event_scout": lambda: EventScoutAgent(self.ollama, self.vector_store, self.scraper, self.maps),
        }

    async def analyze(self, user_profile: Dict) -> Dict:
        """
        This method supports a generic "mission" with constraints.

        Expected user_profile keys:
        - goal: high-level mission goal string
        - context: optional dict with craft_type/location/etc.
        - constraints: { max_steps: int, region_priority: str, step_timeout_s: int }
        - capabilities: list of worker keys to allow (subset of self._workers.keys())
        """
        goal: str = user_profile.get("goal", "").strip()
        context: Dict[str, Any] = user_profile.get("context", {})
        constraints: Dict[str, Any] = user_profile.get("constraints", {})
        allowed_caps: Optional[List[str]] = user_profile.get("capabilities")

        if not goal:
            return {"error": "Missing 'goal' in request"}

        max_steps: int = int(constraints.get("max_steps", 6))
        region_priority: str = str(constraints.get("region_priority", "in-first"))

        # 1) Plan steps using Planner (compact and bounded)
        self.log_execution("planning_start", {"goal": goal, "max_steps": max_steps})
        try:
            steps = await self.planner.create_plan(goal, context, max_steps, list(self._workers.keys()))
        except Exception as parse_err:
            logger.warning(f"Planner failed, falling back to minimal plan: {parse_err}")
            steps = self._fallback_minimal_plan(goal, context)

        # Filter to allowed capabilities if provided
        if allowed_caps:
            steps = [s for s in steps if s.get("worker") in allowed_caps]

        # Enforce max steps hard cap
        steps = steps[:max_steps]

        self.log_execution("planning_complete", {"num_steps": len(steps)})

        # 2) Execute plan sequentially with guardrails and tool calls
        artifacts: List[Dict[str, Any]] = []
        executor = Executor(self.tools.get, timeout_s=int(constraints.get("step_timeout_s", 60)), max_retries=int(constraints.get("retries", 1)))
        for idx, step in enumerate(steps, start=1):
            worker_key = step.get("worker")
            inputs = step.get("inputs", {})

            if worker_key not in self._workers:
                self.log_execution("skip_step", {"step": idx, "reason": "unknown_worker", "worker": worker_key})
                continue

            if allowed_caps and worker_key not in allowed_caps:
                self.log_execution("skip_step", {"step": idx, "reason": "capability_not_allowed", "worker": worker_key})
                continue

            worker = self._workers[worker_key]()

            # Merge mission context into worker inputs (worker can ignore extras) and run through executor
            worker_input = {**context, **inputs}
            worker_input_str = self.guardrails.redact_pii(str(worker_input))
            self.log_execution("step_start", {"step": idx, "worker": worker_key, "inputs": worker_input_str})

            try:
                result = await executor.execute_step(step, lambda inp: worker.analyze(inp))
            except Exception as run_err:
                self.log_execution("step_error", {"step": idx, "worker": worker_key, "error": str(run_err)})
                continue

            artifacts.append({
                "step": idx,
                "worker": worker_key,
                "result": result,
            })
            self.log_execution("step_complete", {"step": idx, "worker": worker_key})

        # 3) Summarize outcomes
        summary_prompt = (
            "Given the mission goal and the artifacts from each step, produce a concise outcome summary "
            "with next-best actions and any blockers. Return JSON with keys: summary, recommended_next_steps[]."
        )
        summary_text = await self.ollama.fast_task(
            summary_prompt + "\nGOAL: " + goal + "\nARTIFACTS: " + str(artifacts)[:4000]
        )

        return {
            "goal": goal,
            "constraints": {"max_steps": max_steps, "region_priority": region_priority},
            "plan": steps,
            "artifacts": artifacts,
            "summary": summary_text,
        }

    def _safe_parse_json_array(self, text: str) -> List[Dict[str, Any]]:
        import json
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict) and "steps" in parsed and isinstance(parsed["steps"], list):
            return parsed["steps"]
        raise ValueError("Unexpected plan JSON shape")

    def _fallback_minimal_plan(self, goal: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        # Heuristic minimal plan: profile -> supply -> growth
        craft_type = context.get("craft_type")
        steps: List[Dict[str, Any]] = []
        if not craft_type:
            steps.append({
                "step_name": "Profile inference",
                "worker": "profile_analyst",
                "inputs": {"input_text": context.get("input_text", goal)},
                "success_criteria": "Extract craft_type and location",
            })
        steps.append({
            "step_name": "Find suppliers",
            "worker": "supply_hunter",
            "inputs": {
                "craft_type": context.get("craft_type", ""),
                "supplies_needed": context.get("supplies_needed", []),
                "location": context.get("location", {}),
            },
            "success_criteria": "Return verified suppliers",
        })
        steps.append({
            "step_name": "Growth opportunities",
            "worker": "growth_marketer",
            "inputs": {
                "craft_type": context.get("craft_type", ""),
                "specialization": context.get("specialization", ""),
                "current_products": context.get("current_products", []),
                "location": context.get("location", {}),
            },
            "success_criteria": "List top 3 actions",
        })
        return steps


