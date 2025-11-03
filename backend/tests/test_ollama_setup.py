"""
Test script to verify Ollama setup and models
"""
import requests
import json


def test_ollama_connection():
    """Verify Ollama is running"""
    try:
        response = requests.get("http://localhost:11434/api/tags")
        assert response.status_code == 200, "Ollama not responding"
        models = response.json()["models"]
        model_names = [m["name"] for m in models]
        
        # Check all required models
        assert "gemma3:4b" in model_names, "gemma3:4b not found"
        assert "gemma3:1b" in model_names, "gemma3:1b not found"
        assert "gemma3:embed" in model_names, "gemma3:embed not found"
        print("✓ All required models installed")
    except Exception as e:
        print(f"✗ Ollama setup failed: {e}")
        raise


def test_inference_4b():
    """Test 4B model inference"""
    payload = {
        "model": "gemma3:4b",
        "prompt": "What is 2+2?",
        "stream": False
    }
    response = requests.post(
        "http://localhost:11434/api/generate",
        json=payload
    )
    assert response.status_code == 200
    result = response.json()
    assert "response" in result
    print(f"✓ 4B model working: {result['response'][:50]}")


def test_inference_1b():
    """Test 1B model inference"""
    payload = {
        "model": "gemma3:1b",
        "prompt": "Hello",
        "stream": False
    }
    response = requests.post(
        "http://localhost:11434/api/generate",
        json=payload
    )
    assert response.status_code == 200
    print("✓ 1B model working")


def test_embeddings():
    """Test embedding model"""
    payload = {
        "model": "gemma3:embed",
        "prompt": "Test embedding"
    }
    response = requests.post(
        "http://localhost:11434/api/embeddings",
        json=payload
    )
    assert response.status_code == 200
    result = response.json()
    assert "embedding" in result
    assert len(result["embedding"]) > 0
    print(f"✓ Embedding model working (dim={len(result['embedding'])})")


if __name__ == "__main__":
    test_ollama_connection()
    test_inference_4b()
    test_inference_1b()
    test_embeddings()
    print("\n✓✓✓ All Ollama tests passed ✓✓✓")

