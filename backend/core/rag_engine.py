"""
RAG Engine - Retrieval Augmented Generation implementation
"""
from typing import List, Dict, Optional
from backend.config import settings
from backend.core.ollama_client import OllamaClient
from backend.core.vector_store import ArtisanVectorStore
from loguru import logger


class RAGEngine:
    """
    RAG Engine for context-aware generation
    Retrieves relevant documents from vector store and uses them as context
    """
    
    def __init__(self, ollama_client: OllamaClient, vector_store: ArtisanVectorStore):
        self.ollama = ollama_client
        self.vector_store = vector_store
    
    async def generate_with_context(
        self,
        query: str,
        collection_name: str = "craft_knowledge",
        n_results: int = 3,
        system_prompt: Optional[str] = None,
        use_reasoning: bool = True
    ) -> Dict:
        """
        Generate response using RAG (Retrieval Augmented Generation)
        
        Args:
            query: User query
            collection_name: Vector store collection to search
            n_results: Number of relevant documents to retrieve
            system_prompt: System prompt
            use_reasoning: Use 4B model (True) or 1B model (False)
        
        Returns:
            Dictionary with response and context used
        """
        # Step 1: Retrieve relevant documents
        relevant_docs = await self.vector_store.query(
            collection_name=collection_name,
            query_text=query,
            n_results=n_results
        )
        
        logger.info(f"Retrieved {len(relevant_docs)} relevant documents")
        
        # Step 2: Build context from retrieved documents
        context = self._build_context(relevant_docs)
        
        # Step 3: Generate response with context
        prompt = f"""Context information:
{context}

User query: {query}

Provide a helpful answer based on the context above. If the context doesn't contain relevant information, say so."""
        
        if use_reasoning:
            response = await self.ollama.reasoning_task(
                prompt=prompt,
                system=system_prompt
            )
            model_used = settings.reasoning_model
        else:
            response = await self.ollama.fast_task(
                prompt=prompt,
                system=system_prompt
            )
            model_used = settings.fast_model
        
        return {
            "response": response,
            "context_used": relevant_docs,
            "model_used": model_used,
            "sources": [doc.get('metadata', {}) for doc in relevant_docs]
        }
    
    def _build_context(self, documents: List[Dict]) -> str:
        """
        Build context string from retrieved documents
        
        Args:
            documents: List of document dictionaries
        
        Returns:
            Formatted context string
        """
        context_parts = []
        
        for i, doc in enumerate(documents, 1):
            doc_text = doc.get('document', '')
            metadata = doc.get('metadata', {})
            
            context_parts.append(f"[Document {i}]")
            if metadata.get('source'):
                context_parts.append(f"Source: {metadata['source']}")
            context_parts.append(f"Content: {doc_text}")
            context_parts.append("")  # Blank line between documents
        
        return "\n".join(context_parts)
    
    async def query_craft_knowledge(self, query: str, n_results: int = 3) -> Dict:
        """Query craft knowledge collection"""
        return await self.generate_with_context(
            query=query,
            collection_name="craft_knowledge",
            n_results=n_results
        )
    
    async def query_supplier_data(self, query: str, n_results: int = 5) -> Dict:
        """Query supplier data collection"""
        return await self.generate_with_context(
            query=query,
            collection_name="supplier_data",
            n_results=n_results
        )
    
    async def query_market_insights(self, query: str, n_results: int = 3) -> Dict:
        """Query market insights collection"""
        return await self.generate_with_context(
            query=query,
            collection_name="market_insights",
            n_results=n_results
        )
    
    async def query_user_context(self, query: str, user_id: str, n_results: int = 3) -> Dict:
        """Query user context collection with user filter"""
        # Note: This would need metadata filtering support in vector_store
        relevant_docs = await self.vector_store.query(
            collection_name="user_context",
            query_text=query,
            n_results=n_results,
            where={"user_id": user_id} if user_id else None
        )
        
        context = self._build_context(relevant_docs)
        
        prompt = f"""User's previous context:
{context}

New query: {query}

Respond based on the user's history and context."""
        
        response = await self.ollama.reasoning_task(prompt=prompt)
        
        return {
            "response": response,
            "context_used": relevant_docs,
            "model_used": settings.reasoning_model
        }

