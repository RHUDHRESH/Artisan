from __future__ import annotations
"""
Planner: Uses LLM to convert a goal/context into a bounded plan of steps.
"""
from typing import List, Dict, Any


class Planner:
    def __init__(self, llm):
        self._llm = llm

    async def create_plan(self, goal: str, context: Dict[str, Any], max_steps: int, allowed_workers: List[str]) -> List[Dict[str, Any]]:
        prompt = (
            "You are a strict mission planner. Create a JSON array of steps (3-" + str(max_steps) + ") where each step has: "
            "step_name, worker (one of " + ",".join(allowed_workers) + "), tool_calls (array of {tool, args}), "
            "inputs (JSON), and success_criteria. Return ONLY JSON array."
        )
        text = await self._llm.reasoning_task(prompt + f"\nGOAL: {goal}\nCONTEXT: {context}")
        import json
        try:
            data = json.loads(text)
            if isinstance(data, list):
                return data[:max_steps]
        except Exception:
            pass
        # Fallback minimal plan
        return [
            {"step_name": "Analyze profile", "worker": "profile_analyst", "tool_calls": [], "inputs": {"input_text": context.get("input_text", goal)}, "success_criteria": "profile extracted"},
            {"step_name": "Find suppliers", "worker": "supply_hunter", "tool_calls": [], "inputs": {"craft_type": context.get("craft_type", ""), "supplies_needed": context.get("supplies_needed", []), "location": context.get("location", {})}, "success_criteria": "verified suppliers"}
        ][:max_steps]


