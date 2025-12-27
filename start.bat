@echo off
REM ==========================================
REM   Artisan Hub - Simple Startup Script
REM ==========================================
REM
REM This script will:
REM   1. Check for Python
REM   2. Create/activate virtual environment
REM   3. Install dependencies (if needed)
REM   4. Check for Ollama
REM   5. Start backend and frontend
REM
REM ==========================================

echo.
echo ==========================================
echo   Artisan Hub - Starting Application
echo ==========================================
echo.

REM Step 1: Check Python
echo [1/5] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Python not found!
    echo Please install Python 3.9+ from python.org
    echo.
    pause
    exit /b 1
)
python --version
echo.

REM Step 2: Setup Virtual Environment
echo [2/5] Setting up virtual environment...
if exist ".venv" goto VENV_EXISTS
echo Creating virtual environment (first time only)...
python -m venv .venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)
echo Virtual environment created!
goto VENV_READY

:VENV_EXISTS
echo Virtual environment found.

:VENV_READY
call .venv\Scripts\activate
echo.

REM Warn if Groq/Supabase envs are missing
if "%GROQ_API_KEY%"=="" (
    echo WARNING: GROQ_API_KEY is not set. Cloud inference via Groq will fail.
)
if "%SUPABASE_URL%"=="" (
    echo INFO: SUPABASE_URL not configured. Backend will fall back to the local JSON store.
)
echo.

REM Step 3: Install Dependencies
echo [3/5] Checking dependencies...
python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies (first time only, may take a few minutes)...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
    echo.
    echo Installing Playwright browsers...
    playwright install chromium
    echo Dependencies installed!
) else (
    echo Dependencies already installed.
)
echo.

REM Step 4: Check cloud LLM keys
echo [4/5] Checking LLM API keys...
if "%GROQ_API_KEY%"=="" (
    if "%OPENROUTER_API_KEY%"=="" (
        if "%GEMINI_API_KEY%"=="" (
            echo WARNING: No LLM API key found. Set GROQ_API_KEY or OPENROUTER_API_KEY or GEMINI_API_KEY.
            echo AI features will fail until a cloud key is provided.
        ) else (
            echo Using Gemini fallback.
        )
    ) else (
        echo Using OpenRouter fallback (no GROQ_API_KEY found).
    )
) else (
    echo Using Groq as primary LLM provider.
)
echo.

REM Step 5: Start Services
echo [5/5] Starting services...
echo.

REM Start Backend
echo Starting Backend on http://localhost:8000...
start "Artisan Backend" cmd /k "call .venv\Scripts\activate && echo Backend running on http://localhost:8000 && echo Press Ctrl+C to stop && uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"

REM Wait for backend to initialize
echo Waiting for backend to start...
timeout /t 5 >nul

REM Start Frontend
echo.
if exist frontend\package.json (
    echo Starting Frontend on http://localhost:3000...
    cd frontend
    if not exist node_modules (
        echo Installing frontend dependencies (first time only)...
        call npm install
    )
    start "Artisan Frontend" cmd /k "echo Frontend running on http://localhost:3000 && echo Press Ctrl+C to stop && npm run dev"
    cd ..
    echo.
    echo ==========================================
    echo   Application Started Successfully!
    echo ==========================================
    echo.
    echo Backend:  http://localhost:8000
    echo Frontend: http://localhost:3000
    echo API Docs: http://localhost:8000/docs
    echo.
    echo Close the backend/frontend windows to stop the application.
    echo.
) else (
    echo Frontend not found (package.json missing).
    echo Backend is running at http://localhost:8000
    echo.
)

pause
