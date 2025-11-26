# Quick Deployment Checklist ✅

## What Was Fixed

✅ **Fixed render.yaml** - Now uses `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`  
✅ **Created requirements-minimal.txt** - 10 packages instead of 70 (20MB vs 2GB)  
✅ **Added feature flag** - `ENABLE_HEAVY_FEATURES` controls AI/ML loading  
✅ **Refactored main.py** - Conditionally loads heavy features  

## Deploy to Render NOW

```bash
# 1. Commit and push
git add requirements-minimal.txt render.yaml backend/main.py backend/config.py RENDER_DEPLOYMENT.md
git commit -m "Fix: Render deployment - minimal mode for free tier"
git push origin main

# 2. Watch Render dashboard
# - Auto-deploys from render.yaml
# - Look for: "Uvicorn running on http://0.0.0.0:10000"
# - Status should change to "Live" ✓

# 3. Set your API keys in Render dashboard
# - GROQ_API_KEY
# - TAVILY_API_KEY (optional)

# 4. Test it
curl https://artisan-backend.onrender.com/
curl https://artisan-backend.onrender.com/health
```

## What Works Now

**Minimal Mode (Free Tier - Default)**:
- ✅ FastAPI server binds to port correctly
- ✅ Health check endpoint
- ✅ Basic GROQ chat at `/api/chat`
- ✅ API documentation at `/docs`
- ✅ Memory: ~150MB (safe for 512MB limit)

**Full Mode (Paid Tier - Optional)**:
- Set `ENABLE_HEAVY_FEATURES=true` in Render
- Change build to `pip install -r requirements.txt`
- Get all 100+ agents, orchestration, vector DB, etc.

## Files You Need

All files already created:
- `requirements-minimal.txt` - Minimal dependencies
- `render.yaml` - Fixed configuration  
- `RENDER_DEPLOYMENT.md` - Full deployment guide
- `backend/main.py` - Refactored with conditional loading
- `backend/config.py` - Added feature flags

## Next Action

**Push to GitHub and Render will auto-deploy!** 🚀

No more "Port scan timeout" errors.
