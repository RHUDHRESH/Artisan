from __future__ import annotations
"""
Tool interface and registry. Wraps concrete capabilities for agent planning/execution.
"""
from typing import Protocol, Dict, Any, Callable, List, Optional
from dataclasses import dataclass
from loguru import logger
import asyncio
import json


class Tool(Protocol):
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    async def run(self, **kwargs) -> Any: ...


@dataclass
class ToolSpec:
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    factory: Callable[[], Tool]


class ToolRegistry:
    def __init__(self):
        self._specs: Dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec):
        logger.debug(f"Registering tool: {spec.name}")
        self._specs[spec.name] = spec

    def list_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": s.name,
                "description": s.description,
                "input_schema": s.input_schema,
                "output_schema": s.output_schema,
            }
            for s in self._specs.values()
        ]

    def get(self, name: str) -> Tool:
        spec = self._specs.get(name)
        if not spec:
            raise KeyError(f"Unknown tool: {name}")
        return spec.factory()


_GLOBAL_REGISTRY: Optional[ToolRegistry] = None


def global_tool_registry() -> ToolRegistry:
    global _GLOBAL_REGISTRY
    if _GLOBAL_REGISTRY is None:
        _GLOBAL_REGISTRY = default_tool_registry()
    return _GLOBAL_REGISTRY


# Built-in tool wrappers around existing services
class WebSearchTool:
    name = "web.search"
    description = "Search the web (region-aware). Returns SERP results."
    input_schema = {"type": "object", "properties": {"query": {"type": "string"}, "region": {"type": "string", "default": "in"}, "num_results": {"type": "integer", "default": 10}}, "required": ["query"]}
    output_schema = {"type": "array"}

    def __init__(self):
        from backend.scraping.web_scraper import WebScraperService
        self._svc = WebScraperService()

    async def run(self, **kwargs):
        return await self._svc.search(kwargs["query"], region=kwargs.get("region", "in"), num_results=kwargs.get("num_results", 10))


class WebScrapeTool:
    name = "web.scrape"
    description = "Fetch page content, optionally using Playwright for dynamic pages."
    input_schema = {"type": "object", "properties": {"url": {"type": "string"}, "use_playwright": {"type": "boolean", "default": False}}, "required": ["url"]}
    output_schema = {"type": "string"}

    def __init__(self):
        from backend.scraping.web_scraper import WebScraperService
        self._svc = WebScraperService()

    async def run(self, **kwargs):
        return await self._svc.scrape_page(kwargs["url"], use_playwright=kwargs.get("use_playwright", False))


class ExtractEntitiesTool:
    name = "nlp.extract_entities"
    description = "LLM-based structured extraction from text (JSON)."
    input_schema = {"type": "object", "properties": {"text": {"type": "string"}, "schema_hint": {"type": "string"}}, "required": ["text"]}
    output_schema = {"type": "object"}

    def __init__(self):
        from backend.core.ollama_client import OllamaClient
        self._llm = OllamaClient()

    async def run(self, **kwargs):
        prompt = (
            "Extract structured JSON according to schema hint if provided. Return only JSON.\n"
            + (f"SCHEMA_HINT: {kwargs.get('schema_hint')}\n" if kwargs.get("schema_hint") else "")
            + f"TEXT:\n{kwargs['text'][:4000]}"
        )
        return await self._llm.reasoning_task(prompt)


class RAGQueryTool:
    name = "rag.query"
    description = "Query vector store for relevant documents."
    input_schema = {"type": "object", "properties": {"collection": {"type": "string"}, "query": {"type": "string"}, "k": {"type": "integer", "default": 5}}, "required": ["collection", "query"]}
    output_schema = {"type": "array"}

    def __init__(self):
        from backend.core.rag_engine import RAGEngine
        self._rag = RAGEngine()

    async def run(self, **kwargs):
        return await self._rag.query(kwargs["collection"], kwargs["query"], k=kwargs.get("k", 5))


