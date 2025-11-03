Artisan Hub - Complete Implementation Guide
Table of Contents

Project Overview
Technology Stack
System Architecture
File Structure
Phase 1: Core Setup
Phase 2: Agent Development
Phase 3: Advanced Features
Phase 4: Testing & Refinement
Verification & Quality Checks
Integration Guidelines


Project Overview
Mission Statement
Build a 100% local, privacy-first AI-powered ecosystem that helps artisans discover suppliers, identify growth opportunities, find events, and optimize their craft businesses using multi-agent intelligence.
Core Principles

ALL processing must be local - No cloud LLM APIs
Open source only - Every dependency must be free and open source
Real data only - No synthetic data, everything from live web scraping
Verification required - Every piece of scraped data must be verified with confidence scores
Audit trails mandatory - Complete logs of all searches, sources, and verification steps

Critical Requirements

Use Gemma 3 models ONLY (no Llama, no GPT, no other models)
All embeddings use Gemma 3 Embed
Dual-model system: 4B for reasoning, 1B for fast responses
India-first approach for all searches (expand globally only if needed)
Web-based interface (can be coded in any framework)
Must run entirely on user's PC


Technology Stack
Core AI/ML Stack (NON-NEGOTIABLE)
yamlLLM Runtime:
  - ollama: Latest version
  
Models (MANDATORY - NO SUBSTITUTIONS):
  - gemma3:4b          # For complex reasoning, analysis, planning
  - gemma3:1b          # For fast responses, classifications, routing
  - gemma3:embed       # For all embeddings and RAG
  
Agent Framework:
  - langchain: ^0.1.0  # Agent orchestration
  - llama-index: ^0.9.0 # RAG framework
  
Vector Database:
  - chromadb: ^0.4.0   # Local vector storage
Backend Stack
yamlPrimary Backend:
  - fastapi: ^0.104.0       # Python async API framework
  - pydantic: ^2.0          # Data validation
  - uvicorn: ^0.24.0        # ASGI server
  
Node.js (Optional for additional services):
  - express: ^4.18.0        # If needed for specific services
  
Database & Storage:
  - firebase-admin: ^6.0.0  # User data, notifications, authentication
  - sqlite3: ^3.42.0        # Local caching
Web Scraping Stack (CRITICAL)
yamlSearch:
  - serpapi: ^0.1.5         # Web search API
  
Scraping:
  - playwright: ^1.40.0     # Dynamic content scraping
  - beautifulsoup4: ^4.12.0 # HTML parsing
  - selenium: ^4.15.0       # Backup scraper
  
Data Processing:
  - pandas: ^2.0.0          # Data manipulation
  - numpy: ^1.24.0          # Numerical operations
Maps & Location Stack
yamlMaps:
  - folium: ^0.15.0         # Map visualization
  - mapbox: SDK             # Primary mapping API
  
Geolocation:
  - geopy: ^2.4.0           # Geocoding
  - python-incois: Latest   # INCOIS API integration (if available)
Frontend Stack (Your Choice)
yamlRecommended:
  - flutter: Latest         # Cross-platform mobile/web/desktop
  - figma: N/A              # UI/UX design
  
Alternatives:
  - react: ^18.0.0          # Web-only option
  - svelte: ^4.0.0          # Lightweight option
  - html/css/js: Vanilla    # Simplest option
Additional Tools
yamlUtilities:
  - python-dotenv: ^1.0.0   # Environment variables
  - requests: ^2.31.0       # HTTP client
  - aiohttp: ^3.9.0         # Async HTTP
  - loguru: ^0.7.0          # Logging
  
Testing:
  - pytest: ^7.4.0          # Unit tests
  - pytest-asyncio: ^0.21.0 # Async tests

System Architecture
High-Level Architecture
┌─────────────────────────────────────────────┐
│           USER INTERFACE                    │
│  (Web-based conversational interface)      │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│        ORCHESTRATION LAYER                  │
│  (FastAPI + LangChain + Ollama)            │
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │  Dual Model Router                   │  │
│  │  - Route to 4B for complex tasks     │  │
│  │  - Route to 1B for fast tasks        │  │
│  └──────────────────────────────────────┘  │
└─────────────────┬───────────────────────────┘
                  │
        ┌─────────┼─────────┬─────────┬────────┐
        ▼         ▼         ▼         ▼        ▼
    ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐  ┌───────┐
    │Profile│ │Supply │ │Growth │ │Event  │  │ Map   │
    │Analyst│ │Hunter │ │Market │ │Scout  │  │Service│
    │Agent  │ │Agent  │ │Agent  │ │Agent  │  │       │
    └───┬───┘ └───┬───┘ └───┬───┘ └───┬───┘  └───┬───┘
        │         │         │         │          │
        └─────────┴─────────┴─────────┴──────────┘
                          │
        ┌─────────────────┴─────────────────┐
        ▼                                   ▼
┌─────────────────┐              ┌─────────────────┐
│  WEB SCRAPING   │              │   VECTOR DB     │
│   PIPELINE      │              │   (ChromaDB)    │
│                 │              │                 │
│ - SerperAPI     │              │ - Craft Data    │
│ - Playwright    │              │ - Suppliers     │
│ - BeautifulSoup │              │ - Market Info   │
│ - Verification  │              │ - User Context  │
└─────────────────┘              └─────────────────┘
Data Flow Diagram
USER INPUT (Conversational)
    │
    ▼
Profile Analyst (Gemma 3 4B)
    │ - Parses unstructured text
    │ - Extracts: craft type, location, needs
    │ - Stores in ChromaDB
    │
    ├──────────────┬──────────────┬─────────────┐
    ▼              ▼              ▼             ▼
Supply Hunter  Growth Marketer  Event Scout  Map Service
    │              │              │             │
    │ Web Search   │ Trend Search │ Event Search│ Geocoding
    ▼              ▼              ▼             ▼
Playwright/BS4  Analysis (4B)  Calendar APIs  Folium/Mapbox
    │              │              │             │
    ▼              ▼              ▼             ▼
