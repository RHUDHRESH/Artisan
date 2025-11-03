# Artisan Hub - Setup Instructions

## Quick Start Guide

### Step 1: Install Ollama and Models

1. **Install Ollama** (if not already installed):
   - Visit: https://ollama.com
   - Download and install for your OS
   - Or use: `curl -fsSL https://ollama.com/install.sh | sh` (Linux/Mac)

2. **Pull Required Models** (MANDATORY):
   ```bash
   ollama pull gemma3:4b
   ollama pull gemma3:1b
   ollama pull gemma3:embed
   ```

3. **Verify Installation**:
   ```bash
   ollama list | grep gemma3
   # Should show all three models
   ```

### Step 2: Install Python Dependencies

1. **Create Virtual Environment**:
   ```bash
   python -m venv venv
   
   # Windows:
   venv\Scripts\activate
   
   # Linux/Mac:
   source venv/bin/activate
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Playwright Browsers**:
   ```bash
   playwright install chromium
   ```

### Step 3: Configure Environment

1. **Get SerpAPI Key**:
   - Visit: https://serpapi.com/
   - Sign up for free account
   - Get your API key

2. **Create .env file**:
   ```bash
   # Copy the example (if it exists) or create new:
   # Windows:
   copy .env.example .env
   
   # Linux/Mac:
   cp .env.example .env
   ```

3. **Edit .env file**:
   ```env
   SERPAPI_KEY=your_serpapi_key_here
   OLLAMA_BASE_URL=http://localhost:11434
   CHROMA_DB_PATH=./data/chroma_db
   LOG_LEVEL=INFO
   ```

### Step 4: Verify Setup

1. **Test Ollama Setup**:
   ```bash
   python backend/tests/test_ollama_setup.py
   ```
   Should output:
   ```
   ✓ All required models installed
   ✓ 4B model working
   ✓ 1B model working
   ✓ Embedding model working
   ✓✓✓ All Ollama tests passed ✓✓✓
   ```

2. **Start the Server**:
   ```bash
   cd backend
   python main.py
   ```

3. **Test API**:
   - Open browser: http://localhost:8000/docs
   - Or test health endpoint: http://localhost:8000/health

## API Endpoints

### Health Check
- `GET /health` - Check if Ollama is connected

### Chat
- `POST /chat/send` - Send message to AI assistant

### Agents
- `POST /agents/profile/analyze` - Analyze artisan profile
- `POST /agents/supply/search` - Search for suppliers

## Testing Individual Components

### Test Ollama Client:
```bash
python backend/core/ollama_client.py
```

### Test Vector Store:
```bash
python backend/core/vector_store.py
```

### Test Profile Analyst:
```bash
python backend/agents/profile_analyst.py
```

### Test Supply Hunter:
```bash
python backend/agents/supply_hunter.py
```

### Test Web Scraper:
```bash
python backend/scraping/web_scraper.py
```

## Troubleshooting

### Ollama not found
- Make sure Ollama is running: `ollama serve`
- Check if models are installed: `ollama list`

### Import errors
- Make sure virtual environment is activated
- Run: `pip install -r requirements.txt`

### SerpAPI errors
- Verify SERPAPI_KEY in .env file
- Check if you have remaining API credits

### ChromaDB errors
- Make sure `data/chroma_db` directory exists
- Check write permissions

## Next Steps

Once setup is complete, you can:
1. Start building the frontend interface
2. Add more agents (Growth Marketer, Event Scout)
3. Implement advanced features
4. Add Firebase integration (optional)

