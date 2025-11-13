"""
ChromaDB vector store for Artisan Hub
"""
from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings
from loguru import logger
from backend.core.ollama_client import OllamaClient
from backend.config import settings
from backend.constants import (
    VECTOR_STORE_PERSIST_IMPL,
    COLLECTION_CRAFT_KNOWLEDGE,
    COLLECTION_SUPPLIER_DATA,
    COLLECTION_MARKET_INSIGHTS,
    COLLECTION_USER_CONTEXT,
    COLLECTION_ARTISAN_KNOWLEDGE,
    VECTOR_QUERY_DEFAULT_RESULTS
)


class ArtisanVectorStore:
    """
    ChromaDB vector store for Artisan Hub
    Collections:
    - craft_knowledge: Technical details about crafts
    - supplier_data: Verified supplier information
    - market_insights: Pricing and demand data
    - user_context: Personal artisan profiles
    """
    
    def __init__(self, persist_directory: Optional[str] = None):
        persist_dir = persist_directory or settings.chroma_db_path
        import os
        # Ensure directory exists
        os.makedirs(persist_dir, exist_ok=True)
        
        try:
            # Clear any ChromaDB environment variables that might force HTTP mode
            import os
            chroma_env_vars = [k for k in os.environ.keys() if k.startswith('CHROMA_')]
            for var in chroma_env_vars:
                del os.environ[var]

            # Try with explicit settings to force embedded mode
            self.client = chromadb.PersistentClient(
                path=persist_dir,
                settings=Settings(
                    allow_reset=True,
                    chroma_db_impl=VECTOR_STORE_PERSIST_IMPL,  # Force embedded implementation
                    anonymized_telemetry=False,
                    is_persistent=True
                )
            )
            logger.info(f"Using ChromaDB PersistentClient with embedded mode at {persist_dir}")
        except (chromadb.errors.ChromaError, OSError, ValueError) as e:
            logger.warning(f"Failed to create PersistentClient with Settings: {type(e).__name__}: {e}, trying simple approach")
            try:
                # Try simpler approach
                self.client = chromadb.PersistentClient(path=persist_dir)
                logger.info(f"Using ChromaDB PersistentClient at {persist_dir}")
            except (chromadb.errors.ChromaError, OSError) as e2:
                logger.warning(f"Failed to create PersistentClient: {type(e2).__name__}: {e2}, trying EphemeralClient")
                try:
                    # Last resort - ephemeral client (won't persist but works)
                    self.client = chromadb.EphemeralClient()
                    logger.warning(f"Using ChromaDB EphemeralClient (data won't persist)")
                except Exception as e3:
                    logger.error(f"Failed to initialize any ChromaDB client: {type(e3).__name__}: {e3}")
                    raise RuntimeError("Could not initialize ChromaDB client in any mode") from e3
        
        self.ollama_client = OllamaClient()
        self.collection_name = COLLECTION_ARTISAN_KNOWLEDGE  # Main collection
        self.collection = None  # Will be initialized

        # Auto-initialize collections immediately
        self._initialize_collections()
        
        logger.info("ChromaDB initialized successfully")
    
    def _initialize_collections(self):
        """Initialize all collections on startup"""
        try:
            # Create or get main collection
            self.collection = self._get_or_create_collection(self.collection_name)

            # Initialize sub-collections
            self.collections = {
                COLLECTION_CRAFT_KNOWLEDGE: self._get_or_create_collection(COLLECTION_CRAFT_KNOWLEDGE),
                COLLECTION_SUPPLIER_DATA: self._get_or_create_collection(COLLECTION_SUPPLIER_DATA),
                COLLECTION_MARKET_INSIGHTS: self._get_or_create_collection(COLLECTION_MARKET_INSIGHTS),
                COLLECTION_USER_CONTEXT: self._get_or_create_collection(COLLECTION_USER_CONTEXT)
            }
            logger.success("ChromaDB collections initialized successfully")
        except (chromadb.errors.ChromaError, RuntimeError) as e:
            logger.error(f"Failed to initialize ChromaDB collections: {type(e).__name__}: {e}")
            # Create fallback empty collections dict
            self.collections = {}
            self.collection = None
    
    def _get_or_create_collection(self, name: str):
        """Get or create a collection"""
        try:
            collection = self.client.get_collection(name)
            logger.debug(f"Retrieved existing collection: {name}")
            return collection
        except chromadb.errors.ChromaError as e:
            logger.debug(f"Collection {name} does not exist, creating it: {e}")
            try:
                collection = self.client.create_collection(name)
                logger.info(f"Created new collection: {name}")
                return collection
            except chromadb.errors.ChromaError as create_error:
                logger.error(f"Failed to create collection {name}: {type(create_error).__name__}: {create_error}")
                raise RuntimeError(f"Could not create collection {name}") from create_error
    
    def get_collection(self):
        """Get the main collection"""
        if self.collection is None:
            self.collection = self._get_or_create_collection(self.collection_name)
        return self.collection
    
    async def add_document(
        self,
        collection_name: str,
        document: str,
        metadata: Dict,
        doc_id: Optional[str] = None
    ):
        """
        Add document to collection with embedding
        
        Args:
            collection_name: Name of collection
            document: Document text
            metadata: Document metadata
            doc_id: Optional document ID
        """
        if collection_name not in self.collections:
            raise ValueError(f"Invalid collection: {collection_name}")
        
        # Generate embedding
        async with self.ollama_client as client:
            embedding = await client.embed(document)
        
        # Add to collection
        collection = self.collections[collection_name]
        
        if doc_id is None:
            import uuid
            doc_id = str(uuid.uuid4())
        
        collection.add(
            embeddings=[embedding],
            documents=[document],
            metadatas=[metadata],
            ids=[doc_id]
        )
        
        logger.info(f"Added document to {collection_name}: {doc_id}")
        return doc_id
    
    async def query(
        self,
        collection_name: str,
        query_text: str,
        n_results: int = VECTOR_QUERY_DEFAULT_RESULTS,
        where: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Query collection for similar documents
        
        Args:
            collection_name: Name of collection
            query_text: Query text
            n_results: Number of results to return
            where: Metadata filter
        
        Returns:
            List of matching documents with metadata
        """
        # Ensure collection exists
        if collection_name not in self.collections:
            # Try to initialize it
            try:
                self.collections[collection_name] = self._get_or_create_collection(collection_name)
            except (RuntimeError, chromadb.errors.ChromaError) as e:
                logger.error(f"Failed to access collection {collection_name}: {type(e).__name__}: {e}")
                raise ValueError(f"Invalid collection: {collection_name}") from e
        
        # Generate query embedding
        async with self.ollama_client as client:
            query_embedding = await client.embed(query_text)
        
        # Query collection
        collection = self.collections[collection_name]
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where
        )
        
        # Format results
        formatted_results = []
        for i in range(len(results['ids'][0])):
            formatted_results.append({
                'id': results['ids'][0][i],
                'document': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i]
            })
        
        logger.info(f"Found {len(formatted_results)} results for query")
        return formatted_results
    
    def get_collection_count(self, collection_name: str) -> int:
        """Get document count in collection"""
        collection = self.collections[collection_name]
        return collection.count()


# Test the vector store
async def test_vector_store():
    store = ArtisanVectorStore("./data/test_chroma")
    
    # Add some test documents
    print("Adding test documents...")
    await store.add_document(
        "craft_knowledge",
        "Blue pottery requires special glazes and high-temperature kilns",
        {"craft": "pottery", "type": "technical"},
        "doc1"
    )
    
    await store.add_document(
        "supplier_data",
        "Rajasthan Clay Suppliers in Jaipur sells pottery clay for Rs 500/kg",
        {"location": "Jaipur", "type": "clay", "verified": True},
        "doc2"
    )
    
    # Query
    print("\nQuerying for pottery information...")
    results = await store.query(
        "craft_knowledge",
        "What do I need for pottery?",
        n_results=2
    )
    
    for i, result in enumerate(results):
        print(f"\nResult {i+1}:")
        print(f"  Document: {result['document']}")
        print(f"  Metadata: {result['metadata']}")
        print(f"  Distance: {result['distance']:.4f}")
    
    # Check counts
    print(f"\nCollection counts:")
    for name in store.collections:
        count = store.get_collection_count(name)
        print(f"  {name}: {count} documents")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_vector_store())
