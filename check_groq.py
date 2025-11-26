
import os
import asyncio
import aiohttp
from dotenv import load_dotenv

load_dotenv()

groq_key = os.getenv("GROQ_API_KEY")

async def test_groq():
    if not groq_key:
        print("No Groq key found.")
        return

    print(f"Testing Groq with key: {groq_key[:5]}...")
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {groq_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama3-70b-8192",
        "messages": [{"role": "user", "content": "Hello"}],
        "max_tokens": 10
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as response:
            print(f"Status: {response.status}")
            if response.status == 200:
                data = await response.json()
                print(f"Response: {data['choices'][0]['message']['content']}")
            else:
                print(f"Error: {await response.text()}")

if __name__ == "__main__":
    asyncio.run(test_groq())
