#!/bin/bash
# deployment_check.sh
# Pre-Deployment Verification - matching next.md specification

echo "🔍 Running Pre-Deployment Checks..."

# Check 1: Ollama
echo "\n1. Checking Ollama..."
if ollama list | grep -q "gemma3:4b"; then
    echo "   ✓ gemma3:4b found"
else
    echo "   ✗ gemma3:4b NOT FOUND"
    exit 1
fi

if ollama list | grep -q "gemma3:1b"; then
    echo "   ✓ gemma3:1b found"
else
    echo "   ✗ gemma3:1b NOT FOUND"
    exit 1
fi

if ollama list | grep -q "gemma3:embed"; then
    echo "   ✓ gemma3:embed found"
else
    echo "   ✗ gemma3:embed NOT FOUND"
    exit 1
fi

# Check 2: Python dependencies
echo "\n2. Checking Python dependencies..."
python -c "import fastapi" 2>/dev/null && echo "   ✓ FastAPI" || { echo "   ✗ FastAPI"; exit 1; }
python -c "import chromadb" 2>/dev/null && echo "   ✓ ChromaDB" || { echo "   ✗ ChromaDB"; exit 1; }
python -c "import playwright" 2>/dev/null && echo "   ✓ Playwright" || { echo "   ✗ Playwright"; exit 1; }

# Check 3: Environment variables
echo "\n3. Checking environment..."
if [ -z "$SERPAPI_KEY" ]; then
    echo "   ✗ SERPAPI_KEY not set"
    exit 1
else
    echo "   ✓ SERPAPI_KEY configured"
fi

# Check 4: Backend health
echo "\n4. Checking backend..."
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    echo "   ✓ Backend is healthy"
else
    echo "   ✗ Backend not responding"
    exit 1
fi

echo "\n✓✓✓ ALL CHECKS PASSED ✓✓✓"