class MapsDistanceTool:
    name = "maps.distance"
    description = "Compute approximate driving distance/time between two points."
    input_schema = {"type": "object", "properties": {"origin": {"type": "object"}, "destination": {"type": "object"}}, "required": ["origin", "destination"]}
    output_schema = {"type": "object"}

    def __init__(self):
        from backend.services.maps_service import MapsService
        self._maps = MapsService()

    async def run(self, **kwargs):
        return await self._maps.estimate_distance(kwargs["origin"], kwargs["destination"])


# Additional general-purpose tools to empower agentic workflows
class HttpFetchTool:
    name = "http.fetch"
    description = "Fetch raw text from a URL (GET)."
    input_schema = {"type": "object", "properties": {"url": {"type": "string"}, "timeout": {"type": "integer", "default": 20}}, "required": ["url"]}
    output_schema = {"type": "object"}

    async def run(self, **kwargs):
        import aiohttp
        timeout = aiohttp.ClientTimeout(total=kwargs.get("timeout", 20))
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(kwargs["url"]) as resp:
                text = await resp.text(errors="ignore")
                return {"status": resp.status, "headers": dict(resp.headers), "text": text[:200000]}


class UrlNormalizeTool:
    name = "url.normalize"
    description = "Normalize/resolve URLs (basic heuristics)."
    input_schema = {"type": "object", "properties": {"base": {"type": "string"}, "path": {"type": "string"}}, "required": ["base", "path"]}
    output_schema = {"type": "string"}

    async def run(self, **kwargs):
        from urllib.parse import urljoin
        return urljoin(kwargs["base"], kwargs["path"])


class ContentHashTool:
    name = "content.hash"
    description = "Compute sha256 hash of text."
    input_schema = {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}
    output_schema = {"type": "string"}

    async def run(self, **kwargs):
        import hashlib
        return hashlib.sha256(kwargs["text"].encode("utf-8", errors="ignore")).hexdigest()


class DeduplicateResultsTool:
    name = "results.deduplicate"
    description = "Deduplicate list of dicts by a key."
    input_schema = {"type": "object", "properties": {"items": {"type": "array"}, "key": {"type": "string"}}, "required": ["items", "key"]}
    output_schema = {"type": "array"}

    async def run(self, **kwargs):
        seen = set()
        out = []
        for item in kwargs["items"]:
            val = item.get(kwargs["key"]) if isinstance(item, dict) else None
            if val and val not in seen:
                seen.add(val)
                out.append(item)
        return out


class JsonSchemaValidateTool:
    name = "json.validate"
    description = "Validate that JSON object contains required keys."
    input_schema = {"type": "object", "properties": {"data": {"type": "object"}, "required": {"type": "array"}}, "required": ["data"]}
    output_schema = {"type": "object"}

    async def run(self, **kwargs):
        required = kwargs.get("required") or []
        data = kwargs["data"]
        missing = [k for k in required if k not in data]
        return {"ok": len(missing) == 0, "missing": missing}


class SummarizeTool:
    name = "nlp.summarize"
    description = "Summarize text briefly (LLM)."
    input_schema = {"type": "object", "properties": {"text": {"type": "string"}, "style": {"type": "string"}}, "required": ["text"]}
    output_schema = {"type": "string"}

    def __init__(self):
        from backend.core.ollama_client import OllamaClient
        self._llm = OllamaClient()

    async def run(self, **kwargs):
        style = kwargs.get("style") or "concise"
        return await self._llm.fast_task(f"Summarize in a {style} style:\n\n{kwargs['text'][:4000]}")


class ClassifyTool:
    name = "nlp.classify"
    description = "Classify text into given labels (LLM)."
    input_schema = {"type": "object", "properties": {"text": {"type": "string"}, "labels": {"type": "array"}}, "required": ["text", "labels"]}
    output_schema = {"type": "object"}

    def __init__(self):
        from backend.core.ollama_client import OllamaClient
        self._llm = OllamaClient()

    async def run(self, **kwargs):
        labels = kwargs["labels"]
        prompt = "Classify the text into one of these labels: " + ", ".join(labels) + ". Return JSON {label: string}.\n\n" + kwargs["text"][:2000]
        return await self._llm.fast_task(prompt)