Verification   ROI Calculation  Match Scoring  Distance Calc
    │              │              │             │
    └──────────────┴──────────────┴─────────────┘
                   │
                   ▼
            Store in ChromaDB
                   │
                   ▼
            Present to User

File Structure
artisan-hub/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
│
├── backend/
│   ├── main.py                      # FastAPI app entry point
│   ├── config.py                    # Configuration management
│   ├── models.py                    # Pydantic models
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── ollama_client.py         # Ollama interface
│   │   ├── dual_model_router.py     # Route queries to 4B or 1B
│   │   ├── rag_engine.py            # RAG implementation
│   │   └── vector_store.py          # ChromaDB interface
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base_agent.py            # Abstract base agent
│   │   ├── profile_analyst.py       # Profile Analyst Agent
│   │   ├── supply_hunter.py         # Supply Hunter Agent
│   │   ├── growth_marketer.py       # Growth Marketer Agent
│   │   └── event_scout.py           # Event Scout Agent
│   │
│   ├── scraping/
│   │   ├── __init__.py
│   │   ├── web_scraper.py           # Main scraping orchestrator
│   │   ├── search_engine.py         # SerperAPI wrapper
│   │   ├── dynamic_scraper.py       # Playwright scraper
│   │   ├── static_scraper.py        # BeautifulSoup scraper
│   │   └── verifier.py              # Verification pipeline
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── maps_service.py          # Folium + Mapbox integration
│   │   ├── firebase_service.py      # Firebase integration
│   │   └── notification_service.py  # Alerts and notifications
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── chat.py              # Chat endpoints
│   │   │   ├── agents.py            # Agent endpoints
│   │   │   ├── maps.py              # Map endpoints
│   │   │   └── search.py            # Search endpoints
│   │   └── websocket.py             # WebSocket for real-time updates
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logger.py                # Logging configuration
│   │   ├── validators.py            # Input validators
│   │   └── helpers.py               # Utility functions
│   │
│   └── tests/
│       ├── __init__.py
│       ├── test_agents.py
│       ├── test_scraping.py
│       └── test_rag.py
│
├── frontend/                         # Your choice of framework
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── utils/
│   └── public/
│
├── data/
│   ├── chroma_db/                   # ChromaDB storage
│   ├── logs/                        # Search and verification logs
│   ├── cache/                       # Temporary cache
│   └── exports/                     # User data exports
│
└── docs/
    ├── API.md                       # API documentation
    ├── AGENTS.md                    # Agent specifications
    └── DEPLOYMENT.md                # Deployment guide

Phase 1: Core Setup (Week 1)
Step 1.1: Install Ollama and Models (DAY 1)
Expectations:

Ollama installed and running
All 3 Gemma 3 models pulled and verified
Test inference working

Implementation:
bash# Install Ollama (Linux/Mac)
curl -fsSL https://ollama.com/install.sh | sh

# Pull required models (MANDATORY - NO SUBSTITUTIONS)
ollama pull gemma3:4b
ollama pull gemma3:1b  
ollama pull gemma3:embed

# Verify installation
ollama list | grep gemma3
Verification Script:
python# backend/tests/test_ollama_setup.py
import requests
import json

def test_ollama_connection():
    """Verify Ollama is running"""
    try:
        response = requests.get("http://localhost:11434/api/tags")
        assert response.status_code == 200, "Ollama not responding"
        models = response.json()["models"]
        model_names = [m["name"] for m in models]
        
        # Check all required models
        assert "gemma3:4b" in model_names, "gemma3:4b not found"
        assert "gemma3:1b" in model_names, "gemma3:1b not found"
        assert "gemma3:embed" in model_names, "gemma3:embed not found"
        print("✓ All required models installed")
    except Exception as e:
        print(f"✗ Ollama setup failed: {e}")
        raise

def test_inference_4b():
    """Test 4B model inference"""
    payload = {
        "model": "gemma3:4b",
        "prompt": "What is 2+2?",
        "stream": False
    }
    response = requests.post(
        "http://localhost:11434/api/generate",
        json=payload
    )
    assert response.status_code == 200
    result = response.json()
    assert "response" in result
    print(f"✓ 4B model working: {result['response'][:50]}")

def test_inference_1b():
    """Test 1B model inference"""
    payload = {
        "model": "gemma3:1b",
        "prompt": "Hello",
        "stream": False
    }
    response = requests.post(
        "http://localhost:11434/api/generate",
        json=payload
    )
    assert response.status_code == 200
    print("✓ 1B model working")

def test_embeddings():
    """Test embedding model"""
    payload = {
        "model": "gemma3:embed",
        "prompt": "Test embedding"
    }
    response = requests.post(
        "http://localhost:11434/api/embeddings",
        json=payload
    )
    assert response.status_code == 200
    result = response.json()
    assert "embedding" in result
    assert len(result["embedding"]) > 0
    print(f"✓ Embedding model working (dim={len(result['embedding'])})")

if __name__ == "__main__":
    test_ollama_connection()
    test_inference_4b()
    test_inference_1b()
    test_embeddings()
    print("\n✓✓✓ All Ollama tests passed ✓✓✓")
Step 1.2: Setup FastAPI Backend (DAY 1)
Create virtual environment and install dependencies:
bash# Create project structure
mkdir -p artisan-hub/backend
cd artisan-hub/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Create requirements.txt
cat > requirements.txt << EOF
# Core Framework
fastapi==0.104.0
uvicorn[standard]==0.24.0
pydantic==2.0.0
pydantic-settings==2.0.0

# AI/ML Stack (MANDATORY)
langchain==0.1.0
llama-index==0.9.0
chromadb==0.4.0

# Web Scraping
playwright==1.40.0
beautifulsoup4==4.12.0
selenium==4.15.0
google-search-results==2.4.2  # SerpAPI

# Maps & Location
folium==0.15.0
geopy==2.4.0
mapbox==0.18.1

# Database & Storage
firebase-admin==6.0.0

# Utilities
python-dotenv==1.0.0
requests==2.31.0
aiohttp==3.9.0
loguru==0.7.0
pandas==2.0.0
numpy==1.24.0

# Testing
pytest==7.4.0
pytest-asyncio==0.21.0
httpx==0.25.0
EOF

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
Create basic FastAPI app:
python# backend/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn

