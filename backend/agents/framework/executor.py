from __future__ import annotations
"""
Executor: Runs planned steps, executing tool calls with timeouts/retries and delegating to workers.
"""
from typing import Dict, Any, List, Callable
import asyncio
from loguru import logger


class Executor:
    def __init__(self, tool_getter: Callable[[str], Any], timeout_s: int = 60, max_retries: int = 1):
        self._get_tool = tool_getter
        self._timeout_s = timeout_s
        self._max_retries = max_retries

    async def _run_with_retries(self, coro_factory, label: str):
        last_err = None
        for attempt in range(self._max_retries + 1):
            try:
                return await asyncio.wait_for(coro_factory(), timeout=self._timeout_s)
            except Exception as e:
                last_err = e
                logger.warning(f"{label} failed (attempt {attempt+1}): {e}")
        raise last_err

    async def execute_step(self, step: Dict[str, Any], worker_call: Callable[[Dict[str, Any]], Any]) -> Dict[str, Any]:
        # 1) Execute tool calls (if any)
        tool_artifacts: List[Dict[str, Any]] = []
        for call in step.get("tool_calls", []) or []:
            tool_name = call.get("tool")
            args = call.get("args", {})
            tool = self._get_tool(tool_name)
            result = await self._run_with_retries(lambda: tool.run(**args), f"tool:{tool_name}")
            tool_artifacts.append({"tool": tool_name, "args": args, "result": result})

        # 2) Call the worker with step inputs enriched by tool artifacts
        inputs = {**(step.get("inputs") or {}), "tool_artifacts": tool_artifacts}
        worker_result = await self._run_with_retries(lambda: worker_call(inputs), f"worker:{step.get('worker')}")

        return {"tool_artifacts": tool_artifacts, "worker_result": worker_result}


