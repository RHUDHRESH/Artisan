# 👨‍💻 Developer Guide - Contributing to Artisan Hub

Complete guide for developers wanting to understand, extend, or contribute to Artisan Hub.

---

## 📑 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Project Structure](#project-structure)
3. [Setting Up Dev Environment](#setting-up-dev-environment)
4. [Code Quality Standards](#code-quality-standards)
5. [Backend Development](#backend-development)
6. [Frontend Development](#frontend-development)
7. [Adding New Features](#adding-new-features)
8. [Testing](#testing)
9. [Debugging](#debugging)
10. [Deployment](#deployment)

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                        │
│              React Components + Tailwind CSS                 │
│                  (Port 3000)                                 │
└───────────────────────────┬─────────────────────────────────┘
                            │
                    HTTP/WebSocket
                            │
┌───────────────────────────┴─────────────────────────────────┐
│                    Backend (FastAPI)                         │
│                     (Port 8000)                              │
├──────────────────────────────────────────────────────────────┤
│ API Routes │ Agents │ Services │ Core                        │
└─────────────┬────────────────────┬─────────────────────────┘
              │                    │
         ┌────▼─────┐         ┌────▼─────────┐
         │  Ollama   │         │  ChromaDB    │
         │ (Port     │         │ (Vector      │
         │ 11434)    │         │  Database)   │
         └───────────┘         └──────────────┘
```

### Component Breakdown:

**Frontend:** React + Next.js
- User interface
- Form handling
- Results display
- Real-time updates via WebSocket

**Backend:** FastAPI + Python
- REST API endpoints
- Multi-agent orchestration
- Web scraping
- Vector search
- Business logic

**AI Core:** Ollama
- Local LLM inference
- Embedding generation
- No external AI API calls

**Data Layer:** ChromaDB
- Vector storage
- Semantic search
- Document persistence

---

## 📁 Project Structure

```
Artisan/
├── backend/                          # Python backend (100K+ LOC)
│   ├── agents/                       # AI agents
│   │   ├── base_agent.py             # Abstract base class
│   │   ├── profile_analyst.py        # Profile analysis agent
│   │   ├── supply_hunter.py          # Supplier discovery agent
│   │   ├── growth_marketer.py        # Growth opportunity agent
│   │   ├── event_scout.py            # Event discovery agent
│   │   ├── supervisor.py             # Agent orchestrator
│   │   └── framework/
│   │       ├── tools.py              # Tool registry & implementations
│   │       ├── planner.py            # Mission planning
│   │       ├── executor.py           # Task execution
│   │       ├── guardrails.py         # Constraint enforcement
│   │       ├── router.py             # Task routing
│   │       └── prompts.py            # LLM prompts
│   ├── api/                          # API endpoints
│   │   ├── routes/
│   │   │   ├── agents.py             # Agent endpoints
│   │   │   ├── chat.py               # Chat endpoint
│   │   │   ├── maps.py               # Maps endpoints
│   │   │   └── search.py             # Search endpoint
│   │   └── websocket.py              # WebSocket management
│   ├── core/                         # Core services
│   │   ├── ollama_client.py          # LLM interface
│   │   ├── vector_store.py           # ChromaDB interface
│   │   ├── rag_engine.py             # RAG implementation
│   │   └── dual_model_router.py      # Model selection
│   ├── scraping/                     # Web scraping
│   │   ├── web_scraper.py            # Main scraper
│   │   ├── search_engine.py          # Search API wrapper
│   │   ├── static_scraper.py         # BeautifulSoup scraper
│   │   ├── dynamic_scraper.py        # Playwright scraper
│   │   └── verifier.py               # Data verification
│   ├── services/                     # Business logic
│   │   ├── maps_service.py           # Maps/location service
│   │   ├── firebase_service.py       # Firebase integration
│   │   └── notification_service.py   # Notifications
│   ├── utils/                        # Utilities
│   │   ├── helpers.py                # Helper functions
│   │   ├── validators.py             # Input validation
│   │   └── logger.py                 # Logging setup
│   ├── constants.py                  # Application constants (NEW)
│   ├── config.py                     # Configuration management
│   ├── models.py                     # Pydantic data models
│   ├── main.py                       # FastAPI app entry point
│   ├── tests/                        # Test suite
│   │   ├── test_agents.py
│   │   ├── test_ollama_setup.py
│   │   ├── test_scraping.py
│   │   ├── test_rag.py
│   │   ├── test_examples.py
│   │   └── test_complete_system.py
│   └── requirements.txt              # Python dependencies
│
├── frontend/                         # Next.js frontend
│   ├── app/
│   │   ├── page.tsx                  # Home page
│   │   ├── layout.tsx                # Root layout
│   │   └── globals.css               # Global styles
│   ├── components/
│   │   ├── questionnaire.tsx         # Main form
│   │   ├── production-gate.tsx       # Loading screen
│   │   ├── ai-thinking.tsx           # AI activity display
│   │   └── ui/                       # UI components
│   │       ├── expandable-tabs.tsx
│   │       ├── sidebar.tsx
│   │       └── text-shimmer.tsx
│   ├── lib/
│   │   └── utils.ts                  # Utility functions
│   ├── package.json
│   ├── tsconfig.json
│   ├── next.config.js
│   ├── tailwind.config.js
│   └── postcss.config.js
│
├── data/                             # Runtime data
│   ├── chroma_db/                    # Vector database
│   ├── cache/                        # Scraper cache
│   ├── logs/                         # Application logs
│   └── exports/                      # Data exports
│
├── docs/                             # Documentation
│   ├── AGENTS.md
│   ├── API.md
│   ├── DEPLOYMENT.md
│   └── TESTING.md
│
├── QUICK_START.md                    # Quick setup (NEW)
├── HOW_TO_USE.md                     # User guide (NEW)
├── TROUBLESHOOTING.md                # Troubleshooting (NEW)
├── DEVELOPER_GUIDE.md                # This file (NEW)
├── README.md
└── start.bat                         # Startup script

```

---

## ⚙️ Setting Up Dev Environment

### Prerequisites

```powershell
# Check versions
python --version              # Need 3.9+
node --version               # Need 18+
git --version                # For version control
```

### Full Dev Setup

```powershell
# 1. Clone/navigate to repository
cd "C:\Users\hp\OneDrive\Desktop\Artisan"

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# 3. Install backend dependencies with dev tools
pip install -r requirements.txt
pip install pytest pytest-asyncio black flake8 mypy

# 4. Install Playwright
playwright install chromium

# 5. Install Ollama models
ollama pull gemma3:4b
ollama pull gemma3:1b
ollama pull nomic-embed-text

# 6. Setup frontend
cd frontend
npm install
cd ..

# 7. Done!
```

### VSCode Setup (Recommended)

**Extensions to install:**
```
- Python (Microsoft)
- Pylance
- ESLint
- Prettier
- Tailwind CSS IntelliSense
- REST Client (for API testing)
```

**Settings (.vscode/settings.json):**
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "[python]": {
    "editor.defaultFormatter": "ms-python.python",
    "editor.formatOnSave": true
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": true
  }
}
```

---

## 📋 Code Quality Standards

### Python Code Style

**Follow PEP 8 + Black formatter:**

```powershell
# Format all Python files
black backend/

# Check style
flake8 backend/ --max-line-length=100

# Type checking
mypy backend/
```

### Python Best Practices

```python
# ✅ Good
async def analyze_profile(request: ProfileAnalysisRequest) -> Dict[str, Any]:
    """Analyze artisan profile from questionnaire response.

    Args:
        request: Profile analysis request with validated input

    Returns:
        Dictionary containing analysis results

    Raises:
        ValueError: If input validation fails
    """
    logger.info(f"Analyzing profile for user: {request.user_id}")
    try:
        # Implementation
        pass
    except SpecificException as e:
        logger.error(f"Profile analysis failed: {type(e).__name__}: {e}")
        raise

# ❌ Bad
async def analyze(req):
    # No type hints
    # No docstring
    try:
        pass
    except:  # Bare except
        pass
```

### TypeScript Code Style

**Follow Prettier + ESLint:**

```powershell
# Format
npm run format

# Lint
npm run lint
```

### TypeScript Best Practices

```typescript
// ✅ Good
interface QuestionnaireResponse {
  inputText: string;
  userId?: string;
}

async function analyzeProfile(response: QuestionnaireResponse): Promise<ProfileResult> {
  if (!response.inputText.trim()) {
    throw new Error('Input text cannot be empty');
  }
  // Implementation
}

// ❌ Bad
async function analyze(resp) {  // No types
  // No validation
  // No error handling
}
```

---

## 🔙 Backend Development

### Adding a New API Endpoint

**File: `backend/api/routes/custom.py`**

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator
from loguru import logger
from backend.constants import MIN_QUERY_LENGTH, MAX_QUERY_LENGTH

router = APIRouter(prefix="/custom", tags=["custom"])

class CustomRequest(BaseModel):
    """Request model with validation"""
    query: str = Field(
        ...,
        min_length=MIN_QUERY_LENGTH,
        max_length=MAX_QUERY_LENGTH,
        description="Search query"
    )

    @field_validator('query')
    def validate_query(cls, v):
        if not v.strip():
            raise ValueError('Query cannot be empty')
        return v

@router.post("/analyze")
async def custom_endpoint(request: CustomRequest):
    """
    Analyze custom data.

    Args:
        request: Custom request with validated input

    Returns:
        Analysis results

    Raises:
        HTTPException: If processing fails
    """
    try:
        logger.info(f"Processing custom request: {request.query}")

        # Your business logic here
        result = {"status": "success", "data": []}

        return result
    except Exception as e:
        logger.error(f"Custom endpoint error: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

**Register in `backend/main.py`:**

```python
from backend.api.routes import custom

app.include_router(custom.router)
```

---

### Adding a New Agent

**File: `backend/agents/custom_agent.py`**

```python
from backend.agents.base_agent import BaseAgent
from backend.core.ollama_client import OllamaClient
from backend.core.vector_store import ArtisanVectorStore
from loguru import logger
from typing import Dict, Any

class CustomAgent(BaseAgent):
    """Custom agent for specific analysis"""

    def __init__(self, ollama: OllamaClient, vector_store: ArtisanVectorStore):
        super().__init__()
        self.ollama = ollama
        self.vector_store = vector_store
        self.name = "CustomAgent"

    async def analyze(self, mission: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute custom analysis.

        Args:
            mission: Mission parameters

        Returns:
            Analysis results
        """
        logger.info(f"{self.name}: Starting analysis")

        try:
            # Step 1: Extract information
            query = mission.get("query", "")

            # Step 2: Search vector store
            results = await self.vector_store.query(
                "relevant_collection",
                query,
                n_results=5
            )

            # Step 3: Generate response using LLM
            response = await self.ollama.generate(
                prompt=f"Analyze: {query}",
                model="gemma3:4b"
            )

            # Step 4: Return formatted results
            return {
                "agent": self.name,
                "status": "success",
                "results": response,
                "context": results
            }

        except Exception as e:
            logger.error(f"{self.name}: Error: {type(e).__name__}: {e}")
            return {
                "agent": self.name,
                "status": "error",
                "message": str(e)
            }
```

---

### Using Vector Store

```python
# Add document
doc_id = await vector_store.add_document(
    collection_name="craft_knowledge",
    document="Blue pottery requires special glazes",
    metadata={"craft": "pottery", "verified": True},
    doc_id="doc_1"
)

# Query documents
results = await vector_store.query(
    collection_name="craft_knowledge",
    query_text="pottery glazes",
    n_results=5,
    where={"verified": True}
)

# Process results
for result in results:
    print(f"Document: {result['document']}")
    print(f"Distance: {result['distance']}")
    print(f"Metadata: {result['metadata']}")
```

---

### Calling Ollama LLM

```python
ollama = OllamaClient()

# Generate text (fast model)
response = await ollama.fast_task(
    prompt="What are common pottery techniques?"
)

# Reasoning task (larger model)
response = await ollama.reasoning_task(
    prompt="Analyze market trends in pottery"
)

# Generate embedding
embedding = await ollama.embed("pottery supplies")
```

---

### Web Scraping

```python
from backend.scraping.web_scraper import WebScraperService

async with WebScraperService() as scraper:
    # Search the web
    results = await scraper.search(
        query="pottery clay suppliers India",
        region="in",
        num_results=10
    )

    # Scrape a page
    content = await scraper.scrape_page(
        url="https://example.com",
        use_playwright=False  # Use True for dynamic content
    )
```

---

## 🎨 Frontend Development

### Creating a New Component

**File: `frontend/components/CustomComponent.tsx`**

```typescript
'use client';

import React, { useState, useEffect } from 'react';
import { cn } from '@/lib/utils';

interface CustomComponentProps {
  title: string;
  onSubmit?: (data: any) => void;
  className?: string;
}

export function CustomComponent({
  title,
  onSubmit,
  className
}: CustomComponentProps) {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    // Component initialization
    console.log('CustomComponent mounted');
  }, []);

  const handleAnalyze = async () => {
    try {
      setLoading(true);

      const response = await fetch('http://localhost:8000/api/endpoint', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ /* data */ })
      });

      if (!response.ok) throw new Error('API error');

      const result = await response.json();
      setData(result);
      onSubmit?.(result);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={cn('p-6 bg-white rounded-lg', className)}>
      <h2 className="text-2xl font-bold mb-4">{title}</h2>

      {data && (
        <div className="mt-4 p-4 bg-gray-50 rounded">
          <pre>{JSON.stringify(data, null, 2)}</pre>
        </div>
      )}

      <button
        onClick={handleAnalyze}
        disabled={loading}
        className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
      >
        {loading ? 'Processing...' : 'Analyze'}
      </button>
    </div>
  );
}
```

### API Communication

```typescript
// Fetch with error handling
async function fetchFromAPI<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(
    `http://localhost:8000${endpoint}`,
    {
      headers: { 'Content-Type': 'application/json' },
      ...options
    }
  );

  if (!response.ok) {
    throw new Error(`API Error: ${response.status}`);
  }

  return response.json();
}

// Usage
const results = await fetchFromAPI<AnalysisResults>(
  '/agents/profile/analyze',
  {
    method: 'POST',
    body: JSON.stringify(requestData)
  }
);
```

### WebSocket Communication

```typescript
// Real-time updates
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
  console.log('WebSocket connected');
  ws.send(JSON.stringify({ type: 'subscribe' }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Received:', message);

  if (message.type === 'agent_progress') {
    // Handle progress update
    updateProgress(message.agent, message.step);
  }
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};
```

---

## ✨ Adding New Features

### Feature: Add Product Recommendation Agent

**Step 1: Create Agent** (`backend/agents/product_recommender.py`)

```python
from backend.agents.base_agent import BaseAgent

class ProductRecommenderAgent(BaseAgent):
    """Recommends new products based on market trends"""

    async def analyze(self, mission: Dict[str, Any]) -> Dict[str, Any]:
        # Implementation
        pass
```

**Step 2: Add API Endpoint** (`backend/api/routes/agents.py`)

```python
class ProductRecommendationRequest(BaseModel):
    craft_type: str
    current_products: List[str]
    market_region: str

@router.post("/products/recommend")
async def recommend_products(request: ProductRecommendationRequest):
    # Implementation
    pass
```

**Step 3: Add UI Component** (`frontend/components/ProductRecommender.tsx`)

```typescript
export function ProductRecommender() {
  const [recommendations, setRecommendations] = useState([]);

  const handleRecommend = async () => {
    // Fetch recommendations
  };

  return (
    <div>
      {/* UI implementation */}
    </div>
  );
}
```

**Step 4: Integrate with Supervisor** (`backend/agents/supervisor.py`)

```python
# Add to supervisor's available agents
self.agents['product_recommender'] = ProductRecommenderAgent(...)
```

---

## 🧪 Testing

### Running Tests

```powershell
# All tests
pytest backend/tests/ -v

# Specific test file
pytest backend/tests/test_agents.py -v

# With coverage
pytest backend/tests/ --cov=backend

# Async tests
pytest backend/tests/ -v -s --asyncio-mode=auto
```

### Writing Tests

**File: `backend/tests/test_custom.py`**

```python
import pytest
from backend.agents.custom_agent import CustomAgent
from backend.core.ollama_client import OllamaClient
from backend.core.vector_store import ArtisanVectorStore

@pytest.fixture
async def custom_agent():
    """Fixture for custom agent"""
    ollama = OllamaClient()
    vector_store = ArtisanVectorStore()
    return CustomAgent(ollama, vector_store)

@pytest.mark.asyncio
async def test_custom_agent_analyze(custom_agent):
    """Test custom agent analysis"""
    mission = {"query": "test"}

    result = await custom_agent.analyze(mission)

    assert result["status"] == "success"
    assert "results" in result

@pytest.mark.asyncio
async def test_custom_agent_error_handling(custom_agent):
    """Test error handling"""
    mission = {}  # Invalid mission

    result = await custom_agent.analyze(mission)

    assert result["status"] == "error"
```

---

## 🐛 Debugging

### Backend Debugging

**Using print debugging:**
```python
from loguru import logger

logger.debug("Debug info: {}", variable)
logger.info("Info: {}", variable)
logger.warning("Warning: {}", variable)
logger.error("Error: {}", variable)
```

**VSCode Debugger:**

Create `.vscode/launch.json`:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["backend.main:app", "--port", "8000"],
      "jinja": true,
      "justMyCode": true
    }
  ]
}
```

### Frontend Debugging

**Browser DevTools:**
```
F12 → Console/Network/Application tabs
Inspect → Elements
Network tab → Monitor API calls
```

**VSCode Debugger:**

Install "Debugger for Chrome" extension, then:
```json
{
  "name": "Next.js debug",
  "type": "chrome",
  "request": "attach",
  "port": 9222
}
```

---

## 📦 Deployment

### Production Build

**Backend:**
```powershell
# Build
pip install gunicorn
pip install -r requirements.txt

# Run with Gunicorn (production server)
gunicorn -w 4 -b 0.0.0.0:8000 backend.main:app
```

**Frontend:**
```powershell
cd frontend
npm run build
npm start
```

### Docker Deployment

**`Dockerfile` (Backend):**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY backend/ backend/
COPY backend/constants.py .

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**`docker-compose.yml`:**

```yaml
version: '3.8'
services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
    depends_on:
      - ollama

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama

  chromadb:
    image: chromadb/chroma:latest
    ports:
      - "8001:8000"

volumes:
  ollama_data:
```

---

## 🔄 Git Workflow

### Branch Strategy

```powershell
# Create feature branch
git checkout -b feature/my-feature

# Make changes
# Commit regularly
git add .
git commit -m "Add feature description"

# Push to remote
git push origin feature/my-feature

# Create pull request
```

### Commit Message Format

```
feat: Add new product recommendation agent
fix: Correct error handling in WebSocket
docs: Update developer guide
test: Add tests for custom agent
refactor: Improve vector store interface
chore: Update dependencies
```

---

## 📚 Learning Resources

### For Agents & LLMs:
- LangChain docs: https://docs.langchain.com/
- LlamaIndex docs: https://docs.llamaindex.ai/
- Ollama docs: https://github.com/ollama/ollama

### For FastAPI:
- FastAPI tutorial: https://fastapi.tiangolo.com/
- Pydantic validation: https://docs.pydantic.dev/

### For React/Next.js:
- Next.js docs: https://nextjs.org/docs
- React docs: https://react.dev/
- Tailwind CSS: https://tailwindcss.com/docs

### For Python:
- PEP 8 style guide: https://www.python.org/dev/peps/pep-0008/
- Type hints: https://docs.python.org/3/library/typing.html
- Async patterns: https://docs.python.org/3/library/asyncio.html

---

## 📋 Development Checklist

Before committing code:

- [ ] Code follows style guide (black, prettier)
- [ ] Type hints added (Python & TypeScript)
- [ ] Docstrings/comments added
- [ ] Tests written and passing
- [ ] No console errors/warnings
- [ ] Secrets not committed
- [ ] Variable names are descriptive
- [ ] Error handling in place
- [ ] Logging added where appropriate
- [ ] No hardcoded values (use constants)
- [ ] API calls have timeout handling
- [ ] Async operations properly awaited

---

## 🚀 Quick Commands

```powershell
# Start development
.venv\Scripts\activate
uvicorn backend.main:app --reload  # Terminal 1

npm run dev  # Terminal 2 (in frontend/)

# Run tests
pytest backend/tests/ -v

# Format code
black backend/
npm run format

# Lint
flake8 backend/
npm run lint

# Type check
mypy backend/

# Check dependencies
pip list
npm list
```

---

## 📞 Getting Help

**Questions/Issues:**
1. Check existing code examples
2. Review docstrings and comments
3. Check tests for usage patterns
4. Review FastAPI/React docs
5. Ask in GitHub issues

---

**Happy coding!** 🚀

Last Updated: November 2025
