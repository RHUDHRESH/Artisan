"""
Unified cloud LLM client for Artisan Hub.

Order of operations:
1) Groq (primary)
2) OpenRouter (fallback)
3) Gemini (fallback)

No local runtimes are required; everything runs against hosted APIs.
"""
from __future__ import annotations

from typing import Dict, List, Optional

import aiohttp
from loguru import logger

from backend.config import settings
from backend.constants import (
    EMBEDDING_MODEL_DEFAULT,
    FAST_MODEL_DEFAULT,
    GEMINI_MODEL_DEFAULT,
    OPENROUTER_BASE_URL_DEFAULT,
    OPENROUTER_EMBEDDING_MODEL_DEFAULT,
    OPENROUTER_FAST_MODEL_DEFAULT,
    OPENROUTER_REASONING_MODEL_DEFAULT,
    REASONING_MODEL_DEFAULT,
)
from backend.core.embeddings import EmbeddingClient


class OllamaClient:
    """
    Backwards compatible interface used across the codebase.
    Under the hood it routes requests to Groq (remote) and falls back to
    OpenRouter and Gemini so we remain 100% cloud-hosted.
    """

    def __init__(
        self,
        llm_provider: Optional[str] = None,
        groq_api_key: Optional[str] = None,
        openrouter_api_key: Optional[str] = None,
        gemini_api_key: Optional[str] = None,
    ):
        self.provider = (llm_provider or settings.llm_provider or "groq").lower()

        self.groq_api_key = groq_api_key or settings.groq_api_key
        self.groq_api_base = "https://api.groq.com/openai/v1"

        self.openrouter_api_key = openrouter_api_key or settings.openrouter_api_key
        self.openrouter_base_url = (
            settings.openrouter_base_url or OPENROUTER_BASE_URL_DEFAULT
        ).rstrip("/")
        self.openrouter_reasoning_model = (
            settings.openrouter_reasoning_model or OPENROUTER_REASONING_MODEL_DEFAULT
        )
        self.openrouter_fast_model = (
            settings.openrouter_fast_model or OPENROUTER_FAST_MODEL_DEFAULT
        )

        self.gemini_api_key = gemini_api_key or settings.gemini_api_key
        self.gemini_model = settings.gemini_model or GEMINI_MODEL_DEFAULT
        self.gemini_base_url = "https://generativelanguage.googleapis.com/v1beta"

        self.reasoning_model = settings.reasoning_model or REASONING_MODEL_DEFAULT
        self.fast_model = settings.fast_model or FAST_MODEL_DEFAULT
        self.embedding_model = settings.embedding_model or EMBEDDING_MODEL_DEFAULT
        self.embedding_client = EmbeddingClient(self.embedding_model)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return False

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: float = 0.7,
        stream: bool = False,
    ) -> str:
        """
        Generate a completion via the active provider.
        """
        target_model = model or self.reasoning_model
        errors: List[str] = []

        for provider in self._provider_chain():
            try:
                if provider == "groq":
                    return await self._generate_groq(
                        prompt=prompt,
                        model=target_model,
                        system=system,
                        temperature=temperature,
                    )
                if provider == "openrouter":
                    or_model = (
                        self.openrouter_reasoning_model
                        if target_model == self.reasoning_model
                        else self.openrouter_fast_model
                    )
                    return await self._generate_openrouter(
                        prompt=prompt,
                        model=or_model,
                        system=system,
                        temperature=temperature,
                    )
                if provider == "gemini":
                    return await self._generate_gemini(
                        prompt=prompt,
                        model=self.gemini_model,
                        system=system,
                        temperature=temperature,
                    )
            except Exception as exc:  # noqa: BLE001 - propagate aggregated
                msg = f"{provider} generation failed: {exc}"
                logger.warning(msg)
                errors.append(msg)
                continue

        raise RuntimeError(
            "All LLM providers failed. Tried: Groq, OpenRouter, Gemini. "
            + " | ".join(errors)
        )

    async def reasoning_task(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
    ) -> str:
        return await self.generate(
            prompt=prompt,
            model=self.reasoning_model,
            system=system,
            temperature=temperature,
        )

    async def fast_task(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.3,
    ) -> str:
        return await self.generate(
            prompt=prompt,
            model=self.fast_model,
            system=system,
            temperature=temperature,
        )

    async def embed(self, text: str) -> List[float]:
        """
        Generate embeddings using OpenRouter when available, otherwise
        fall back to the local SentenceTransformers backend.
        """
        if self.openrouter_api_key:
            try:
                return await self._embed_openrouter(text)
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"OpenRouter embeddings failed: {exc}; falling back to SentenceTransformers")

        vector = await self.embedding_client.embed(text)
        return vector  # Already converted to Python list

    async def health_check(self) -> bool:
        """
        Check whichever provider is configured.
        """
        for provider in self._provider_chain():
            try:
                if provider == "groq":
                    headers = self._groq_headers
                    async with aiohttp.ClientSession() as session:
                        async with session.get(
                            f"{self.groq_api_base}/models",
                            headers=headers,
                            timeout=aiohttp.ClientTimeout(total=5),
                        ) as response:
                            if response.status == 200:
                                return True
                elif provider == "openrouter":
                    headers = self._openrouter_headers
                    async with aiohttp.ClientSession() as session:
                        async with session.get(
                            f"{self.openrouter_base_url}/models",
                            headers=headers,
                            timeout=aiohttp.ClientTimeout(total=5),
                        ) as response:
                            if response.status == 200:
                                return True
                elif provider == "gemini":
                    params = {"key": self.gemini_api_key}
                    async with aiohttp.ClientSession() as session:
                        async with session.get(
                            f"{self.gemini_base_url}/models",
                            params=params,
                            timeout=aiohttp.ClientTimeout(total=5),
                        ) as response:
                            if response.status == 200:
                                return True
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"{provider} health check failed: {exc}")
                continue

        return False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _provider_chain(self) -> List[str]:
        """
        Ordered list of providers to try based on configured API keys.
        """
        chain: List[str] = []
        if self.groq_api_key:
            chain.append("groq")
        if self.openrouter_api_key:
            chain.append("openrouter")
        if self.gemini_api_key:
            chain.append("gemini")
        if not chain:
            raise RuntimeError("No cloud LLM provider configured. Set GROQ_API_KEY, OPENROUTER_API_KEY, or GEMINI_API_KEY.")
        return chain

    @property
    def _groq_headers(self) -> Dict[str, str]:
        if not self.groq_api_key:
            raise RuntimeError("GROQ_API_KEY is not configured.")
        return {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json",
        }

    async def _generate_groq(
        self,
        prompt: str,
        model: str,
        system: Optional[str],
        temperature: float,
    ) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 2048,
            "stream": False,
        }

        logger.info(f"Groq generating with {model}: {prompt[:100]}...")
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.groq_api_base}/chat/completions",
                headers=self._groq_headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60),
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(f"GROQ error ({response.status}): {error_text}")

                data = await response.json()
                content = data["choices"][0]["message"]["content"]
                return content

    @property
    def _openrouter_headers(self) -> Dict[str, str]:
        if not self.openrouter_api_key:
            raise RuntimeError("OPENROUTER_API_KEY is not configured.")
        return {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json",
        }

    async def _generate_openrouter(
        self,
        prompt: str,
        model: str,
        system: Optional[str],
        temperature: float,
    ) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": False,
        }

        logger.info(f"OpenRouter generating with {model}: {prompt[:100]}...")
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.openrouter_base_url}/chat/completions",
                headers=self._openrouter_headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120),
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(
                        f"OpenRouter error ({response.status}): {error_text}"
                    )
                data = await response.json()
                return data["choices"][0]["message"]["content"]

    async def _generate_gemini(
        self,
        prompt: str,
        model: str,
        system: Optional[str],
        temperature: float,
    ) -> str:
        contents: List[Dict[str, object]] = []
        if system:
            contents.append({"role": "system", "parts": [{"text": system}]})
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": 2048,
            },
        }

        logger.info(f"Gemini generating with {model}: {prompt[:100]}...")
        params = {"key": self.gemini_api_key}
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.gemini_base_url}/models/{model}:generateContent",
                params=params,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120),
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(
                        f"Gemini error ({response.status}): {error_text}"
                    )
                data = await response.json()
                candidates = data.get("candidates") or []
                if not candidates:
                    raise RuntimeError("Gemini returned no candidates")
                parts = candidates[0].get("content", {}).get("parts") or []
                return " ".join(part.get("text", "") for part in parts)

    async def _embed_openrouter(self, text: str | List[str]) -> List[float] | List[List[float]]:
        payload: Dict[str, object] = {
            "input": text,
            "model": OPENROUTER_EMBEDDING_MODEL_DEFAULT,
        }
        logger.info("OpenRouter generating embeddings...")
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.openrouter_base_url}/embeddings",
                headers=self._openrouter_headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60),
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(
                        f"OpenRouter embedding error ({response.status}): {error_text}"
                    )
                data = await response.json()
                embeddings = [item["embedding"] for item in data.get("data", [])]
                if isinstance(text, str) and embeddings:
                    return embeddings[0]
                return embeddings


# ----------------------------------------------------------------------
# Basic smoke test
# ----------------------------------------------------------------------
async def test_ollama_client():
    client = OllamaClient()

    print("Testing reasoning task (Groq preferred)...")
    reply = await client.reasoning_task(
        "Give me three marketing ideas for handcrafted pottery."
    )
    print(reply[:300])

    print("\nTesting fast classification...")
    quick = await client.fast_task("Classify this: carved sandalwood jewelry box")
    print(quick[:300])

    print("\nTesting embeddings...")
    vector = await client.embed("Blue pottery artisan from Jaipur seeking suppliers.")
    print(f"Embedding length: {len(vector)}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_ollama_client())
