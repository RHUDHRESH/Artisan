# Render Deployment Guide

## Quick Start

### Deploy to Render

1. **Push changes to GitHub**:
   ```bash
   git add requirements-minimal.txt render.yaml backend/main.py backend/config.py
   git commit -m "Fix: Render deployment with minimal dependencies"
   git push origin main
   ```

2. **In Render Dashboard**:
   - Your service should auto-deploy from the updated `render.yaml`
   - Watch the build logs for:
     ```
     ==> Installing dependencies from requirements-minimal.txt
     ==> Running 'uvicorn backend.main:app --host 0.0.0.0 --port $PORT'
     ```
   - Wait for: `Uvicorn running on http://0.0.0.0:10000`
   - Service should show as "Live" (not "Port scan timeout")

3. **Set environment variables** (if not using render.yaml):
   - `GROQ_API_KEY` - your GROQ API key
   - `TAVILY_API_KEY` - your Tavily API key (if needed)
   - `CORS_ORIGINS` - your Vercel frontend URL
   - `ENABLE_HEAVY_FEATURES` - `false` (for free tier)

### Test Deployment

Once deployed, test your endpoints:

```bash
# Replace with your actual Render URL
$RENDER_URL="https://artisan-backend.onrender.com"

# Test root
curl $RENDER_URL/

# Test health
curl $RENDER_URL/health

# Test minimal chat (if GROQ_API_KEY is set)
curl -X POST $RENDER_URL/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, test"}'
```

**Expected responses:**
- `/` - Returns version and mode info
- `/health` - Returns healthy status with "minimal" mode
- `/api/chat` - Returns AI response using GROQ

### Upgrade to Full Features (Paid Tier)

When you upgrade to a paid Render instance (1GB+ RAM):

1. **In Render Dashboard**:
   - Set `ENABLE_HEAVY_FEATURES` to `true`
   - Change build command to `pip install -r requirements.txt`
   - Trigger manual deploy

2. **The app will then load**:
   - Full monitoring (Prometheus + Structlog)
   - All agent routes (orchestration, maps, search, etc.)
   - WebSocket support
   - Vector databases (ChromaDB)
   - Firebase/Supabase integrations

## Troubleshooting

### "Port scan timeout" still happening

- Check Render logs for the line `Uvicorn running on http://0.0.0.0:10000`
- If you don't see it, there's an import error - check logs above that line
- Common issues:
  - Missing `GROQ_API_KEY` causing import failure
  - Python module not found (missing from requirements-minimal.txt)

### "Import Error" on startup

If you see errors like:
```
ModuleNotFoundError: No module named 'langchain'
```

This means `ENABLE_HEAVY_FEATURES=true` but you're using `requirements-minimal.txt`.

**Fix**: Either:
- Set `ENABLE_HEAVY_FEATURES=false`, OR
- Change build command to `pip install -r requirements.txt` (needs paid tier)

### Memory errors

If logs show OOM (Out of Memory):
```
Process killed (OOM)
```

You're on free tier (512MB) with heavy features enabled.

**Fix**: Set `ENABLE_HEAVY_FEATURES=false` or upgrade to paid tier.

## Files Changed

| File | Change |
|------|--------|
| `render.yaml` | Fixed start command to use uvicorn with `$PORT` |
| `requirements-minimal.txt` | NEW - 10 essential packages only |
| `backend/config.py` | Added `enable_heavy_features` and `port` settings |
| `backend/main.py` | Conditional loading based on feature flag |

## Architecture

```
┌─────────────────────────────────────────┐
│         Render Free Tier (512MB)        │
├─────────────────────────────────────────┤
│  ENABLE_HEAVY_FEATURES=false (default)  │
│                                         │
│  ✓ FastAPI core                         │
│  ✓ Basic health check                   │
│  ✓ Minimal chat (GROQ only)             │
│  ✓ CORS                                 │
│  ✗ Monitoring                           │
│  ✗ Agents/Orchestration                 │
│  ✗ Vector DB                            │
│                                         │
│  Memory: ~150MB                         │
│  Boot time: 3-5 seconds                 │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│      Render Paid Tier (1GB+ RAM)        │
├─────────────────────────────────────────┤
│  ENABLE_HEAVY_FEATURES=true             │
│                                         │
│  ✓ Everything in minimal mode           │
│  ✓ Prometheus metrics                   │
│  ✓ Structured logging                   │
│  ✓ Full agent orchestration             │
│  ✓ LangChain/LangGraph                  │
│  ✓ ChromaDB vector store                │
│  ✓ WebSocket                            │
│  ✓ Firebase/Supabase                    │
│                                         │
│  Memory: 400-800MB                      │
│  Boot time: 15-30 seconds               │
└─────────────────────────────────────────┘
```