app = FastAPI(
    title="Artisan Hub API",
    description="AI-Powered Ecosystem for Local Craftspeople",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class HealthResponse(BaseModel):
    status: str
    message: str
    ollama_connected: bool

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Artisan Hub API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    import requests
    try:
        # Check Ollama connection
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        ollama_ok = response.status_code == 200
    except:
        ollama_ok = False
    
    return HealthResponse(
        status="healthy" if ollama_ok else "degraded",
        message="Ollama connected" if ollama_ok else "Ollama not connected",
        ollama_connected=ollama_ok
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
Test the setup:
bash# Run the server
python main.py

# In another terminal, test endpoints
curl http://localhost:8000/
curl http://localhost:8000/health
Expected Output:
json{
  "status": "healthy",
  "message": "Ollama connected",
  "ollama_connected": true
}
Step 1.3: Implement Ollama Client (DAY 2)
Create Ollama interface:
python# backend/core/ollama_client.py
from typing import Dict, List, Optional, AsyncIterator
import aiohttp
import asyncio
from loguru import logger

class OllamaClient:
    """
    Client for interacting with Ollama API
    MANDATORY: Only use Gemma 3 models
    """
    
    REASONING_MODEL = "gemma3:4b"  # For complex analysis
    FAST_MODEL = "gemma3:1b"       # For quick responses
    EMBED_MODEL = "gemma3:embed"    # For embeddings
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def generate(
        self,
        prompt: str,
        model: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        stream: bool = False
    ) -> str:
        """
        Generate completion from Ollama
        
        Args:
            prompt: User prompt
            model: Model to use (must be 4b or 1b)
            system: System prompt
            temperature: Sampling temperature
            stream: Whether to stream response
        
        Returns:
            Generated text
        """
        if model not in [self.REASONING_MODEL, self.FAST_MODEL]:
            raise ValueError(
                f"Invalid model '{model}'. "
                f"Must use {self.REASONING_MODEL} or {self.FAST_MODEL}"
            )
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": temperature
            }
        }
        
        if system:
            payload["system"] = system
        
        logger.info(f"Generating with {model}: {prompt[:100]}...")
        
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        async with self.session.post(
            f"{self.base_url}/api/generate",
            json=payload
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Ollama error: {error_text}")
            
            result = await response.json()
            generated_text = result.get("response", "")
            
            logger.success(f"Generated {len(generated_text)} chars with {model}")
            return generated_text
    
    async def embed(self, text: str) -> List[float]:
        """
        Generate embeddings using Gemma 3 Embed
        
        Args:
            text: Text to embed
        
        Returns:
            Embedding vector
        """
        payload = {
            "model": self.EMBED_MODEL,
            "prompt": text
        }
        
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        async with self.session.post(
            f"{self.base_url}/api/embeddings",
            json=payload
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Embedding error: {error_text}")
            
            result = await response.json()
            embedding = result.get("embedding", [])
            
            logger.debug(f"Generated embedding (dim={len(embedding)})")
            return embedding
    
    async def reasoning_task(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7
    ) -> str:
        """
        Use 4B model for complex reasoning tasks
        """
        return await self.generate(
            prompt=prompt,
            model=self.REASONING_MODEL,
            system=system,
            temperature=temperature
        )
    
    async def fast_task(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.3
    ) -> str:
        """
        Use 1B model for fast, simple tasks
        """
        return await self.generate(
            prompt=prompt,
            model=self.FAST_MODEL,
            system=system,
            temperature=temperature
        )


# Test the client
async def test_ollama_client():
    async with OllamaClient() as client:
        # Test reasoning model
        print("Testing 4B reasoning model...")
        result = await client.reasoning_task(
            "Analyze this craft: I make blue pottery. What tools do I need?"
        )
        print(f"4B Result: {result[:200]}\n")
        
        # Test fast model
        print("Testing 1B fast model...")
        result = await client.fast_task(
            "Classify this as pottery, weaving, or metalwork: blue pottery"
        )
        print(f"1B Result: {result[:200]}\n")
        
        # Test embeddings
        print("Testing embeddings...")
        embedding = await client.embed("blue pottery artisan from jaipur")
        print(f"Embedding dimension: {len(embedding)}")
        print(f"First 5 values: {embedding[:5]}\n")

if __name__ == "__main__":
    asyncio.run(test_ollama_client())
Run test:
bashpython backend/core/ollama_client.py
Expected Output:
Testing 4B reasoning model...
4B Result: For blue pottery, you'll need: 1. Potter's wheel...

Testing 1B fast model...
1B Result: pottery

Embedding dimension: 768
First 5 values: [0.123, -0.456, 0.789, ...]
Step 1.4: Implement ChromaDB Vector Store (DAY 2-3)
Create vector store wrapper:
python# backend/core/vector_store.py
from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings
from loguru import logger
from .ollama_client import OllamaClient

class ArtisanVectorStore:
    """
    ChromaDB vector store for Artisan Hub
    Collections:
    - craft_knowledge: Technical details about crafts
    - supplier_data: Verified supplier information
    - market_insights: Pricing and demand data
    - user_context: Personal artisan profiles
    """
    
    def __init__(self, persist_directory: str = "./data/chroma_db"):
        self.client = chromadb.Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=persist_directory
        ))
        self.ollama_client = OllamaClient()
        
        # Initialize collections
        self.collections = {
            "craft_knowledge": self._get_or_create_collection("craft_knowledge"),
            "supplier_data": self._get_or_create_collection("supplier_data"),
            "market_insights": self._get_or_create_collection("market_insights"),
            "user_context": self._get_or_create_collection("user_context")
        }
        
        logger.info("Initialized ChromaDB with 4 collections")
    
    def _get_or_create_collection(self, name: str):
        """Get or create a collection"""
        try:
            return self.client.get_collection(name)
        except:
            return self.client.create_collection(name)
    
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
        n_results: int = 5,
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
        if collection_name not in self.collections:
            raise ValueError(f"Invalid collection: {collection_name}")
        
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
Test the vector store:
bashpython backend/core/vector_store.py
Step 1.5: Create Conversational Interface (DAY 3)
Basic chat endpoint:
python# backend/api/routes/chat.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from core.ollama_client import OllamaClient
from loguru import logger

