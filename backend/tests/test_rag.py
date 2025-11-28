"""
Tests for RAG (Retrieval Augmented Generation) functionality
"""
import pytest
from backend.core.cloud_llm_client import CloudLLMClient
from backend.core.vector_store import ArtisanVectorStore
from backend.core.rag_engine import RAGEngine


@pytest.mark.asyncio
class TestRAG:
    """Test RAG engine"""
    
    @pytest.fixture
    async def setup_rag(self):
        """Setup RAG engine"""
        llm = CloudLLMClient()
        vector_store = ArtisanVectorStore()
        rag_engine = RAGEngine(llm, vector_store)
        
        yield rag_engine
        
        # Cleanup if needed
    
    async def test_rag_generate_with_context(self, setup_rag):
        """Test RAG generation with context"""
        rag = setup_rag
        
        # First, add some test documents
        await rag.vector_store.add_document(
            "craft_knowledge",
            "Blue pottery requires special cobalt oxide glazes and high-temperature kilns around 1200°C",
            {"craft": "pottery", "type": "technical"},
            "test_doc_1"
        )
        
        # Now query with RAG
        result = await rag.generate_with_context(
            query="What temperature do I need for blue pottery?",
            collection_name="craft_knowledge",
            n_results=1
        )
        
        assert "response" in result, "Should return response"
        assert "context_used" in result, "Should include context used"
        assert "model_used" in result, "Should specify model used"
        assert len(result["context_used"]) > 0, "Should have retrieved context"
        
        print("✓ RAG generate with context: PASS")
    
    async def test_rag_query_craft_knowledge(self, setup_rag):
        """Test query craft knowledge"""
        rag = setup_rag
        
        result = await rag.query_craft_knowledge("pottery tools", n_results=2)
        
        assert "response" in result, "Should return response"
        assert isinstance(result["context_used"], list), "Context should be a list"
        
        print("✓ RAG query craft knowledge: PASS")
    
    async def test_rag_query_supplier_data(self, setup_rag):
        """Test query supplier data"""
        rag = setup_rag
        
        # Add test supplier data
        await rag.vector_store.add_document(
            "supplier_data",
            "Rajasthan Clay Suppliers provides high-quality pottery clay in Jaipur",
            {"location": "Jaipur", "type": "supplier", "verified": True},
            "test_supplier_1"
        )
        
        result = await rag.query_supplier_data("clay suppliers Jaipur", n_results=1)
        
        assert "response" in result, "Should return response"
        assert "sources" in result, "Should include sources"
        
        print("✓ RAG query supplier data: PASS")
    
    async def test_rag_build_context(self, setup_rag):
        """Test context building"""
        rag = setup_rag
        
        test_docs = [
            {
                "document": "Test document 1 about pottery",
                "metadata": {"source": "test1"}
            },
            {
                "document": "Test document 2 about glazes",
                "metadata": {"source": "test2"}
            }
        ]
        
        context = rag._build_context(test_docs)
        
        assert "[Document 1]" in context, "Should include document markers"
        assert "Test document 1" in context, "Should include document content"
        assert "Test document 2" in context, "Should include all documents"
        
        print("✓ RAG build context: PASS")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

