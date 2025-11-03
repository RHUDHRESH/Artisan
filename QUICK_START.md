# Artisan Hub - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Install Ollama Models
```bash
ollama pull gemma3:4b
ollama pull gemma3:1b
ollama pull gemma3:embed
```

### Step 2: Setup Python Environment
```bash
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
playwright install chromium
```

### Step 3: Configure Environment
Create `.env` file:
```env
SERPAPI_KEY=your_serpapi_key_here
```

Get free key from: https://serpapi.com/

### Step 4: Start Backend
```bash
cd backend
python main.py
```

Backend will run at: http://localhost:8000

### Step 5: Open Frontend
Open `frontend/index.html` in your browser, or:
```bash
cd frontend
python -m http.server 3000
```
Then visit: http://localhost:3000

## 📝 Test It Out

1. **Open the frontend** in your browser
2. **Type your introduction**, for example:
   ```
   I'm Raj, I make traditional blue pottery in Jaipur. 
   Been doing this for 10 years. We specialize in decorative plates and vases.
   ```
3. **Watch the magic happen!** The system will automatically:
   - ✅ Analyze your profile
   - ✅ Find suppliers
   - ✅ Identify growth opportunities
   - ✅ Discover relevant events

## 🔍 Verify Setup

Test Ollama:
```bash
python backend/tests/test_ollama_setup.py
```

Test Backend:
- Visit: http://localhost:8000/health
- Should show: `{"status": "healthy", "ollama_connected": true}`

## 📚 API Documentation

Interactive API docs: http://localhost:8000/docs

All endpoints:
- `POST /chat/send` - Chat with AI
- `POST /agents/profile/analyze` - Profile analysis
- `POST /agents/supply/search` - Find suppliers
- `POST /agents/growth/analyze` - Growth opportunities
- `POST /agents/events/search` - Find events

## 🎯 What You Have

✅ **4 AI Agents** working together
✅ **Web Scraping** with verification
✅ **Vector Database** for knowledge storage
✅ **Beautiful Frontend** interface
✅ **Complete API** with all endpoints
✅ **100% Local** - No cloud LLMs
✅ **India-First** search approach

## 🐛 Troubleshooting

**Backend won't start?**
- Check if Ollama is running: `ollama list`
- Verify models are installed
- Check port 8000 is available

**No search results?**
- Verify SERPAPI_KEY in .env
- Check you have API credits remaining

**Frontend can't connect?**
- Make sure backend is running on port 8000
- Check browser console for errors
- Verify CORS is enabled (it should be)

## 📖 Next Steps

- Customize the frontend styling
- Add more craft types
- Extend agent capabilities
- Add user authentication (optional)
- Deploy to production

Enjoy building with Artisan Hub! 🎨