router = APIRouter(prefix="/chat", tags=["chat"])

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[ChatMessage]] = []
    user_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    model_used: str
    processing_time: float

@router.post("/send", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """
    Send a message to the AI assistant
    """
    import time
    start_time = time.time()
    
    try:
        # Build conversation context
        context = ""
        for msg in request.conversation_history[-5:]:  # Last 5 messages
            context += f"{msg.role}: {msg.content}\n"
        
        context += f"user: {request.message}\n"
        
        # Use fast model for simple queries, reasoning model for complex ones
        async with OllamaClient() as client:
            # Simple classification to route to correct model
            classification_prompt = f"Classify this query as 'simple' or 'complex': {request.message}"
            classification = await client.fast_task(classification_prompt)
            
            is_complex = "complex" in classification.lower()
            
            # Generate response
            system_prompt = """You are a helpful AI assistant for artisans and craftspeople.
Your role is to understand their craft, help them find suppliers, identify growth opportunities,
and connect them with relevant events. Be concise, helpful, and empathetic."""
            
            if is_complex:
                response = await client.reasoning_task(
                    prompt=context,
                    system=system_prompt
                )
                model_used = "gemma3:4b"
            else:
                response = await client.fast_task(
                    prompt=context,
                    system=system_prompt
                )
                model_used = "gemma3:1b"
        
        processing_time = time.time() - start_time
        
        logger.info(f"Chat response generated in {processing_time:.2f}s using {model_used}")
        
        return ChatResponse(
            response=response,
            model_used=model_used,
            processing_time=processing_time
        )
    
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Update main.py to include this router
Update main.py to include chat routes:
python# Add to main.py
from api.routes import chat

app.include_router(chat.router)
Test chat endpoint:
bashcurl -X POST "http://localhost:8000/chat/send" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, I am a potter from Jaipur",
    "conversation_history": []
  }'

Phase 2: Agent Development (Week 2-3)
Step 2.1: Base Agent Class (DAY 4)
python# backend/agents/base_agent.py
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from core.ollama_client import OllamaClient
from core.vector_store import ArtisanVectorStore
from loguru import logger

class BaseAgent(ABC):
    """
    Abstract base class for all agents
    All agents must implement: analyze() method
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        ollama_client: OllamaClient,
        vector_store: ArtisanVectorStore
    ):
        self.name = name
        self.description = description
        self.ollama = ollama_client
        self.vector_store = vector_store
        self.execution_logs: List[Dict] = []
        
        logger.info(f"Initialized {self.name} agent")
    
    @abstractmethod
    async def analyze(self, user_profile: Dict) -> Dict:
        """
        Main analysis method - must be implemented by each agent
        
        Args:
            user_profile: User profile dictionary containing:
                - craft_type: Type of craft
                - location: User location
                - story: User's story
                - context: Additional context
        
        Returns:
            Dictionary containing agent's analysis and recommendations
        """
        pass
    
    def log_execution(self, step: str, data: Dict):
        """Log execution step for audit trail"""
        log_entry = {
            "agent": self.name,
            "step": step,
            "data": data,
            "timestamp": self._get_timestamp()
        }
        self.execution_logs.append(log_entry)
        logger.debug(f"[{self.name}] {step}: {data}")
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_logs(self) -> List[Dict]:
        """Get execution logs"""
        return self.execution_logs
    
    def clear_logs(self):
        """Clear execution logs"""
        self.execution_logs = []
Step 2.2: Profile Analyst Agent (DAY 4-5)
This agent is CRITICAL - it's the first point of contact
python# backend/agents/profile_analyst.py
from typing import Dict, List, Optional
from .base_agent import BaseAgent
from loguru import logger
import json

class ProfileAnalystAgent(BaseAgent):
    """
    Profile Analyst Agent
    
    Responsibilities:
    1. Parse unstructured user input (organic conversation)
    2. Identify craft type and specialization
    3. Infer tool requirements
    4. Determine workspace needs
    5. Extract location from context
    6. Identify supply categories
    7. Understand skill adjacencies
    8. Assess market positioning
    
    Uses: Gemma 3 4B (reasoning model) for deep understanding
    """
    
    def __init__(self, ollama_client, vector_store):
        super().__init__(
            name="Profile Analyst",
            description="Infers artisan needs from organic conversation",
            ollama_client=ollama_client,
            vector_store=vector_store
        )
    
    async def analyze(self, user_profile: Dict) -> Dict:
        """
        Analyze user profile and infer needs
        
        Input format:
        {
            "input_text": "I'm Raj, I make traditional blue pottery...",
            "raw_conversation": [...] (optional)
        }
        
        Output format:
        {
            "craft_type": "pottery",
            "specialization": "blue pottery",
            "location": {
                "city": "Jaipur",
                "state": "Rajasthan",
                "country": "India"
            },
            "inferred_needs": {
                "tools": ["pottery wheel", "kiln", "glazing tools"],
                "workspace": "kiln required, ventilation needed",
                "supplies": ["clay", "blue pigments", "glazes"],
                "skills": ["wheel throwing", "glazing", "firing"]
            },
            "skill_adjacencies": ["ceramic jewelry", "tile making"],
            "market_position": "traditional craft, premium segment",
            "confidence": 0.85
        }
        """
        self.log_execution("start", {"input": user_profile.get("input_text", "")[:100]})
        
        input_text = user_profile.get("input_text", "")
        
        # Step 1: Extract basic information
        extraction_prompt = f"""Analyze this artisan's introduction and extract structured information.

Input: "{input_text}"

Extract the following in JSON format:
{{
    "name": "artisan's name",
    "craft_type": "type of craft (pottery, weaving, metalwork, etc.)",
    "specialization": "specific style or technique",
    "location": {{"city": "city name", "state": "state", "country": "country"}},
    "experience_years": number or null,
    "learned_from": "how they learned the craft",
    "story_elements": ["key story points"]
}}

