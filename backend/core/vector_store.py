"""
In-process vector store that keeps embeddings in memory.
Designed for cloud-only deployments without external vector databases.
"""
from __future__ import annotations

from typing import Dict, List, Optional
import math
import uuid

from backend.constants import (
    VECTOR_QUERY_DEFAULT_RESULTS,
    COLLECTION_ARTISAN_KNOWLEDGE,
    COLLECTION_CRAFT_KNOWLEDGE,
    COLLECTION_SUPPLIER_DATA,
    COLLECTION_MARKET_INSIGHTS,
    COLLECTION_USER_CONTEXT,
)
from backend.core.embeddings import EmbeddingClient
from loguru import logger


def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Compute cosine similarity between two vectors (returns 0 on zero-vector)."""
    dot = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


class ArtisanVectorStore:
    """
    Lightweight vector store backed by in-memory collections and hosted embeddings.
    This mirrors the previous vector store behavior without relying on an external service.
    """

    def __init__(
        self,
        embedding_client: Optional[EmbeddingClient] = None,
        *,
        persist_directory: Optional[str] = None
    ):
        self.embedding_client = embedding_client or EmbeddingClient()
        self.collections: Dict[str, List[Dict]] = {
            COLLECTION_ARTISAN_KNOWLEDGE: [],
            COLLECTION_CRAFT_KNOWLEDGE: [],
            COLLECTION_SUPPLIER_DATA: [],
            COLLECTION_MARKET_INSIGHTS: [],
            COLLECTION_USER_CONTEXT: [],
        }

    async def add_document(
        self,
        collection_name: str,
        document: str,
        metadata: Dict,
        doc_id: Optional[str] = None
    ) -> str:
        """Add a document with its embedding to the specified collection."""
        if collection_name not in self.collections:
            raise ValueError(f"Invalid collection: {collection_name}")

        embedding = await self.embedding_client.embed(document)

        item = {
            "id": doc_id or str(uuid.uuid4()),
            "document": document,
            "metadata": metadata,
            "embedding": embedding,
        }
        self.collections[collection_name].append(item)
        logger.info(f"Stored document {item['id']} in collection {collection_name}")
        return item["id"]

    async def query(
        self,
        collection_name: str,
        query_text: str,
        n_results: int = VECTOR_QUERY_DEFAULT_RESULTS,
        where: Optional[Dict] = None
    ) -> List[Dict]:
        """Query a collection by computing embeddings and ranking by cosine similarity."""
        if collection_name not in self.collections:
            raise ValueError(f"Invalid collection: {collection_name}")

        query_embedding = await self.embedding_client.embed(query_text)
        candidates = self.collections[collection_name]

        scored: List[Dict] = []
        for entry in candidates:
            if where:
                metadata = entry.get("metadata", {})
                if not all(metadata.get(k) == v for k, v in where.items()):
                    continue

            similarity = _cosine_similarity(entry["embedding"], query_embedding)
            scored.append({
                "id": entry["id"],
                "document": entry["document"],
                "metadata": entry.get("metadata", {}),
                "distance": 1.0 - similarity,
                "similarity": similarity
            })

        scored.sort(key=lambda x: x["distance"])
        return scored[:n_results]

    def get_collection(self, collection_name: str) -> List[Dict]:
        """Return raw collection entries."""
        return self.collections.get(collection_name, [])

    def get_collection_count(self, collection_name: str) -> int:
        """Return number of stored documents in a collection."""
        return len(self.collections.get(collection_name, []))
