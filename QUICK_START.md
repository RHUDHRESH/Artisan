# ⚡ Quick Start Guide - 5 Minutes to Running Artisan Hub

Get Artisan Hub running **in under 5 minutes**!

---

## 📋 Prerequisites Check (1 minute)

Run these commands to verify you have everything:

```powershell
python --version        # Need 3.9+
node --version          # Need v18+
ollama --version        # Need Ollama installed
```

✅ All three installed? → Continue to Step 1

❌ Missing something? → Install from:
- Python: https://python.org
- Node.js: https://nodejs.org
- Ollama: https://ollama.com

---

## 🔧 Step 1: Download AI Models (2 minutes)

Open PowerShell and run:

```powershell
ollama pull gemma3:4b
ollama pull gemma3:1b
ollama pull nomic-embed-text
```

⏳ **This takes 10-15 minutes the first time** (download ~8GB)
- Keep this window open!
- Don't close it or restart!

---

## 🚀 Step 2: Start Backend (1 minute)

**New PowerShell window:**

```powershell
cd "C:\Users\hp\OneDrive\Desktop\Artisan"
.venv\Scripts\activate
pip install -r requirements.txt  # First time only
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

✅ You should see: `Uvicorn running on http://0.0.0.0:8000`

---

## 🎨 Step 3: Start Frontend (1 minute)

**Another new PowerShell window:**

```powershell
cd "C:\Users\hp\OneDrive\Desktop\Artisan\frontend"
npm install    # First time only
npm run dev
```

✅ You should see: `- Local: http://localhost:3000`

---

## 🌐 Step 4: Open Browser (instant)

```
http://localhost:3000
```

✅ **Done!** Artisan Hub is running!

---

## 📊 Terminal Status

You should have 3 terminals running:

```
Terminal 1: ollama serve          ✅ Running (port 11434)
Terminal 2: uvicorn backend       ✅ Running (port 8000)
Terminal 3: npm run dev (frontend) ✅ Running (port 3000)
Browser:    http://localhost:3000 ✅ Open
```

---

## 🎯 Using the App (2-3 minutes)

1. **Answer 8 questions** about your craft
2. **Click "Analyze My Craft"**
3. **Wait 30-60 seconds** for results
4. **View recommendations** from AI agents

---

## 🛑 To Stop Everything

Press **`Ctrl + C`** in each terminal

---

## ⚠️ Troubleshooting (If Something Fails)

### "Python not found"
```powershell
# Make sure Python 3.9+ is installed
python --version
```

### "Ollama not running"
```powershell
# Terminal 1 should have ollama serve
# Make sure it's still running (don't close it!)
```

### "Port 8000 already in use"
```powershell
# Use different port
uvicorn backend.main:app --port 8001
```

### "pip install failed"
```powershell
# Upgrade pip first
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### "npm ERR!"
```powershell
npm cache clean --force
npm install
npm run dev
```

---

## ✅ Done!

Your Artisan Hub is ready to use! 🎉

For detailed information, see **HOW_TO_USE.md**
