# deployment_check.ps1 - Pre-deployment verification script for Windows PowerShell

Write-Host "🔍 Running Pre-Deployment Checks..." -ForegroundColor Cyan
Write-Host ""

$Errors = 0

# Check 1: Ollama
Write-Host "1. Checking Ollama..." -ForegroundColor Yellow
try {
    $ollamaList = ollama list 2>&1
    if ($ollamaList -match "gemma3:4b") {
        Write-Host "   ✓ gemma3:4b found" -ForegroundColor Green
    } else {
        Write-Host "   ✗ gemma3:4b NOT FOUND" -ForegroundColor Red
        $Errors++
    }
    
    if ($ollamaList -match "gemma3:1b") {
        Write-Host "   ✓ gemma3:1b found" -ForegroundColor Green
    } else {
        Write-Host "   ✗ gemma3:1b NOT FOUND" -ForegroundColor Red
        $Errors++
    }
    
    if ($ollamaList -match "gemma3:embed") {
        Write-Host "   ✓ gemma3:embed found" -ForegroundColor Green
    } else {
        Write-Host "   ✗ gemma3:embed NOT FOUND" -ForegroundColor Red
        $Errors++
    }
} catch {
    Write-Host "   ✗ Ollama not installed or not in PATH" -ForegroundColor Red
    $Errors++
}

# Check 2: Python dependencies
Write-Host ""
Write-Host "2. Checking Python dependencies..." -ForegroundColor Yellow
$modules = @("fastapi", "chromadb", "playwright", "aiohttp", "loguru")
foreach ($module in $modules) {
    try {
        python -c "import $module" 2>$null
        Write-Host "   ✓ $module" -ForegroundColor Green
    } catch {
        Write-Host "   ✗ $module" -ForegroundColor Red
        $Errors++
    }
}

# Check 3: Environment variables
Write-Host ""
Write-Host "3. Checking environment..." -ForegroundColor Yellow
if ($env:SERPAPI_KEY) {
    Write-Host "   ✓ SERPAPI_KEY configured" -ForegroundColor Green
} elseif (Test-Path ".env") {
    $envContent = Get-Content ".env"
    if ($envContent -match "SERPAPI_KEY" -and $envContent -notmatch "SERPAPI_KEY=your_serpapi_key_here") {
        Write-Host "   ✓ SERPAPI_KEY found in .env" -ForegroundColor Green
    } else {
        Write-Host "   ⚠ SERPAPI_KEY not configured in .env" -ForegroundColor Yellow
        $Errors++
    }
} else {
    Write-Host "   ⚠ .env file not found" -ForegroundColor Yellow
    $Errors++
}

# Check 4: Directory structure
Write-Host ""
Write-Host "4. Checking directory structure..." -ForegroundColor Yellow
$dirs = @("backend", "backend/agents", "backend/core", "data")
foreach ($dir in $dirs) {
    if (Test-Path $dir) {
        Write-Host "   ✓ $dir/" -ForegroundColor Green
    } else {
        Write-Host "   ✗ $dir/" -ForegroundColor Red
        $Errors++
    }
}

# Check 5: Backend health
Write-Host ""
Write-Host "5. Checking backend health..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
    if ($response.Content -match "healthy") {
        Write-Host "   ✓ Backend is healthy" -ForegroundColor Green
    } else {
        Write-Host "   ⚠ Backend is running but degraded" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ⚠ Backend not running (start with: cd backend; python main.py)" -ForegroundColor Yellow
}

# Summary
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
if ($Errors -eq 0) {
    Write-Host "✓✓✓ ALL CHECKS PASSED ✓✓✓" -ForegroundColor Green
    exit 0
} else {
    Write-Host "✗✗✗ $Errors ERRORS FOUND ✗✗✗" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please fix the errors above before deployment." -ForegroundColor Yellow
    exit 1
}

