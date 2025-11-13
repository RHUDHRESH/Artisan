# 🔧 Troubleshooting Guide - Common Issues & Solutions

Comprehensive troubleshooting for Artisan Hub issues.

---

## 📑 Table of Contents

1. [Installation Issues](#installation-issues)
2. [Backend Issues](#backend-issues)
3. [Frontend Issues](#frontend-issues)
4. [Ollama/AI Issues](#ollamaai-issues)
5. [API & Connection Issues](#api--connection-issues)
6. [Data & Results Issues](#data--results-issues)
7. [Performance Issues](#performance-issues)
8. [Windows-Specific Issues](#windows-specific-issues)

---

## 💾 Installation Issues

### ❌ "Python not found"

**Symptoms:**
```
'python' is not recognized as an internal or external command
```

**Solutions:**

1. **Check if Python is installed:**
   ```powershell
   python --version
   ```

2. **Reinstall Python:**
   - Download from https://www.python.org/downloads/
   - ✅ Check "Add Python to PATH" during installation
   - Restart PowerShell
   - Test: `python --version`

3. **Use full path to Python:**
   ```powershell
   C:\Users\YourUsername\AppData\Local\Programs\Python\Python311\python.exe --version
   ```

4. **Multiple Python versions:**
   ```powershell
   # Use specific version
   python3.11 --version
   py -3.11 --version
   ```

---

### ❌ "Node.js not found"

**Symptoms:**
```
'npm' is not recognized
'node' is not recognized
```

**Solutions:**

1. **Check if Node is installed:**
   ```powershell
   node --version
   npm --version
   ```

2. **Reinstall Node.js:**
   - Download from https://nodejs.org/
   - Use LTS version (v18 or newer)
   - Restart PowerShell
   - Test: `node --version`

3. **Clear npm cache:**
   ```powershell
   npm cache clean --force
   npm install -g npm@latest
   ```

---

### ❌ "Virtual environment creation fails"

**Symptoms:**
```
Error: [Errno 2] No such file or directory
ModuleNotFoundError: No module named 'venv'
```

**Solutions:**

1. **Create virtual environment manually:**
   ```powershell
   cd "C:\Users\hp\OneDrive\Desktop\Artisan"
   python -m venv .venv
   ```

2. **If that fails, use venv module:**
   ```powershell
   python -m pip install virtualenv
   virtualenv .venv
   .venv\Scripts\activate
   ```

3. **Delete and recreate:**
   ```powershell
   # Remove old env
   rmdir /s .venv

   # Create fresh
   python -m venv .venv
   .venv\Scripts\activate
   ```

---

### ❌ "pip install fails"

**Symptoms:**
```
ERROR: Could not install packages due to an EnvironmentError
ERROR: Microsoft Visual C++ 14.0 is required
```

**Solutions:**

1. **Upgrade pip first:**
   ```powershell
   .venv\Scripts\activate
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

2. **Install Visual C++ Build Tools:**
   - Download: https://visualstudio.microsoft.com/visual-cpp-build-tools/
   - Install "Desktop development with C++"
   - Restart PowerShell
   - Retry pip install

3. **Install packages one by one:**
   ```powershell
   pip install fastapi
   pip install uvicorn
   pip install pydantic
   # ... continue with other packages
   ```

4. **Use binary wheel versions:**
   ```powershell
   pip install --only-binary :all: -r requirements.txt
   ```

---

### ❌ "Playwright install fails"

**Symptoms:**
```
ERROR: Failed to download browser
playwright install chromium failed
```

**Solutions:**

1. **Retry install:**
   ```powershell
   .venv\Scripts\activate
   playwright install chromium
   ```

2. **Install with timeout:**
   ```powershell
   playwright install chromium --with-deps
   ```

3. **Manual browser download:**
   ```powershell
   # Try again later (network issue)
   playwright install
   ```

4. **Check disk space:**
   - Need ~500MB free
   - Check: `dir C:\`

---

## 🔙 Backend Issues

### ❌ "uvicorn: command not found"

**Symptoms:**
```
'uvicorn' is not recognized as an internal or external command
```

**Solutions:**

1. **Activate virtual environment:**
   ```powershell
   cd "C:\Users\hp\OneDrive\Desktop\Artisan"
   .venv\Scripts\activate
   # You should see (.venv) at the start
   ```

2. **Install uvicorn:**
   ```powershell
   pip install uvicorn
   ```

3. **Run with python module:**
   ```powershell
   python -m uvicorn backend.main:app --port 8000
   ```

---

### ❌ "Port 8000 already in use"

**Symptoms:**
```
OSError: [WinError 10048] Only one usage of each socket address
ERROR: Address already in use
```

**Solutions:**

1. **Use different port:**
   ```powershell
   uvicorn backend.main:app --port 8001 --reload
   ```

2. **Find process using port 8000:**
   ```powershell
   netstat -ano | findstr :8000
   # Note the PID (Process ID)
   taskkill /PID <PID> /F
   ```

3. **Kill all Python processes:**
   ```powershell
   taskkill /IM python.exe /F
   # Then restart
   ```

4. **Check what's using the port:**
   ```powershell
   Get-Process | Where-Object { $_.Handles -gt 1000 }
   ```

---

### ❌ "ModuleNotFoundError: No module named 'backend'"

**Symptoms:**
```
ModuleNotFoundError: No module named 'backend'
```

**Solutions:**

1. **Make sure you're in correct directory:**
   ```powershell
   cd "C:\Users\hp\OneDrive\Desktop\Artisan"
   ls backend/  # Should list backend folder
   ```

2. **Create __init__.py files:**
   ```powershell
   # Make sure these exist:
   backend/__init__.py
   backend/api/__init__.py
   backend/agents/__init__.py
   backend/core/__init__.py
   backend/scraping/__init__.py
   backend/services/__init__.py
   ```

3. **Install in development mode:**
   ```powershell
   pip install -e .
   ```

---

### ❌ "ImportError: cannot import name..."

**Symptoms:**
```
ImportError: cannot import name 'OllamaClient' from 'backend.core'
```

**Solutions:**

1. **Check file exists:**
   ```powershell
   ls backend/core/ollama_client.py
   ```

2. **Reinstall dependencies:**
   ```powershell
   pip install -r requirements.txt --force-reinstall
   ```

3. **Check Python path:**
   ```powershell
   python -c "import sys; print(sys.path)"
   ```

---

### ❌ "Backend crashes on startup"

**Symptoms:**
```
Application startup failed
AttributeError: ...
```

**Solutions:**

1. **Check for syntax errors:**
   ```powershell
   python -m py_compile backend/main.py
   ```

2. **Run with verbose logging:**
   ```powershell
   uvicorn backend.main:app --log-level debug --port 8000
   ```

3. **Check backend/main.py:**
   - Look for recent edits
   - Check imports are correct
   - Verify all dependencies installed

4. **Test imports manually:**
   ```powershell
   python
   >>> from backend.core.ollama_client import OllamaClient
   >>> from backend.config import settings
   ```

---

### ❌ "No module named 'chromadb'"

**Symptoms:**
```
ModuleNotFoundError: No module named 'chromadb'
```

**Solutions:**

```powershell
# Reinstall ChromaDB
pip install chromadb --upgrade

# Or reinstall all dependencies
pip install -r requirements.txt
```

---

## 🎨 Frontend Issues

### ❌ "npm: command not found"

**Symptoms:**
```
'npm' is not recognized as an internal or external command
```

**Solutions:**

1. **Reinstall Node.js** from https://nodejs.org/
2. **Restart PowerShell** after installation
3. **Test:** `npm --version`

---

### ❌ "Port 3000 already in use"

**Symptoms:**
```
Error: listen EADDRINUSE: address already in use :::3000
```

**Solutions:**

1. **Use different port:**
   ```powershell
   npm run dev -- -p 3001
   # Then open http://localhost:3001
   ```

2. **Kill process using port 3000:**
   ```powershell
   netstat -ano | findstr :3000
   taskkill /PID <PID> /F
   ```

3. **Find Node processes:**
   ```powershell
   taskkill /IM node.exe /F
   ```

---

### ❌ "npm ERR! code ERESOLVE"

**Symptoms:**
```
npm ERR! ERESOLVE unable to resolve dependency tree
```

**Solutions:**

1. **Clear npm cache:**
   ```powershell
   npm cache clean --force
   ```

2. **Remove node_modules and reinstall:**
   ```powershell
   cd frontend
   rmdir /s node_modules
   del package-lock.json
   npm install
   ```

3. **Force legacy peer dependencies:**
   ```powershell
   npm install --legacy-peer-deps
   npm run dev
   ```

---

### ❌ "npm ERR! FETCH404"

**Symptoms:**
```
npm ERR! 404 Not Found - GET https://registry.npmjs.org/...
```

**Solutions:**

1. **Check internet connection**

2. **Clear npm cache:**
   ```powershell
   npm cache clean --force
   ```

3. **Use different npm registry:**
   ```powershell
   npm config set registry https://registry.npmjs.org/
   npm install
   ```

4. **Retry after a few minutes** (npm registry might be down)

---

### ❌ "next: command not found"

**Symptoms:**
```
'next' is not recognized
npm ERR! missing script: dev
```

**Solutions:**

```powershell
cd frontend
npm install
npm run dev
```

---

### ❌ "Port already in use" (Next.js on 3000)

**See:** "Port 3000 already in use" above

---

## 🤖 Ollama/AI Issues

### ❌ "Ollama not found"

**Symptoms:**
```
WARNING: Ollama doesn't appear to be running
Connection refused: http://localhost:11434
```

**Solutions:**

1. **Download Ollama:**
   ```
   https://ollama.com
   ```

2. **Start Ollama in new terminal:**
   ```powershell
   ollama serve
   ```

3. **Keep terminal open** - Ollama must stay running!

4. **Test connection:**
   ```powershell
   curl http://localhost:11434/api/tags
   ```

---

### ❌ "Models not downloaded"

**Symptoms:**
```
Error: model not found
OLLAMA: Model 'gemma3:4b' not found
```

**Solutions:**

1. **Check available models:**
   ```powershell
   ollama list
   ```

2. **Download missing models:**
   ```powershell
   ollama pull gemma3:4b
   ollama pull gemma3:1b
   ollama pull nomic-embed-text
   ```

3. **Wait for download to complete** (10-15 minutes)

4. **Check again:**
   ```powershell
   ollama list
   ```

---

### ❌ "Ollama out of memory"

**Symptoms:**
```
CUDA out of memory
Error: not enough memory
```

**Solutions:**

1. **Reduce model size** - use smaller models
2. **Close other applications** to free RAM
3. **Use CPU instead of GPU:**
   ```powershell
   ollama serve --gpu=false
   ```

4. **Check system RAM:**
   - Need minimum 8GB RAM
   - Recommended 16GB+

---

### ❌ "AI responses are slow"

**Symptoms:**
```
Waiting 2+ minutes for AI response
Generation taking very long
```

**Solutions:**

1. **Check CPU/GPU usage:**
   - Task Manager → Performance
   - Look for bottlenecks

2. **Close unnecessary applications:**
   - Chrome with many tabs
   - Other heavy apps

3. **Use faster model:**
   ```
   # Change in backend/constants.py
   FAST_MODEL = "gemma3:1b"  # Already using 1B
   ```

4. **Increase RAM allocation** to Ollama:
   ```powershell
   # Windows: Increase available memory
   ```

---

### ❌ "Connection to Ollama timeout"

**Symptoms:**
```
TimeoutError: Connection to Ollama timed out
socket timeout
```

**Solutions:**

1. **Check Ollama is running:**
   ```powershell
   # Terminal 1 should show "listening on"
   ```

2. **Increase timeout in code:**
   - Edit `backend/constants.py`
   - Increase `TAVILY_API_TIMEOUT` value

3. **Restart Ollama:**
   ```powershell
   # Stop Ollama (Ctrl+C in Terminal 1)
   # Start again: ollama serve
   ```

4. **Check firewall:**
   - Windows Defender Firewall
   - Allow Ollama through firewall

---

## 🔗 API & Connection Issues

### ❌ "Cannot connect to backend"

**Symptoms:**
```
Failed to fetch from http://localhost:8000
Connection refused
```

**Solutions:**

1. **Verify backend is running:**
   ```
   Terminal 2 should show: "Uvicorn running on http://0.0.0.0:8000"
   ```

2. **Test connection manually:**
   ```powershell
   curl http://localhost:8000/health
   ```

3. **Check port 8000:**
   ```powershell
   netstat -ano | findstr :8000
   ```

4. **Restart backend:**
   ```powershell
   # Press Ctrl+C in Terminal 2
   # Restart: uvicorn backend.main:app --port 8000
   ```

---

### ❌ "CORS error"

**Symptoms:**
```
Access to XMLHttpRequest blocked by CORS policy
```

**Solutions:**

1. **Check frontend URL:**
   ```
   Frontend must be on: http://localhost:3000
   Backend must be on: http://localhost:8000
   ```

2. **CORS is configured in backend** - shouldn't happen

3. **Clear browser cache:**
   ```
   Ctrl+Shift+Delete → Clear all
   ```

4. **Try incognito window:**
   ```
   Ctrl+Shift+N → Test again
   ```

---

### ❌ "API returns 500 error"

**Symptoms:**
```
HTTP Error 500: Internal Server Error
```

**Solutions:**

1. **Check backend terminal** for error message

2. **Enable debug logging:**
   ```powershell
   # Edit backend/config.py
   # Set: log_level = "DEBUG"
   ```

3. **Restart backend** with debug:
   ```powershell
   uvicorn backend.main:app --log-level debug --port 8000
   ```

4. **Test with API docs:**
   ```
   http://localhost:8000/docs
   ```

---

### ❌ "API timeout"

**Symptoms:**
```
Request timed out after 30 seconds
```

**Solutions:**

1. **Check if Ollama is running** (might be processing)

2. **Check internet connection** (for web scraping)

3. **Increase timeout in constants:**
   ```python
   # backend/constants.py
   TAVILY_API_TIMEOUT = 60  # Increase from 30
   ```

4. **Check system resources** (RAM, CPU)

---

## 📊 Data & Results Issues

### ❌ "No results found for suppliers"

**Symptoms:**
```
Search returned 0 suppliers
Empty supplier list
```

**Solutions:**

1. **Try broader search terms:**
   ```
   ❌ "Imported German clay with 15% alumina"
   ✅ "Clay suppliers India"
   ```

2. **Check location spelling:**
   - Use standard city/state names
   - e.g., "Tamil Nadu" not "TN"

3. **Search manually:**
   - Google: "[material] suppliers [location]"
   - IndiaMART.com
   - TradeKey.com

4. **Try related materials:**
   - Searching for "ceramic glaze" instead of specific brand

---

### ❌ "No events found"

**Symptoms:**
```
Event search returned 0 results
No exhibitions in your region
```

**Solutions:**

1. **Seasonal variation:**
   - More events during festival season
   - Check back next month

2. **Manual search:**
   - Google Events
   - Eventbrite
   - Local craft associations
   - Instagram: #craftfair #exhibition

3. **Different craft type:**
   - Try broader craft category
   - e.g., "textiles" instead of "specific weave"

---

### ❌ "Results page stuck loading"

**Symptoms:**
```
Spinner keeps spinning
Results never appear
```

**Solutions:**

1. **Wait longer** (up to 2 minutes)
   - Scraping web takes time

2. **Check browser console** (F12 → Console):
   - Look for error messages
   - Take screenshot of error

3. **Check backend terminal:**
   - Should show API requests coming in
   - Look for error logs

4. **Refresh page:**
   ```
   Ctrl+R or F5
   Run analysis again
   ```

---

### ❌ "Results show old data"

**Symptoms:**
```
Same results as last week
Data not updated
```

**Solutions:**

1. **Refresh browser cache:**
   ```
   Ctrl+Shift+Delete → Clear all
   ```

2. **Clear backend cache:**
   ```
   rm -r data/cache/*
   ```

3. **Restart backend:**
   ```powershell
   # Ctrl+C in Terminal 2
   # Restart
   ```

---

## ⚡ Performance Issues

### ❌ "Application is very slow"

**Symptoms:**
```
Loading takes 30+ seconds
UI is unresponsive
```

**Solutions:**

1. **Check system resources:**
   - Task Manager → Performance
   - CPU, RAM usage
   - Close unnecessary apps

2. **Check internet speed:**
   - https://speedtest.net
   - Need at least 5 Mbps

3. **Clear browser cache:**
   ```
   Ctrl+Shift+Delete
   ```

4. **Restart services:**
   ```powershell
   # Ctrl+C all terminals
   # Wait 10 seconds
   # Restart each
   ```

---

### ❌ "High memory usage"

**Symptoms:**
```
RAM usage above 80%
Application becomes unresponsive
```

**Solutions:**

1. **Close unnecessary applications**

2. **Restart backend/frontend:**
   ```powershell
   # Stop and restart
   ```

3. **Check for memory leaks:**
   - Look at backend/frontend logs
   - Long-running processes

4. **Reduce Ollama memory:**
   ```powershell
   ollama serve --gpu=false
   ```

---

### ❌ "CPU usage at 100%"

**Symptoms:**
```
Fan noise increases
Computer becomes slow
CPU maxed out
```

**Solutions:**

1. **Check what's running:**
   - Task Manager → Processes
   - Find Python/Node processes

2. **Reduce model complexity:**
   - Use `gemma3:1b` instead of `4b`

3. **Close other applications**

4. **Restart Ollama:**
   ```powershell
   # Stop and restart
   ```

---

## 🪟 Windows-Specific Issues

### ❌ ".venv\Scripts\activate doesn't work"

**Symptoms:**
```
The script activate.ps1 is not digitally signed
```

**Solutions:**

1. **Run PowerShell as Administrator:**
   - Right-click PowerShell
   - "Run as Administrator"

2. **Change execution policy:**
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

3. **Try batch file activation:**
   ```powershell
   .venv\Scripts\activate.bat
   ```

4. **Use Python directly:**
   ```powershell
   .venv\Scripts\python.exe -m pip install ...
   ```

---

### ❌ "Path issues with spaces in folder names"

**Symptoms:**
```
Cannot find path 'C:\Users\hp\OneDrive\Desktop\...
```

**Solutions:**

1. **Use quotes around path:**
   ```powershell
   cd "C:\Users\hp\OneDrive\Desktop\Artisan"
   ```

2. **Use full path:**
   ```powershell
   & 'C:\Users\hp\OneDrive\Desktop\Artisan\.venv\Scripts\activate'
   ```

---

### ❌ "Windows Defender blocks Ollama"

**Symptoms:**
```
Windows Defender warning
Cannot run ollama.exe
```

**Solutions:**

1. **Add to Windows Defender exclusions:**
   - Settings → Virus & threat protection
   - Manage settings → Add exclusions
   - Add Ollama installation folder

2. **Temporarily disable Defender** (test only):
   - Not recommended for production

---

### ❌ "Git line endings issue"

**Symptoms:**
```
CRLF vs LF errors
```

**Solutions:**

```powershell
git config core.autocrlf true
git checkout HEAD -- .
```

---

## 📞 Still Having Issues?

### Getting Help:

1. **Check error messages:**
   - Browser console (F12)
   - Terminal output
   - Log files

2. **Gather information:**
   - Screenshot of error
   - Full error message
   - What you were doing when it happened

3. **Restart everything:**
   ```powershell
   # Close all terminals
   # Wait 30 seconds
   # Start fresh
   ```

4. **Report issue:**
   - GitHub: https://github.com/anthropics/claude-code/issues

---

## 🆘 Emergency Reset

If everything is broken:

```powershell
# Stop all services (Ctrl+C in all terminals)

# Remove virtual environment
rmdir /s .venv

# Remove node modules
cd frontend
rmdir /s node_modules
del package-lock.json
cd ..

# Delete cache
rmdir /s data/cache
rmdir /s data/chroma_db

# Recreate everything
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium

cd frontend
npm install
npm run dev

# In another terminal:
cd ..
.venv\Scripts\activate
uvicorn backend.main:app --port 8000
```

---

**Last Updated:** November 2025

