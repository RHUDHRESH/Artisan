"""
Ollama Client for interacting with Gemma 3 models
MANDATORY: Only use Gemma 3 models
"""
from typing import Dict, List, Optional
import aiohttp
import asyncio
from loguru import logger
from backend.config import settings


class OllamaClient:
    """
    Client for interacting with Ollama API
    MANDATORY: Only use Gemma 3 models
    """
    
    REASONING_MODEL = "gemma3:4b"  # For complex analysis
    FAST_MODEL = "gemma3:1b"       # For quick responses
    EMBED_MODEL = "nomic-embed-text:latest"    # For embeddings
    
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or settings.ollama_base_url
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def generate(
        self,
        prompt: str,
        model: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        stream: bool = False
    ) -> str:
        """
        Generate completion from Ollama
        
        Args:
            prompt: User prompt
            model: Model to use (must be 4b or 1b)
            system: System prompt
            temperature: Sampling temperature
            stream: Whether to stream response
        
        Returns:
            Generated text
        """
        if model not in [self.REASONING_MODEL, self.FAST_MODEL]:
            raise ValueError(
                f"Invalid model '{model}'. "
                f"Must use {self.REASONING_MODEL} or {self.FAST_MODEL}"
            )
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": temperature
            }
        }
        
        if system:
            payload["system"] = system
        
        logger.info(f"Generating with {model}: {prompt[:100]}...")
        
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        async with self.session.post(
            f"{self.base_url}/api/generate",
            json=payload
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Ollama error: {error_text}")
            
            result = await response.json()
            generated_text = result.get("response", "")
            
            logger.success(f"Generated {len(generated_text)} chars with {model}")
            return generated_text
    
    async def embed(self, text: str) -> List[float]:
        """
        Generate embeddings using Gemma 3 Embed
        
        Args:
            text: Text to embed
        
        Returns:
            Embedding vector
        """
        payload = {
            "model": self.EMBED_MODEL,
            "prompt": text
        }
        
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        async with self.session.post(
            f"{self.base_url}/api/embeddings",
            json=payload
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Embedding error: {error_text}")
            
            result = await response.json()
            embedding = result.get("embedding", [])
            
            logger.debug(f"Generated embedding (dim={len(embedding)})")
            return embedding
    
    async def reasoning_task(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7
    ) -> str:
        """
        Use 4B model for complex reasoning tasks
        """
        return await self.generate(
            prompt=prompt,
            model=self.REASONING_MODEL,
            system=system,
            temperature=temperature
        )
    
    async def fast_task(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.3
    ) -> str:
        """
        Use 1B model for fast, simple tasks
        """
        return await self.generate(
            prompt=prompt,
            model=self.FAST_MODEL,
            system=system,
            temperature=temperature
        )


# Test the client
async def test_ollama_client():
    async with OllamaClient() as client:
        # Test reasoning model
        print("Testing 4B reasoning model...")
        result = await client.reasoning_task(
            "Analyze this craft: I make blue pottery. What tools do I need?"
        )
        print(f"4B Result: {result[:200]}\n")
        
        # Test fast model
        print("Testing 1B fast model...")
        result = await client.fast_task(
            "Classify this as pottery, weaving, or metalwork: blue pottery"
        )
        print(f"1B Result: {result[:200]}\n")
        
        # Test embeddings
        print("Testing embeddings...")
        embedding = await client.embed("blue pottery artisan from jaipur")
        print(f"Embedding dimension: {len(embedding)}")
        print(f"First 5 values: {embedding[:5]}\n")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_ollama_client())