class TranslateTool:
    name = "nlp.translate"
    description = "Translate text to a target language (LLM)."
    input_schema = {"type": "object", "properties": {"text": {"type": "string"}, "target_lang": {"type": "string"}}, "required": ["text", "target_lang"]}
    output_schema = {"type": "string"}

    def __init__(self):
        from backend.core.ollama_client import OllamaClient
        self._llm = OllamaClient()

    async def run(self, **kwargs):
        return await self._llm.fast_task(f"Translate to {kwargs['target_lang']}:\n\n{kwargs['text'][:4000]}")


class TableExtractTool:
    name = "nlp.extract_table"
    description = "Extract table-like JSON from semi-structured text (LLM)."
    input_schema = {"type": "object", "properties": {"text": {"type": "string"}, "columns": {"type": "array"}}, "required": ["text", "columns"]}
    output_schema = {"type": "array"}

    def __init__(self):
        from backend.core.ollama_client import OllamaClient
        self._llm = OllamaClient()

    async def run(self, **kwargs):
        cols = ", ".join(kwargs["columns"])[:200]
        prompt = f"Extract a JSON array of rows with columns [{cols}] from:\n\n{kwargs['text'][:4000]}\nReturn ONLY JSON array."
        return await self._llm.reasoning_task(prompt)


class EmailExtractTool:
    name = "contact.extract_emails"
    description = "Extract emails from text."
    input_schema = {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}
    output_schema = {"type": "array"}

    async def run(self, **kwargs):
        import re
        return re.findall(r"[\w\.-]+@[\w\.-]+", kwargs["text"])


class PhoneExtractTool:
    name = "contact.extract_phones"
    description = "Extract phone numbers from text (heuristic)."
    input_schema = {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}
    output_schema = {"type": "array"}

    async def run(self, **kwargs):
        import re
        return re.findall(r"\b\+?\d[\d\s-]{7,}\b", kwargs["text"])


class SitemapDiscoverTool:
    name = "web.sitemap_discover"
    description = "Try fetching /sitemap.xml and return content if available."
    input_schema = {"type": "object", "properties": {"base_url": {"type": "string"}}, "required": ["base_url"]}
    output_schema = {"type": "object"}

    async def run(self, **kwargs):
        import aiohttp
        url = kwargs["base_url"].rstrip("/") + "/sitemap.xml"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    return {"status": 200, "url": url, "text": (await resp.text(errors="ignore"))[:200000]}
                return {"status": resp.status, "url": url, "text": ""}


class RobotsCheckTool:
    name = "web.robots_txt"
    description = "Fetch robots.txt"
    input_schema = {"type": "object", "properties": {"base_url": {"type": "string"}}, "required": ["base_url"]}
    output_schema = {"type": "object"}

    async def run(self, **kwargs):
        import aiohttp
        url = kwargs["base_url"].rstrip("/") + "/robots.txt"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                txt = await resp.text(errors="ignore")
                return {"status": resp.status, "text": txt[:200000]}


class RateLimitSleepTool:
    name = "control.sleep"
    description = "Async sleep to respect rate limits or pacing."
    input_schema = {"type": "object", "properties": {"seconds": {"type": "number"}}, "required": ["seconds"]}
    output_schema = {"type": "null"}

    async def run(self, **kwargs):
        await asyncio.sleep(float(kwargs["seconds"]))
        return None


class MergeArtifactsTool:
    name = "util.merge_artifacts"
    description = "Merge arrays/objects simply."
    input_schema = {"type": "object", "properties": {"a": {}, "b": {}}, "required": ["a", "b"]}
    output_schema = {}

    async def run(self, **kwargs):
        a, b = kwargs["a"], kwargs["b"]
        if isinstance(a, list) and isinstance(b, list):
            return a + b
        if isinstance(a, dict) and isinstance(b, dict):
            c = dict(a)
            c.update(b)
            return c
        return b