Return ONLY valid JSON, no other text."""

        extraction_result = await self.ollama.reasoning_task(extraction_prompt)
        
        self.log_execution("extraction", {"raw_result": extraction_result})
        
        # Parse JSON (handle potential parsing errors)
        try:
            # Clean up the response (remove markdown code blocks if present)
            if "```json" in extraction_result:
                extraction_result = extraction_result.split("```json")[1].split("```")[0]
            elif "```" in extraction_result:
                extraction_result = extraction_result.split("```")[1].split("```")[0]
            
            basic_info = json.loads(extraction_result.strip())
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}\nResponse: {extraction_result}")
            # Fallback to simpler extraction
            basic_info = await self._fallback_extraction(input_text)
        
        self.log_execution("parsed_info", basic_info)
        
        # Step 2: Infer needs based on craft type
        needs_prompt = f"""Based on this craft profile, infer the artisan's needs:

Craft Type: {basic_info.get('craft_type', 'unknown')}
Specialization: {basic_info.get('specialization', 'unknown')}

Provide in JSON format:
{{
    "tools": ["essential tools needed"],
    "workspace_requirements": "description of workspace needs",
    "raw_materials": ["materials needed regularly"],
    "skills_required": ["key skills for this craft"],
    "typical_products": ["products they likely make"],
    "market_segment": "market positioning (premium/mid/budget, traditional/modern)"
}}

Return ONLY valid JSON."""

        needs_result = await self.ollama.reasoning_task(needs_prompt)
        
        try:
            if "```json" in needs_result:
                needs_result = needs_result.split("```json")[1].split("```")[0]
            elif "```" in needs_result:
                needs_result = needs_result.split("```")[1].split("```")[0]
            needs_info = json.loads(needs_result.strip())
        except:
            needs_info = {"error": "Could not parse needs"}
        
        self.log_execution("inferred_needs", needs_info)
        
        # Step 3: Identify skill adjacencies (what else could they make/sell)
        adjacency_prompt = f"""Given this craft: {basic_info.get('craft_type')} ({basic_info.get('specialization')})

What are 3-5 adjacent products or markets they could explore? Consider:
- Related crafts using similar skills
- Modern adaptations of traditional items
- Complementary products
- Higher-margin applications

