"""
Embedding utilities powered by hosted OpenRouter embeddings.
No local model downloads are required.
"""
from __future__ import annotations

from typing import List, Optional, Sequence, Union

import aiohttp
from loguru import logger

from backend.config import settings
from backend.constants import (
    EMBEDDING_MODEL_DEFAULT,
    OPENROUTER_BASE_URL_DEFAULT,
    OPENROUTER_EMBEDDING_MODEL_DEFAULT,
)

TextInput = Union[str, Sequence[str]]


class EmbeddingClient:
    """
    Async embedding client that always calls hosted endpoints.
    """

    def __init__(
        self,
        model_name: str | None = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        configured = model_name or settings.embedding_model or EMBEDDING_MODEL_DEFAULT
        self.model_name = configured or OPENROUTER_EMBEDDING_MODEL_DEFAULT
        self.base_url = (base_url or settings.openrouter_base_url or OPENROUTER_BASE_URL_DEFAULT).rstrip("/")
        self.api_key = api_key or settings.openrouter_api_key

    async def embed(self, text: TextInput) -> Union[List[float], List[List[float]]]:
        """
        Generate embeddings via OpenRouter. Raises a helpful error if the API
        key is missing to avoid silent local fallbacks.
        """
        if not self.api_key:
            raise RuntimeError("OpenRouter API key missing. Set OPENROUTER_API_KEY to enable embeddings.")

        payload: dict[str, object] = {
            "input": text,
            "model": self.model_name or OPENROUTER_EMBEDDING_MODEL_DEFAULT,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        logger.info("OpenRouter generating embeddings (cloud).")
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/embeddings",
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
