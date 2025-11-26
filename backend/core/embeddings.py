"""
Embedding utilities powered by SentenceTransformers.
Provides an async-friendly interface so the rest of the codebase
no longer depends on a running Ollama instance for embeddings.
"""
from __future__ import annotations

import asyncio
from functools import lru_cache
from typing import Iterable, List, Sequence, Union

import aiohttp
from loguru import logger
from sentence_transformers import SentenceTransformer

from backend.config import settings
from backend.constants import (
    EMBEDDING_MODEL_DEFAULT,
    OPENROUTER_BASE_URL_DEFAULT,
    OPENROUTER_EMBEDDING_MODEL_DEFAULT,
    OLLAMA_EMBEDDING_MODEL_DEFAULT,
)

TextInput = Union[str, Sequence[str]]


def _normalize_model_name(model_name: str) -> str:
    """
    Map historical identifiers (Ollama style) to Hugging Face checkpoints.
    """
    if not model_name:
        return EMBEDDING_MODEL_DEFAULT

    normalized = model_name.strip()
    if normalized in {"nomic-embed-text:latest", "nomic-embed-text"}:
        return "nomic-ai/nomic-embed-text-v1.5"

    # Fall back to original value – SentenceTransformer
    # will raise a helpful error if the checkpoint is invalid.
    return normalized


@lru_cache(maxsize=4)
def _load_sentence_transformer(model_name: str) -> SentenceTransformer:
    resolved = _normalize_model_name(model_name)
    logger.info(f"Loading embedding model: {resolved}")
    model = SentenceTransformer(resolved)
    return model


class EmbeddingClient:
    """
    Thin async wrapper around SentenceTransformers.
    Uses thread executors to avoid blocking the event loop.
    """

    def __init__(self, model_name: str | None = None):
        configured = model_name or settings.embedding_model or EMBEDDING_MODEL_DEFAULT
        self.model_name = configured or OLLAMA_EMBEDDING_MODEL_DEFAULT

    async def embed(self, text: TextInput) -> Union[List[float], List[List[float]]]:
        if settings.openrouter_api_key:
            try:
                return await self._embed_openrouter(text)
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"OpenRouter embeddings failed: {exc}; falling back to local SentenceTransformers.")

        model = _load_sentence_transformer(self.model_name)

        def _encode() -> Union[List[float], List[List[float]]]:
            vectors = model.encode(text)
            if hasattr(vectors, "tolist"):
                return vectors.tolist()
            return vectors

        return await asyncio.to_thread(_encode)

    async def _embed_openrouter(self, text: TextInput) -> Union[List[float], List[List[float]]]:
        """
        Hosted embedding generation via OpenRouter to avoid local model downloads.
        """
        payload: dict[str, object] = {
            "input": text,
            "model": OPENROUTER_EMBEDDING_MODEL_DEFAULT,
        }
        headers = {
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "Content-Type": "application/json",
        }
        base_url = (settings.openrouter_base_url or OPENROUTER_BASE_URL_DEFAULT).rstrip("/")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{base_url}/embeddings",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60),
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(f"OpenRouter embedding error ({response.status}): {error_text}")

                data = await response.json()
                embeddings = [item["embedding"] for item in data.get("data", [])]
                if isinstance(text, str):
                    return embeddings[0] if embeddings else []
                return embeddings