Return as JSON array: ["adjacency 1", "adjacency 2", ...]"""

        adjacency_result = await self.ollama.reasoning_task(adjacency_prompt)
        
        try:
            if "```json" in adjacency_result:
                adjacency_result = adjacency_result.split("```json")[1].split("```")[0]
            elif "```" in adjacency_result:
                adjacency_result = adjacency_result.split("```")[1].split("```")[0]
            adjacencies = json.loads(adjacency_result.strip())
        except:
            adjacencies = []
        
        self.log_execution("adjacencies", adjacencies)
        
        # Step 4: Store in vector database for future retrieval
        profile_document = f"""
        Artisan: {basic_info.get('name', 'Unknown')}
        Craft: {basic_info.get('craft_type')} - {basic_info.get('specialization')}
        Location: {basic_info.get('location', {}).get('city', 'Unknown')}
        Tools needed: {', '.join(needs_info.get('tools', []))}
        Materials: {', '.join(needs_info.get('raw_materials', []))}
        """
        
        await self.vector_store.add_document(
            collection_name="user_context",
            document=profile_document,
            metadata={
                "user_id": user_profile.get("user_id", "anonymous"),
                "craft_type": basic_info.get('craft_type', 'unknown'),
                "location": basic_info.get('location', {}).get('city', 'unknown')
            }
        )
        
        # Compile final response
        final_response = {
            "craft_type": basic_info.get('craft_type'),
            "specialization": basic_info.get('specialization'),
            "location": basic_info.get('location'),
            "experience_years": basic_info.get('experience_years'),
            "inferred_needs": {
                "tools": needs_info.get('tools', []),
                "workspace": needs_info.get('workspace_requirements', ''),
                "supplies": needs_info.get('raw_materials', []),
                "skills": needs_info.get('skills_required', [])
            },
            "typical_products": needs_info.get('typical_products', []),
            "skill_adjacencies": adjacencies,
            "market_position": needs_info.get('market_segment', ''),
            "confidence": 0.85,  # TODO: Implement confidence scoring
            "execution_logs": self.get_logs()
        }
        
        self.log_execution("complete", {"status": "success"})
        
        return final_response
    
    async def _fallback_extraction(self, text: str) -> Dict:
        """Fallback extraction if JSON parsing fails"""
        return {
            "name": "Unknown",
            "craft_type": "unknown",
            "specialization": "unknown",
            "location": {"city": "unknown", "state": "unknown", "country": "India"},
            "experience_years": None,
            "learned_from": "unknown",
            "story_elements": []
        }


# Test the Profile Analyst Agent
async def test_profile_analyst():
    from core.ollama_client import OllamaClient
    from core.vector_store import ArtisanVectorStore
    
    ollama = OllamaClient()
    vector_store = ArtisanVectorStore("./data/test_chroma")
    
    agent = ProfileAnalystAgent(ollama, vector_store)
    
    # Test input
    test_input = {
        "input_text": "I'm Raj, I make traditional blue pottery in Jaipur. Been doing this for 10 years, learned from my father. We specialize in decorative plates and vases with intricate floral patterns.",
        "user_id": "test_user_001"
    }
    
    print("Analyzing profile...")
    result = await agent.analyze(test_input)
    
    print("\n=== ANALYSIS RESULT ===")
    print(json.dumps(result, indent=2))
    
    print("\n=== EXECUTION LOGS ===")
    for log in result['execution_logs']:
        print(f"[{log['timestamp']}] {log['step']}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_profile_analyst())
Run test:
bashpython backend/agents/profile_analyst.py
Expected Output:
json{
  "craft_type": "pottery",
  "specialization": "blue pottery",
  "location": {
    "city": "Jaipur",
    "state": "Rajasthan",
    "country": "India"
  },
  "experience_years": 10,
  "inferred_needs": {
    "tools": ["pottery wheel", "kiln", "glazing brushes", "carving tools"],
    "workspace": "Requires high-temperature kiln, proper ventilation",
    "supplies": ["clay", "blue cobalt oxide", "glazes", "water"],
    "skills": ["wheel throwing", "hand painting", "glaze application", "kiln firing"]
  },
  "typical_products": ["decorative plates", "vases", "bowls", "tiles"],
  "skill_adjacencies": [
    "ceramic jewelry",
    "pottery workshops/classes",
    "custom commissioned pieces",
    "modern minimalist pottery",
    "pottery kits for beginners"
  ],
  "market_position": "premium, traditional craft",
  "confidence": 0.85
}
Step 2.3: Supply Hunter Agent (DAY 5-7)
This is the most complex agent - handles web scraping and verification
python# backend/agents/supply_hunter.py
from typing import Dict, List, Optional
from .base_agent import BaseAgent
from loguru import logger
import json

class SupplyHunterAgent(BaseAgent):
    """
    Supply Hunter Agent
    
    Responsibilities:
    1. Search for suppliers based on inferred needs
    2. Scrape supplier websites for details
    3. Extract pricing information
    4. Analyze reviews and ratings
    5. Verify legitimacy through cross-referencing
    6. Calculate logistics (distance, delivery time)
    7. Maintain detailed search logs
    
    Search Priority:
    1. India (mandatory first)
    2. Regional (Asia) if needed
    3. Global only if unavailable in India/Asia
    
    Uses: Gemma 3 4B for analysis, 1B for classification
    """
    
    def __init__(self, ollama_client, vector_store, scraper_service):
        super().__init__(
            name="Supply Hunter",
            description="Finds and verifies suppliers for artisan materials",
            ollama_client=ollama_client,
            vector_store=vector_store
        )
        self.scraper = scraper_service
    
    async def analyze(self, user_profile: Dict) -> Dict:
        """
        Find suppliers for the artisan
        
        Input format:
        {
            "craft_type": "pottery",
            "supplies_needed": ["clay", "glazes", "pigments"],
            "location": {"city": "Jaipur", "state": "Rajasthan"},
            "budget_range": "mid" (optional)
        }
        
        Output format:
        {
            "suppliers": [
                {
                    "name": "Supplier name",
                    "products": ["list of products"],
                    "location": {"city": "", "distance_km": 0},
                    "contact": {"phone": "", "email": "", "website": ""},
                    "pricing": {"product": "price range"},
                    "ratings": {"overall": 4.5, "review_count": 120},
                    "verification": {
                        "confidence": 0.85,
                        "sources_checked": 3,
                        "legitimacy_indicators": ["..."],
                        "red_flags": []
                    },
                    "logistics": {
                        "distance_km": 15,
                        "estimated_delivery": "2-3 days",
                        "shipping_available": true
                    }
                }
            ],
            "search_logs": [...],
            "total_suppliers_found": 5,
            "india_suppliers": 4,
            "global_suppliers": 1
        }
        """
        self.log_execution("start", {"supplies_needed": user_profile.get("supplies_needed", [])})
        
        supplies = user_profile.get("supplies_needed", [])
        location = user_profile.get("location", {})
        craft_type = user_profile.get("craft_type", "")
        
        all_suppliers = []
        search_logs = []
        
        # Search for each supply
        for supply in supplies:
            self.log_execution("searching_supply", {"supply": supply})
            
            # Step 1: Search in India first (MANDATORY)
            india_results = await self._search_suppliers_india(
                supply_name=supply,
                craft_type=craft_type,
                location=location
            )
            
            search_logs.extend(india_results["search_logs"])
            
            # Step 2: If insufficient results, search regionally
            if len(india_results["suppliers"]) < 3:
                self.log_execution("expanding_search", {"reason": "insufficient_india_results"})
                regional_results = await self._search_suppliers_regional(
                    supply_name=supply,
                    craft_type=craft_type
                )
                india_results["suppliers"].extend(regional_results["suppliers"])
                search_logs.extend(regional_results["search_logs"])
            
            # Step 3: Verify each supplier
            verified_suppliers = []
            for supplier in india_results["suppliers"][:5]:  # Top 5
                verification = await self._verify_supplier(supplier)
                supplier["verification"] = verification
                
                if verification["confidence"] > 0.6:  # Only include if confidence > 60%
                    verified_suppliers.append(supplier)
            
            all_suppliers.extend(verified_suppliers)
        
        # Count India vs global suppliers
        india_count = sum(1 for s in all_suppliers if s.get("location", {}).get("country") == "India")
        global_count = len(all_suppliers) - india_count
        
        self.log_execution("complete", {
            "total_found": len(all_suppliers),
            "india_suppliers": india_count,
            "global_suppliers": global_count
        })
        
        return {
            "suppliers": all_suppliers,
            "search_logs": search_logs,
            "total_suppliers_found": len(all_suppliers),
            "india_suppliers": india_count,
            "global_suppliers": global_count,
            "execution_logs": self.get_logs()
        }
    
    async def _search_suppliers_india(
        self,
        supply_name: str,
        craft_type: str,
        location: Dict
    ) -> Dict:
        """Search for suppliers in India"""
        
        # Build search query
        city = location.get("city", "")
        state = location.get("state", "")
        
        queries = [
            f"{supply_name} suppliers {city} {state} India",
            f"{craft_type} {supply_name} wholesale {state}",
            f"buy {supply_name} for {craft_type} {city}",
            f"{supply_name} manufacturers India {state}"
        ]
        
        all_results = []
        search_logs = []
        
        for query in queries:
            self.log_execution("web_search", {"query": query, "region": "India"})
            
            # Call scraper service to search
            results = await self.scraper.search(
                query=query,
                region="in",  # India
                num_results=10
            )
            
            search_logs.append({
                "query": query,
                "results_count": len(results),
                "timestamp": self._get_timestamp()
            })
            
            # Parse each result
            for result in results:
                supplier_data = await self._parse_supplier_page(result)
                if supplier_data:
                    all_results.append(supplier_data)
        
        # Deduplicate by name/website
        unique_suppliers = self._deduplicate_suppliers(all_results)
        
        return {
            "suppliers": unique_suppliers,
            "search_logs": search_logs
        }
    
    async def _search_suppliers_regional(self, supply_name: str, craft_type: str) -> Dict:
        """Search for suppliers in Asia (excluding India)"""
        queries = [
            f"{supply_name} suppliers Asia",
            f"{craft_type} {supply_name} wholesale Southeast Asia"
        ]
        
        # Similar implementation to India search but with different region
        # Implementation here...
        
        return {
            "suppliers": [],
            "search_logs": []
        }
    
    async def _parse_supplier_page(self, search_result: Dict) -> Optional[Dict]:
        """
        Parse a supplier page to extract information
        
        Args:
            search_result: {
                "url": "...",
                "title": "...",
                "snippet": "..."
            }
        
        Returns:
            Parsed supplier data or None
        """
        url = search_result.get("url")
        
        self.log_execution("scraping_page", {"url": url})
        
        try:
            # Scrape the page
            page_content = await self.scraper.scrape_page(url)
            
            # Use LLM to extract structured information
            extraction_prompt = f"""Extract supplier information from this webpage content:

