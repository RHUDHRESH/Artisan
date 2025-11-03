from __future__ import annotations
"""
Router: Picks models/agents/tools based on task complexity and constraints.
"""
from typing import Dict, Any


class Router:
    def choose_model(self, task: Dict[str, Any]) -> str:
        text = (task.get("inputs") or {}).get("input_text") or ""
        if len(text) > 400:
            return "reasoning"
        return "fast"


