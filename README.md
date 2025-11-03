# Artisan Hub

A 100% local, privacy-first AI-powered ecosystem that helps artisans discover suppliers, identify growth opportunities, find events, and optimize their craft businesses using multi-agent intelligence.

## 🚀 Quick Start

### Prerequisites

1. **Python 3.9+** installed
2. **Ollama** installed from [ollama.com](https://ollama.com)
3. **SerpAPI Key** - Get a free key from [serpapi.com](https://serpapi.com)

### Step 1: Install Ollama Models

Open a terminal and run:
```bash
ollama pull gemma3:4b
ollama pull gemma3:1b
ollama pull gemma3:embed
```

### Step 2: Configure Environment

Create a `.env` file in the project root:
```env
SERPAPI_KEY=your_serpapi_key_here
```

### Step 3: Run the Application

**Windows:** Simply double-click `start.bat` or run:
```bash
start.bat
```

**Manual Setup (if needed):**
```bash
# Create virtual environment (first time only)
python -m venv .venv

# Activate virtual environment
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Install dependencies (first time only)
pip install -r requirements.txt

# Install Playwright browsers (first time only)
playwright install chromium

# Start backend
cd backend
python main.py

# In another terminal, start frontend
cd frontend
npm install  # First time only
npm run dev
```

### Step 4: Access the Application

- **Backend API:** http://localhost:8000
- **Frontend:** http://localhost:3000
- **API Documentation:** http://localhost:8000/docs

## 📁 Project Structure

```
Artisan/
├── backend/          # FastAPI backend application
│   ├── agents/       # AI agents (profile analyst, supply hunter, etc.)
│   ├── api/          # API routes and WebSocket
│   ├── core/         # Core services (Ollama client, vector store)
│   ├── scraping/     # Web scraping services
│   └── services/     # Additional services (maps, notifications)
├── frontend/         # Next.js frontend application
├── data/             # Data storage (ChromaDB, logs, cache)
├── docs/             # Detailed documentation
├── start.bat         # Windows startup script
└── requirements.txt  # Python dependencies
```

## 🎯 Features

- ✅ **4 AI Agents** working together
- ✅ **Web Scraping** with verification
- ✅ **Vector Database** for knowledge storage
- ✅ **Real-time Updates** via WebSocket
- ✅ **100% Local** - No cloud LLMs
- ✅ **India-First** search approach

## 📚 Documentation

- **Detailed Setup:** See `docs/` folder for comprehensive guides
- **API Reference:** Visit http://localhost:8000/docs when running
- **Agent Documentation:** See `docs/AGENTS.md`

## ⚙️ Configuration

The application uses environment variables for configuration. Create a `.env` file with:

```env
SERPAPI_KEY=your_key_here
OLLAMA_BASE_URL=http://localhost:11434
CHROMA_DB_PATH=./data/chroma_db
LOG_LEVEL=INFO
```

## 🐛 Troubleshooting

**Backend won't start?**
- Ensure Ollama is running: `ollama list`
- Verify all three Gemma models are installed
- Check port 8000 is available

**Frontend won't start?**
- Run `npm install` in the `frontend/` directory
- Ensure backend is running on port 8000
- Check Node.js is installed (v18+)

**No search results?**
- Verify `SERPAPI_KEY` is set in `.env` file
- Check you have API credits remaining on SerpAPI

## 🧪 Testing

Run Ollama setup tests:
```bash
python backend/tests/test_ollama_setup.py
```

## 📝 License

Open Source
