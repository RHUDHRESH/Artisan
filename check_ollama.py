
import requests
from backend.config import settings

def check_ollama():
    try:
        url = f"{settings.ollama_base_url}/api/tags"
        print(f"Checking Ollama at {url}...")
        response = requests.get(url, timeout=5)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("Ollama is running.")
            models = response.json().get('models', [])
            print(f"Available models: {[m['name'] for m in models]}")
        else:
            print("Ollama returned error.")
    except Exception as e:
        print(f"Ollama check failed: {e}")

if __name__ == "__main__":
    check_ollama()
