"""
Backend Verification Script
Tests all components: Ollama, ChromaDB, API endpoints
"""
import asyncio
import sys
import requests
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

async def verify_ollama():
    """Verify Ollama models are available"""
    print("[CHECK] Verifying Ollama Models...")
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code != 200:
            print("[FAIL] Ollama not running")
            return False
        
        models = response.json().get("models", [])
        model_names = [m["name"] for m in models]
        
        required = ["gemma3:4b", "gemma3:1b", "gemma3:embed"]
        missing = [m for m in required if m not in model_names]
        
        if missing:
            print(f"[FAIL] Missing models: {', '.join(missing)}")
            print("  Run: ollama pull gemma3:4b && ollama pull gemma3:1b && ollama pull gemma3:embed")
            return False
        
        print("[PASS] All Ollama models available")
        
        # Test inference
        print("  Testing 4B model...")
        payload = {"model": "gemma3:4b", "prompt": "Say hello", "stream": False}
        resp = requests.post("http://localhost:11434/api/generate", json=payload, timeout=30)
        if resp.status_code == 200:
            print("  [PASS] 4B model responding")
        else:
            print("  [FAIL] 4B model not responding")
            return False
        
        return True
    except Exception as e:
        print(f"[FAIL] Ollama verification failed: {e}")
        return False

async def verify_chromadb():
    """Verify ChromaDB setup"""
    print("\n[CHECK] Verifying ChromaDB...")
    try:
        from backend.core.vector_store import ArtisanVectorStore
        store = ArtisanVectorStore("./data/test_verify")
        
        # Test add
        test_id = "test_verify_001"
        await store.add_craft_knowledge(
            craft_type="test",
            content="Test content",
            metadata={"test": True}
        )
        print("  [PASS] ChromaDB write working")
        
        # Test search
        results = await store.search_craft_knowledge("test", top_k=1)
        if results:
            print("  [PASS] ChromaDB search working")
        
        return True
    except Exception as e:
        print(f"[FAIL] ChromaDB verification failed: {e}")
        return False

def verify_api_endpoints():
    """Verify API endpoints are accessible"""
    print("\n[CHECK] Verifying API Endpoints...")
    base = "http://localhost:8000"
    
    endpoints = [
        ("/", "GET"),
        ("/health", "GET"),
        ("/docs", "GET"),
    ]
    
    all_ok = True
    for endpoint, method in endpoints:
        try:
            if method == "GET":
                resp = requests.get(f"{base}{endpoint}", timeout=5)
            if resp.status_code in [200, 405]:  # 405 is OK for some endpoints
                print(f"  [PASS] {method} {endpoint}")
            else:
                print(f"  [FAIL] {method} {endpoint} - Status: {resp.status_code}")
                all_ok = False
        except Exception as e:
            print(f"  [FAIL] {method} {endpoint} - Error: {e}")
            all_ok = False
    
    return all_ok

async def main():
    """Run all verifications"""
    print("=" * 60)
    print("BACKEND VERIFICATION")
    print("=" * 60)
    
    results = {
        "Ollama": await verify_ollama(),
        "ChromaDB": await verify_chromadb(),
        "API": verify_api_endpoints(),
    }
    
    print("\n" + "=" * 60)
    print("RESULTS:")
    print("=" * 60)
    for component, status in results.items():
        status_icon = "[PASS]" if status else "[FAIL]"
        print(f"{status_icon} {component}")
    
    all_pass = all(results.values())
    if all_pass:
        print("\n[SUCCESS] ALL BACKEND COMPONENTS VERIFIED")
    else:
        print("\n[WARNING] SOME COMPONENTS FAILED - Fix issues before proceeding")
    
    return all_pass

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

