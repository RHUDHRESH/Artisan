# Artisan Hub

A 100% local, privacy-first AI-powered ecosystem that helps artisans discover suppliers, identify growth opportunities, find events, and optimize their craft businesses using multi-agent intelligence.

## Core Principles

- ✅ **ALL processing is local** - No cloud LLM APIs
- ✅ **Open source only** - Every dependency is free and open source
- ✅ **Real data only** - No synthetic data, everything from live web scraping
- ✅ **Verification required** - Every piece of scraped data is verified with confidence scores
- ✅ **Audit trails mandatory** - Complete logs of all searches, sources, and verification steps

## Critical Requirements

- **Use Gemma 3 models ONLY** (no Llama, no GPT, no other models)
- All embeddings use Gemma 3 Embed
- Dual-model system: 4B for reasoning, 1B for fast responses
- India-first approach for all searches (expand globally only if needed)
- Web-based interface
- Must run entirely on user's PC

## Prerequisites

1. **Ollama installed and running**
   ```bash
   # Install Ollama from https://ollama.com
   # Then pull required models:
   ollama pull gemma3:4b
   ollama pull gemma3:1b
   ollama pull gemma3:embed
   ```

2. **Python 3.9+**
3. **SerpAPI Key** (for web search) - Get free key from https://serpapi.com/

## Installation

1. Clone the repository
2. Create virtual environment:
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Linux/Mac:
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install Playwright browsers:
   ```bash
   playwright install chromium
   ```

5. Copy `.env.example` to `.env` and configure:
   ```bash
   cp .env.example .env
   # Edit .env and add your SERPAPI_KEY
   ```

## Running the Application

Start the FastAPI server:
```bash
cd backend
python main.py
```

The API will be available at `http://localhost:8000`

API Documentation: `http://localhost:8000/docs`

## Testing

Run Ollama setup tests:
```bash
python backend/tests/test_ollama_setup.py
```

## Project Structure

```
artisan-hub/
├── backend/          # FastAPI backend
├── frontend/         # Web interface
├── data/             # ChromaDB, logs, cache
└── docs/             # Documentation
```

## License

Open Source

