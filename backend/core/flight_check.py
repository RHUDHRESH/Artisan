"""
Flight check utilities for verifying backend dependencies.
"""
from __future__ import annotations

import asyncio
import importlib
import os
import platform
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

try:  # Prefer async httpx if available
    import httpx
except ImportError:  # pragma: no cover - fallback for minimal installs
    httpx = None
import requests

from backend.config import settings
from backend.constants import (
    EMBEDDING_MODEL_DEFAULT,
    FAST_MODEL_DEFAULT,
    REASONING_MODEL_DEFAULT,
)
from backend.core.cloud_llm_client import CloudLLMClient
from backend.core.monitoring import get_logger


class FlightCheck:
    """Run a comprehensive readiness check for the backend stack."""

    REQUIRED_PYTHON: tuple[int, int] = (3, 9)
    REQUIRED_MODULES: Dict[str, str] = {
        "fastapi": "HTTP API framework",
        "langgraph": "Multi-agent orchestration",
        "playwright.async_api": "Dynamic scraping",
        "sqlalchemy": "Tool metadata database",
        "aiohttp": "Async networking for LLM + scraping",
    }
    def __init__(self) -> None:
        self.logger = get_logger("flight_check")
        self.results: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "unknown",
            "environment": {
                "python_version": platform.python_version(),
                "platform": platform.platform(),
                "llm_provider": settings.llm_provider,
                "vector_store": "in-memory",
                "groq_configured": bool(getattr(settings, "groq_api_key", None)),
                "openrouter_configured": bool(getattr(settings, "openrouter_api_key", None)),
                "gemini_configured": bool(getattr(settings, "gemini_api_key", None)),
            },
            "checks": {},
            "action_items": [],
        }

    async def run(self) -> Dict[str, Any]:
        """Execute all checks."""
        await asyncio.gather(
            self._check_python_environment(),
            self._check_runtime_dependencies(),
            self._check_llm_connectivity(),
            self._check_vector_store(),
            self._check_tool_database(),
            self._check_web_search(),
            self._check_supabase(),
        )
        self._finalize()
        return self.results

    def _record_check(
        self,
        name: str,
        status: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        suggestion: Optional[str] = None,
    ) -> None:
        """Store an individual check result."""
        self.results["checks"][name] = {
            "status": status,
            "message": message,
            "details": details or {},
        }
        if suggestion:
            self.results["checks"][name]["suggestion"] = suggestion

        if status in {"warning", "unhealthy", "error"}:
            self.results["action_items"].append(
                {
                    "component": name,
                    "status": status,
                    "message": message,
                    "suggestion": suggestion,
                }
            )

    def _finalize(self) -> None:
        """Compute overall status and summary."""
        statuses = [check["status"] for check in self.results["checks"].values()]
        if any(status in {"unhealthy", "error"} for status in statuses):
            self.results["overall_status"] = "degraded"
        elif any(status == "warning" for status in statuses):
            self.results["overall_status"] = "warning"
        else:
            self.results["overall_status"] = "healthy"

        summary: List[str] = []
        for name, check in self.results["checks"].items():
            summary.append(f"{name}: {check['status']} - {check['message']}")
        self.results["summary"] = summary

    async def _check_python_environment(self) -> None:
        """Ensure Python version meets minimum requirements."""
        version_info = sys.version_info
        meets_requirement = version_info >= self.REQUIRED_PYTHON
        status = "healthy" if meets_requirement else "unhealthy"
        message = (
            f"Python {version_info.major}.{version_info.minor} detected"
            if meets_requirement
            else "Python 3.9+ required"
        )
        details = {
            "detected_version": f"{version_info.major}.{version_info.minor}.{version_info.micro}",
            "required_version": f"{self.REQUIRED_PYTHON[0]}.{self.REQUIRED_PYTHON[1]}+",
            "executable": sys.executable,
        }
        suggestion = None
        if not meets_requirement:
            suggestion = "Install Python 3.9+ and recreate the virtual environment."
        self._record_check("python_runtime", status, message, details, suggestion)

    async def _check_runtime_dependencies(self) -> None:
        """Verify critical Python packages are importable."""
        missing: List[Dict[str, str]] = []
        installed: List[Dict[str, Optional[str]]] = []

        for module_path, description in self.REQUIRED_MODULES.items():
            try:
                module = importlib.import_module(module_path)
                version = getattr(module, "__version__", None)
                installed.append(
                    {
                        "module": module_path,
                        "version": version,
                        "description": description,
                    }
                )
            except Exception as exc:  # pragma: no cover - import failure messaging
                missing.append(
                    {
                        "module": module_path,
                        "description": description,
                        "error": str(exc),
                    }
                )

        if missing:
            status = "unhealthy"
            message = f"{len(missing)} required modules missing"
            suggestion = "Run `pip install -r requirements.txt` inside your virtual environment."
        else:
            status = "healthy"
            message = "All critical Python packages are available"
            suggestion = None

        details = {"installed": installed, "missing": missing}
        self._record_check("python_dependencies", status, message, details, suggestion)

    async def _fetch_json(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 5.0,
    ) -> Dict[str, Any]:
        """Fetch JSON using httpx when available, otherwise requests in a thread."""
        if httpx is not None:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return response.json()

        def sync_request() -> Dict[str, Any]:
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response.json()

        return await asyncio.to_thread(sync_request)

    async def _check_llm_connectivity(self) -> None:
        """Validate cloud LLM connectivity (Groq -> OpenRouter -> Gemini)."""
        client = CloudLLMClient()
        try:
            statuses = await client.provider_statuses()
            ok = any(statuses.values())
        except Exception as exc:  # noqa: BLE001
            self._record_check(
                "llm_providers",
                "unhealthy",
                "No cloud LLM provider configured",
                {"error": str(exc)},
                "Set GROQ_API_KEY, OPENROUTER_API_KEY, or GEMINI_API_KEY in .env.",
            )
            return

        if ok:
            configured = {
                "groq": bool(getattr(settings, "groq_api_key", None)),
                "openrouter": bool(getattr(settings, "openrouter_api_key", None)),
                "gemini": bool(getattr(settings, "gemini_api_key", None)),
            }
            self._record_check(
                "llm_providers",
                "healthy",
                "At least one cloud LLM provider reachable",
                {"configured": configured, "providers": statuses},
            )
        else:
            self._record_check(
                "llm_providers",
                "unhealthy",
                "Cloud LLM providers unreachable",
                {"providers": statuses},
                "Verify API keys and outbound HTTPS connectivity.",
            )

    async def _check_vector_store(self) -> None:
        """Verify the in-memory vector store can be instantiated."""
        try:
            store = ArtisanVectorStore()
            counts = {name: len(entries) for name, entries in store.collections.items()}
            message = "Vector store in-memory collections initialized"
            details = {"collection_counts": counts}
            self._record_check("vector_store", "healthy", message, details)
        except Exception as exc:
            message = "Vector store initialization failed"
            details = {"error": str(exc), "error_type": type(exc).__name__}
            suggestion = "Ensure OPENROUTER_API_KEY is set so embeddings can be created."
            self._record_check("vector_store", "unhealthy", message, details, suggestion)

    async def _check_tool_database(self) -> None:
        """Ensure the SQLite tool database can be opened."""
        try:
            from sqlalchemy import text
            from backend.orchestration.tool_database import Tool, ToolDatabaseManager
        except ImportError as exc:
            message = "SQLAlchemy not available for tool database"
            details = {"error": str(exc)}
            suggestion = "Install backend dependencies to enable the tool registry."
            self._record_check("tool_database", "unhealthy", message, details, suggestion)
            return

        def probe() -> Dict[str, Any]:
            data_dir = Path("data")
            data_dir.mkdir(parents=True, exist_ok=True)
            manager = ToolDatabaseManager()
            session = manager.get_session()
            try:
                session.execute(text("SELECT 1"))
                total_tools = session.query(Tool).count()
                return {
                    "database_url": str(manager.engine.url),
                    "total_tools": total_tools,
                }
            finally:
                session.close()

        try:
            details = await asyncio.to_thread(probe)
        except Exception as exc:
            message = "Tool database unavailable"
            data = {"error": str(exc), "error_type": type(exc).__name__}
            suggestion = "Ensure ./data is writable and the SQLite file is not locked."
            self._record_check("tool_database", "unhealthy", message, data, suggestion)
            return

        self._record_check("tool_database", "healthy", "SQLite tool registry reachable", details)

    async def _check_web_search(self) -> None:
        """Check Tavily/SerpAPI keys that power the scraping stack."""
        tavily_key = getattr(settings, "tavily_api_key", "")
        serp_key = getattr(settings, "serpapi_key", "")

        if tavily_key:
            message = "Tavily API key configured"
            details = {
                "provider": "tavily",
                "api_key_preview": f"{tavily_key[:6]}..." if len(tavily_key) > 6 else "***",
                "impacts": ["Supply Hunter", "Growth Marketer", "Event Scout", "Web scraper"],
                "blocking": False,
            }
            self._record_check("web_search", "healthy", message, details)
            return

        if serp_key:
            message = "Fallback SerpAPI key configured – Tavily missing"
            details = {
                "provider": "serpapi",
                "api_key_preview": f"{serp_key[:6]}..." if len(serp_key) > 6 else "***",
                "impacts": [
                    "Search uses slower fallback; Tavily-specific features disabled",
                    "Web scraping limited to SerpAPI quotas",
                ],
                "blocking": False,
            }
            suggestion = "Set TAVILY_API_KEY in .env for the richer search experience."
            self._record_check("web_search", "warning", message, details, suggestion)
            return

        message = "No search API key configured – supplier/event discovery will fail"
        details = {
            "provider": None,
            "impacts": [
                "WebScraperService.search returns an error",
                "Supply Hunter / Growth / Events agents stop with setup guidance",
            ],
            "blocking": True,
        }
        suggestion = "Add TAVILY_API_KEY (preferred) or SERPAPI_KEY to .env, then restart backend."
        self._record_check("web_search", "unhealthy", message, details, suggestion)

    async def _check_supabase(self) -> None:
        """Validate Supabase configuration for cloud persistence."""
        if not getattr(settings, "supabase_url", None) or not getattr(settings, "supabase_key", None):
            self._record_check(
                "supabase",
                "warning",
                "Supabase not configured – falling back to local JSON store",
                {"configured": False},
                "Set SUPABASE_URL and SUPABASE_KEY to enable cloud persistence.",
            )
            return

        try:
            from backend.core.supabase_client import get_supabase_client

            client = get_supabase_client(settings.supabase_url, settings.supabase_key)
            healthy = await client.health_check()
        except Exception as exc:
            self._record_check(
                "supabase",
                "unhealthy",
                "Failed to connect to Supabase",
                {"configured": True, "error": str(exc)},
                "Verify Supabase credentials and whitelist the Cloud Run IP if required.",
            )
            return

        if healthy:
            self._record_check(
                "supabase",
                "healthy",
                "Supabase reachable",
                {
                    "configured": True,
                    "url": settings.supabase_url,
                },
            )
        else:
            self._record_check(
                "supabase",
                "warning",
                "Supabase client initialized but health probe failed",
                {"configured": True, "url": settings.supabase_url},
                "Check that the `_health` table exists and the service role key has access.",
            )
