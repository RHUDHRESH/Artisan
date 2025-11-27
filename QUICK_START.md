# Quick Start: Connect Vercel to Render

Your backend is **already live** on Render! Just need to connect it to Vercel.

## TL;DR - Do This Now

### 1. In Render Dashboard

Go to your service → Environment → Add:

```bash
CORS_ORIGINS=https://your-vercel-app.vercel.app
```

Replace `your-vercel-app` with your actual Vercel domain, then click **"Manual Deploy" → "Deploy latest commit"**

### 2. In Vercel Dashboard

Go to Settings → Environment Variables → Add:

```bash
NEXT_PUBLIC_API_URL=https://artisan-rem1.onrender.com
NEXT_PUBLIC_WS_URL=wss://artisan-rem1.onrender.com/ws
```

Then trigger a new deployment (or wait for next deploy).

### 3. Test It

Open browser console on your Vercel site:

```javascript
fetch(process.env.NEXT_PUBLIC_API_URL || "https://artisan-rem1.onrender.com")
  .then(r => r.json())
  .then(console.log)
```

Should see: `{message: "Artisan Hub API", status: "running", ...}`

---

## Detailed Guide

See [VERCEL_SETUP.md](./VERCEL_SETUP.md) for:
- Complete step-by-step instructions
- Debugging common issues
- Testing methods
- Understanding minimal mode vs full features

## Verify Connection

Run the verification script:

```bash
# Install requests if needed
pip install requests

# Update FRONTEND_ORIGIN in the script first, then:
python verify_connection.py
```

---

## Common Issues

### "CORS policy error"
→ Check `CORS_ORIGINS` in Render includes your exact Vercel domain  
→ Redeploy Render after changing

### "Failed to fetch" or timeout
→ Render free tier sleeps after 15min inactivity  
→ First request wakes it up (takes ~30 seconds)  
→ Try again after waiting

### "404 Not Found"
→ Check you're calling the right endpoint (`/api/chat` not `/chat`)  
→ See [VERCEL_SETUP.md](./VERCEL_SETUP.md) for full API structure

---

## What's Available Now

Your backend is in **minimal mode** (optimized for Render free tier):

✅ Working:
- Basic chat: `POST /api/chat`
- Health check: `GET /health`
- API info: `GET /`

❌ Not enabled (need `ENABLE_HEAVY_FEATURES=true`):
- Full agent orchestration
- WebSocket support
- Advanced search features

To enable full features, see [VERCEL_SETUP.md](./VERCEL_SETUP.md) Step 5.

---

## Need Help?

1. Check browser DevTools → Network tab for exact errors
2. Check Render logs for backend errors
3. See [VERCEL_SETUP.md](./VERCEL_SETUP.md) for debugging guide