URL: {url}
Content: {page_content[:2000]}...

Extract in JSON format:
{{
    "name": "supplier name",
    "products": ["list of products they sell"],
    "location": {{"city": "", "state": "", "country": "India"}},
    "contact": {{
        "phone": "",
        "email": "",
        "website": "{url}"
    }},
    "pricing_info": "any pricing information found",
    "business_type": "manufacturer/wholesaler/retailer"
}}

Return ONLY valid JSON."""

            result = await self.ollama.reasoning_task(extraction_prompt)
            
            # Parse JSON
            try:
                if "```json" in result:
                    result = result.split("```json")[1].split("```")[0]
                supplier_data = json.loads(result.strip())
                
                # Add source URL
                supplier_data["source_url"] = url
                supplier_data["scraped_at"] = self._get_timestamp()
                
                return supplier_data
            except:
                logger.error(f"Failed to parse supplier data from {url}")
                return None
        
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return None
    
    async def _verify_supplier(self, supplier: Dict) -> Dict:
        """
        Verify supplier legitimacy through multiple checks
        
        Returns verification results with confidence score
        """
        self.log_execution("verifying_supplier", {"name": supplier.get("name")})
        
        verification = {
            "confidence": 0.0,
            "sources_checked": 0,
            "legitimacy_indicators": [],
            "red_flags": [],
            "cross_references": []
        }
        
        # Check 1: Search for the supplier name to find other mentions
        supplier_name = supplier.get("name")
        search_query = f'"{supplier_name}" reviews India'
        
        search_results = await self.scraper.search(search_query, region="in", num_results=5)
        verification["sources_checked"] = len(search_results)
        
        # Check 2: Look for reviews
        for result in search_results:
            if "review" in result.get("title", "").lower() or "review" in result.get("snippet", "").lower():
                verification["cross_references"].append(result["url"])
        
        # Check 3: Verify contact information
        if supplier.get("contact", {}).get("phone"):
            verification["legitimacy_indicators"].append("Phone number provided")
        if supplier.get("contact", {}).get("email"):
            verification["legitimacy_indicators"].append("Email provided")
        if supplier.get("contact", {}).get("website"):
            verification["legitimacy_indicators"].append("Website available")
        
        # Check 4: Look for red flags
        red_flag_keywords = ["scam", "fraud", "fake", "complaint", "beware"]
        for result in search_results:
            snippet = result.get("snippet", "").lower()
            for keyword in red_flag_keywords:
                if keyword in snippet:
                    verification["red_flags"].append(f"Found '{keyword}' in search results")
        
        # Calculate confidence score
        confidence = 0.5  # Base confidence
        
        if len(verification["cross_references"]) > 0:
            confidence += 0.2
        if len(verification["legitimacy_indicators"]) >= 2:
            confidence += 0.15
        if len(verification["red_flags"]) == 0:
            confidence += 0.15
        
        # Penalty for red flags
        confidence -= (len(verification["red_flags"]) * 0.15)
        
        verification["confidence"] = max(0.0, min(1.0, confidence))
        
        self.log_execution("verification_complete", {
            "supplier": supplier_name,
            "confidence": verification["confidence"]
        })
        
        return verification
    
    def _deduplicate_suppliers(self, suppliers: List[Dict]) -> List[Dict]:
        """Remove duplicate suppliers based on name or website"""
        seen = set()
        unique = []
        
        for supplier in suppliers:
            name = supplier.get("name", "").lower()
            website = supplier.get("contact", {}).get("website", "").lower()
            
            identifier = f"{name}|{website}"
            
            if identifier not in seen:
                seen.add(identifier)
                unique.append(supplier)
        
        return unique


# Test the Supply Hunter Agent
async def test_supply_hunter():
    from core.ollama_client import OllamaClient
    from core.vector_store import ArtisanVectorStore
    from scraping.web_scraper import WebScraperService  # We'll create this next
    
    ollama = OllamaClient()
    vector_store = ArtisanVectorStore("./data/test_chroma")
    scraper = WebScraperService()
    
    agent = SupplyHunterAgent(ollama, vector_store, scraper)
    
    # Test input
    test_input = {
        "craft_type": "pottery",
        "supplies_needed": ["clay", "pottery glaze"],
        "location": {"city": "Jaipur", "state": "Rajasthan", "country": "India"},
        "user_id": "test_user_001"
    }
    
    print("Searching for suppliers...")
    result = await agent.analyze(test_input)
    
    print("\n=== SUPPLIERS FOUND ===")
    print(f"Total: {result['total_suppliers_found']}")
    print(f"India: {result['india_suppliers']}, Global: {result['global_suppliers']}")
    
    for i, supplier in enumerate(result['suppliers'][:3]):  # Show first 3
        print(f"\n--- Supplier {i+1} ---")
        print(f"Name: {supplier.get('name')}")
        print(f"Location: {supplier.get('location')}")
        print(f"Confidence: {supplier.get('verification', {}).get('confidence', 0):.2f}")
        print(f"Products: {', '.join(supplier.get('products', [])[:3])}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_supply_hunter())
Now we need to implement the Web Scraper Service:
python# backend/scraping/web_scraper.py
from typing import Dict, List, Optional
import aiohttp
import asyncio
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from loguru import logger
import os

class WebScraperService:
    """
    Web scraping service using SerpAPI + Playwright + BeautifulSoup
    
    CRITICAL REQUIREMENTS:
    - MUST use real web search (SerpAPI)
    - MUST scrape actual live data
    - NO synthetic data
    - NO database lookups
    - Full audit logs required
    """
    
    def __init__(self):
        self.serpapi_key = os.getenv("SERPAPI_KEY")
        if not self.serpapi_key:
            logger.warning("SERPAPI_KEY not set - web search will be limited")
        
        self.session: Optional[aiohttp.ClientSession] = None
        self.search_logs: List[Dict] = []
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def search(
        self,
        query: str,
        region: str = "in",
        num_results: int = 10
    ) -> List[Dict]:
        """
        Search web using SerpAPI
        
        Args:
            query: Search query
            region: Region code (in=India, us=USA, etc.)
            num_results: Number of results to return
        
        Returns:
            List of search results
        """
        if not self.serpapi_key:
            logger.error("Cannot search: SERPAPI_KEY not configured")
            return []
        
        logger.info(f"Searching: '{query}' (region={region}, n={num_results})")
        
        # Use SerpAPI
        url = "https://serpapi.com/search"
        params = {
            "q": query,
            "location": self._get_location_string(region),
            "hl": "en",
            "gl": region,
            "api_key": self.serpapi_key,
            "num": num_results
        }
        
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        try:
            async with self.session.get(url, params=params, timeout=30) as response:
                if response.status != 200:
                    logger.error(f"SerpAPI error: {response.status}")
                    return []
                
                data = await response.json()
                
                # Extract organic results
                results = data.get("organic_results", [])
                
                # Format results
                formatted_results = []
                for result in results:
                    formatted_results.append({
                        "title": result.get("title", ""),
                        "url": result.get("link", ""),
                        "snippet": result.get("snippet", ""),
                        "position": result.get("position", 0)
                    })
                
                # Log search
                self.search_logs.append({
                    "query": query,
                    "region": region,
                    "results_count": len(formatted_results),
                    "timestamp": self._get_timestamp()
                })
                
                logger.success(f"Found {len(formatted_results)} results")
                return formatted_results
        
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    
    async def scrape_page(self, url: str, use_playwright: bool = False) -> str:
        """
        Scrape a webpage
        
        Args:
            url: URL to scrape
            use_playwright: Use Playwright for dynamic content (slower but handles JS)
        
        Returns:
            Page text content
        """
        logger.info(f"Scraping: {url} (playwright={use_playwright})")
        
        try:
            if use_playwright:
                return await self._scrape_with_playwright(url)
            else:
                return await self._scrape_with_beautifulsoup(url)
        except Exception as e:
            logger.error(f"Scraping error for {url}: {e}")
            return ""
    
    async def _scrape_with_beautifulsoup(self, url: str) -> str:
        """Scrape using BeautifulSoup (fast, static content)"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        async with self.session.get(url, headers=headers, timeout=15) as response:
            if response.status != 200:
                return ""
            
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text
            text = soup.get_text()
            
            # Clean up
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text[:5000]  # Limit to 5000 chars
    
    async def _scrape_with_playwright(self, url: str) -> str:
        """Scrape using Playwright (slow, handles dynamic content)"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)
                
                # Wait for content to load
                await page.wait_for_timeout(2000)
                
                # Get text content
                text = await page.evaluate("() => document.body.innerText")
                
                await browser.close()
                
                return text[:5000]  # Limit to 5000 chars
            except Exception as e:
                await browser.close()
                raise e
    
    def _get_location_string(self, region_code: str) -> str:
        """Get location string for SerpAPI"""
        locations = {
            "in": "India",
            "us": "United States",
            "uk": "United Kingdom",
            "au": "Australia"
        }
        return locations.get(region_code, "India")
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_search_logs(self) -> List[Dict]:
        """Get all search logs"""
        return self.search_logs


# Test the scraper
async def test_scraper():
    scraper = WebScraperService()
    
    # Test search
    print("Testing web search...")
    results = await scraper.search("pottery clay suppliers Jaipur India", region="in", num_results=3)
    
    for i, result in enumerate(results):
        print(f"\n--- Result {i+1} ---")
        print(f"Title: {result['title']}")
        print(f"URL: {result['url']}")
        print(f"Snippet: {result['snippet'][:100]}...")
    
    # Test scraping (if results found)
    if results:
        print("\n\nTesting page scraping...")
        url = results[0]['url']
        content = await scraper.scrape_page(url)
        print(f"Scraped {len(content)} characters from {url}")
        print(f"First 200 chars: {content[:200]}...")

if __name__ == "__main__":
    import asyncio
    
    # You need to set SERPAPI_KEY environment variable
    # Get free key from: https://serpapi.com/
    
    asyncio.run(test_scraper())
Create .env file:
bash# .env
SERPAPI_KEY=your_serpapi_key_here
Step 2.4: Growth Marketer Agent (DAY 8-9)
This will be continued in the next part due to length...

CRITICAL VERIFICATION CHECKLIST
After implementing each phase, you MUST verify:
Phase 1 Checklist:

 Ollama installed and running (ollama list)
 All 3 Gemma 3 models present (4b, 1b, embed)
 Can generate text with 4b model
 Can generate text with 1b model
 Can generate embeddings
 FastAPI server runs without errors
 Health endpoint returns ollama_connected: true
 ChromaDB creates 4 collections
 Can add documents to ChromaDB
 Can query ChromaDB and get results
 Chat endpoint responds correctly

Phase 2 Checklist:

 Profile Analyst extracts craft type correctly
 Profile Analyst identifies location
 Profile Analyst infers tools needed
 SerpAPI key configured and working
 Web search returns real results
 BeautifulSoup can scrape pages
 Supply Hunter finds suppliers
 Verification pipeline calculates confidence
 All search logs are saved


This implementation guide continues for all agents and phases. Would you like me to continue with:

Growth Marketer Agent details
Event Scout Agent details
Frontend integration
Complete testing procedures

