# Vercel → Render Connection Setup

## Problem Summary
Your Render backend is **UP and RUNNING** ✅  
But Vercel frontend can't reach it due to missing environment variables and CORS configuration.

---

## Step 1: Configure Render Environment Variables

In your Render dashboard, set these environment variables:

### Required for Frontend Access
```bash
CORS_ORIGINS=https://your-vercel-app.vercel.app,https://www.your-custom-domain.com
```

**Replace** `your-vercel-app.vercel.app` with your actual Vercel deployment URL.

You can find your Vercel URL in:
- Vercel Dashboard → Your Project → Domains

### Example
If your Vercel app is at `artisan-hub.vercel.app`:
```bash
CORS_ORIGINS=https://artisan-hub.vercel.app,https://artisan-hub-git-main.vercel.app,https://artisan-hub-*.vercel.app
```

### During Development (Optional)
To allow localhost testing during development:
```bash
CORS_ORIGINS=http://localhost:3000,https://artisan-hub.vercel.app
```

Or simply use wildcard (⚠️ NOT recommended for production):
```bash
CORS_ORIGINS=*
```

**After setting this**, redeploy your Render service.

---

## Step 2: Configure Vercel Environment Variables

In Vercel Dashboard → Your Project → Settings → Environment Variables, add:

### Production Environment
```bash
NEXT_PUBLIC_API_URL=https://artisan-rem1.onrender.com
NEXT_PUBLIC_WS_URL=wss://artisan-rem1.onrender.com/ws
```

### Preview & Development (Optional)
You can set different values for preview/development environments if needed.

**After setting these**, redeploy your Vercel app or trigger a new deployment.

---

## Step 3: Verify the Connection

### 3.1 Test Backend Directly
Open in browser:
```
https://artisan-rem1.onrender.com
```

Expected response:
```json
{
  "message": "Artisan Hub API",
  "version": "1.0.0",
  "status": "running",
  "mode": "minimal",
  "features_enabled": false
}
```

### 3.2 Test API Endpoint
```
https://artisan-rem1.onrender.com/api/chat
```

Expected: 405 Method Not Allowed (because it needs POST, not GET - this is correct!)

### 3.3 Test from Browser Console
Open your Vercel deployment → DevTools → Console, run:

```javascript
fetch("https://artisan-rem1.onrender.com", {
  method: "GET"
})
  .then(r => r.json())
  .then(console.log)
  .catch(console.error);
```

**If you see CORS error** → Double check Step 1 and redeploy Render.  
**If it works** → Connection is good!

### 3.4 Test POST to Chat Endpoint
```javascript
fetch("https://artisan-rem1.onrender.com/api/chat", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ message: "Hello!" })
})
  .then(r => r.json())
  .then(console.log)
  .catch(console.error);
```

---

## Step 4: Debugging Issues

### Issue: CORS Error in Browser Console

**Error looks like:**
```
Access to fetch at 'https://artisan-rem1.onrender.com' from origin 'https://yourapp.vercel.app' 
has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present
```

**Solution:**
1. Check `CORS_ORIGINS` in Render includes your exact Vercel domain
2. Redeploy Render after changing env vars
3. Clear browser cache or use incognito mode

### Issue: Network Error or Timeout

**Check:**
1. Backend is actually running: `https://artisan-rem1.onrender.com`
2. Render service isn't sleeping (free tier sleeps after inactivity)
3. Check Render logs for errors

### Issue: 404 Not Found

**Your frontend might be calling the wrong path.**

Current API structure:
- Root: `/` → Returns API info
- Health: `/health` → Health check
- **Chat endpoint: `/api/chat`** ← Most important for your app
- Heavy features (disabled in minimal mode):
  - `/api/agents/*`
  - `/api/maps/*`
  - `/api/search/*`

Make sure your frontend uses `buildApiUrl("/api/chat")` not just `"/chat"`.

### Issue: 405 Method Not Allowed

- `/api/chat` only accepts POST requests
- Make sure you're not sending GET requests

---

## Step 5: Understanding Current Backend Mode

Your backend is running in **MINIMAL mode**. This means:

✅ Available:
- Root endpoint `/`
- Health check `/health`
- Minimal chat `/api/chat`

❌ Not Available (needs ENABLE_HEAVY_FEATURES=true):
- Full agent orchestration
- WebSocket support
- Monitoring endpoints
- Map services
- Advanced search

### To Enable Full Features:

In Render, set:
```bash
ENABLE_HEAVY_FEATURES=true
```

Also ensure you have these API keys set:
```bash
GROQ_API_KEY=your_key_here
TAVILY_API_KEY=your_key_here
```

---

## Quick Checklist

- [ ] Set `CORS_ORIGINS` in Render with Vercel domain
- [ ] Redeploy Render service
- [ ] Set `NEXT_PUBLIC_API_URL` in Vercel
- [ ] Redeploy Vercel app
- [ ] Test `https://artisan-rem1.onrender.com` in browser
- [ ] Check browser DevTools → Network tab for actual errors
- [ ] Verify frontend calls correct paths (e.g., `/api/chat` not `/chat`)

---

## Example: Complete Environment Setup

### Render Environment Variables
```bash
# Core
ENVIRONMENT=production
PORT=10000

# CORS - Update with your actual domain
CORS_ORIGINS=https://artisan-hub.vercel.app

# API Keys
GROQ_API_KEY=gsk_xxxxx

# Optional (for full features)
ENABLE_HEAVY_FEATURES=false
TAVILY_API_KEY=tvly_xxxxx
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=xxx
```

### Vercel Environment Variables
```bash
# Backend Connection
NEXT_PUBLIC_API_URL=https://artisan-rem1.onrender.com
NEXT_PUBLIC_WS_URL=wss://artisan-rem1.onrender.com/ws

# Other variables...
```

---

## Still Having Issues?

Check your browser's **Network tab** when the error occurs:

1. Open DevTools → Network
2. Try to use the feature that fails
3. Look for the failed request
4. Click on it → See the exact error

Common errors:
- **Status 0**: CORS issue
- **Status 404**: Wrong path
- **Status 405**: Wrong HTTP method (GET instead of POST)
- **Status 500**: Backend error (check Render logs)

Share the exact error from Network tab if you need more help!