def default_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(ToolSpec(WebSearchTool.name, WebSearchTool.description, WebSearchTool.input_schema, WebSearchTool.output_schema, lambda: WebSearchTool()))
    registry.register(ToolSpec(WebScrapeTool.name, WebScrapeTool.description, WebScrapeTool.input_schema, WebScrapeTool.output_schema, lambda: WebScrapeTool()))
    registry.register(ToolSpec(ExtractEntitiesTool.name, ExtractEntitiesTool.description, ExtractEntitiesTool.input_schema, ExtractEntitiesTool.output_schema, lambda: ExtractEntitiesTool()))
    registry.register(ToolSpec(RAGQueryTool.name, RAGQueryTool.description, RAGQueryTool.input_schema, RAGQueryTool.output_schema, lambda: RAGQueryTool()))
    registry.register(ToolSpec(MapsDistanceTool.name, MapsDistanceTool.description, MapsDistanceTool.input_schema, MapsDistanceTool.output_schema, lambda: MapsDistanceTool()))
    # Additional tools
    registry.register(ToolSpec(HttpFetchTool.name, HttpFetchTool.description, HttpFetchTool.input_schema, HttpFetchTool.output_schema, lambda: HttpFetchTool()))
    registry.register(ToolSpec(UrlNormalizeTool.name, UrlNormalizeTool.description, UrlNormalizeTool.input_schema, UrlNormalizeTool.output_schema, lambda: UrlNormalizeTool()))
    registry.register(ToolSpec(ContentHashTool.name, ContentHashTool.description, ContentHashTool.input_schema, ContentHashTool.output_schema, lambda: ContentHashTool()))
    registry.register(ToolSpec(DeduplicateResultsTool.name, DeduplicateResultsTool.description, DeduplicateResultsTool.input_schema, DeduplicateResultsTool.output_schema, lambda: DeduplicateResultsTool()))
    registry.register(ToolSpec(JsonSchemaValidateTool.name, JsonSchemaValidateTool.description, JsonSchemaValidateTool.input_schema, JsonSchemaValidateTool.output_schema, lambda: JsonSchemaValidateTool()))
    registry.register(ToolSpec(SummarizeTool.name, SummarizeTool.description, SummarizeTool.input_schema, SummarizeTool.output_schema, lambda: SummarizeTool()))
    registry.register(ToolSpec(ClassifyTool.name, ClassifyTool.description, ClassifyTool.input_schema, ClassifyTool.output_schema, lambda: ClassifyTool()))
    registry.register(ToolSpec(TranslateTool.name, TranslateTool.description, TranslateTool.input_schema, TranslateTool.output_schema, lambda: TranslateTool()))
    registry.register(ToolSpec(TableExtractTool.name, TableExtractTool.description, TableExtractTool.input_schema, TableExtractTool.output_schema, lambda: TableExtractTool()))
    registry.register(ToolSpec(EmailExtractTool.name, EmailExtractTool.description, EmailExtractTool.input_schema, EmailExtractTool.output_schema, lambda: EmailExtractTool()))
    registry.register(ToolSpec(PhoneExtractTool.name, PhoneExtractTool.description, PhoneExtractTool.input_schema, PhoneExtractTool.output_schema, lambda: PhoneExtractTool()))
    registry.register(ToolSpec(SitemapDiscoverTool.name, SitemapDiscoverTool.description, SitemapDiscoverTool.input_schema, SitemapDiscoverTool.output_schema, lambda: SitemapDiscoverTool()))
    registry.register(ToolSpec(RobotsCheckTool.name, RobotsCheckTool.description, RobotsCheckTool.input_schema, RobotsCheckTool.output_schema, lambda: RobotsCheckTool()))
    registry.register(ToolSpec(RateLimitSleepTool.name, RateLimitSleepTool.description, RateLimitSleepTool.input_schema, RateLimitSleepTool.output_schema, lambda: RateLimitSleepTool()))
    registry.register(ToolSpec(MergeArtifactsTool.name, MergeArtifactsTool.description, MergeArtifactsTool.input_schema, MergeArtifactsTool.output_schema, lambda: MergeArtifactsTool()))
    return registry


