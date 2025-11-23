"""
LLM Provider Interface - Supports multiple inference providers
Supports: GROQ (primary), Ollama (fallback)
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from enum import Enum
import aiohttp
import asyncio
from loguru import logger


class LLMProvider(str, Enum):
    """Available LLM providers"""
    GROQ = "groq"
    OLLAMA = "ollama"


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients"""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        model: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        stream: bool = False
    ) -> str:
        """Generate completion"""
        pass

    @abstractmethod
    async def reasoning_task(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7
    ) -> str:
        """Complex reasoning task"""
        pass

    @abstractmethod
    async def fast_task(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.3
    ) -> str:
        """Quick/simple task"""
        pass

    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """Generate embeddings"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if provider is available"""
        pass


class GroqClient(BaseLLMClient):
    """
    GROQ API Client - Fast inference with various models
    """

    # GROQ model mappings
    REASONING_MODEL = "llama-3.3-70b-versatile"  # Best for complex reasoning
    FAST_MODEL = "llama-3.1-8b-instant"          # Fast responses
    EMBED_MODEL = "nomic-embed-text:latest"      # For embeddings (fallback to Ollama)

    def __init__(self, api_key: str, base_url: str = "https://api.groq.com/openai/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def health_check(self) -> bool:
        """Check if GROQ API is available"""
        try:
            if not self.api_key or self.api_key == "your-groq-api-key-here":
                logger.warning("GROQ API key not configured")
                return False

            if not self.session:
                self.session = aiohttp.ClientSession()

            # Try a minimal API call to verify connectivity
            async with self.session.get(
                f"{self.base_url}/models",
                headers=self._headers,
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"GROQ health check failed: {e}")
            return False

    async def generate(
        self,
        prompt: str,
        model: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        stream: bool = False
    ) -> str:
        """
        Generate completion from GROQ

        Args:
            prompt: User prompt
            model: Model to use
            system: System prompt
            temperature: Sampling temperature
            stream: Whether to stream response (not implemented yet)

        Returns:
            Generated text
        """
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 2048,
            "stream": False  # GROQ streaming not implemented yet
        }

        logger.info(f"🚀 GROQ generating with {model}: {prompt[:100]}...")

        if not self.session:
            self.session = aiohttp.ClientSession()

        try:
            async with self.session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=self._headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"GROQ error ({response.status}): {error_text}")

                result = await response.json()
                generated_text = result["choices"][0]["message"]["content"]

                logger.success(f"✅ GROQ generated {len(generated_text)} chars with {model}")
                return generated_text

        except Exception as e:
            logger.error(f"❌ GROQ generation failed: {e}")
            raise

    async def reasoning_task(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7
    ) -> str:
        """Use GROQ's powerful model for complex reasoning"""
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
        """Use GROQ's fast model for quick tasks"""
        return await self.generate(
            prompt=prompt,
            model=self.FAST_MODEL,
            system=system,
            temperature=temperature
        )

    async def embed(self, text: str) -> List[float]:
        """
        Generate embeddings - GROQ doesn't support embeddings yet
        This will fallback to Ollama automatically via LLMManager
        """
        raise NotImplementedError("GROQ doesn't support embeddings - use Ollama fallback")


class OllamaClient(BaseLLMClient):
    """
    Ollama Client for local inference
    Supports: Gemma 3, LLaMA, and other local models
    """

    REASONING_MODEL = "gemma3:4b"  # For complex analysis
    FAST_MODEL = "gemma3:1b"       # For quick responses
    EMBED_MODEL = "nomic-embed-text:latest"    # For embeddings

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def health_check(self) -> bool:
        """Check if Ollama is available"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()

            async with self.session.get(
                f"{self.base_url}/api/tags",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False

    async def generate(
        self,
        prompt: str,
        model: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        stream: bool = False
    ) -> str:
        """Generate completion from Ollama"""
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

        logger.info(f"🏠 Ollama generating with {model}: {prompt[:100]}...")

        if not self.session:
            self.session = aiohttp.ClientSession()

        try:
            async with self.session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Ollama error: {error_text}")

                result = await response.json()
                generated_text = result.get("response", "")

                logger.success(f"✅ Ollama generated {len(generated_text)} chars with {model}")
                return generated_text

        except Exception as e:
            logger.error(f"❌ Ollama generation failed: {e}")
            raise

    async def embed(self, text: str) -> List[float]:
        """Generate embeddings using Ollama"""
        payload = {
            "model": self.EMBED_MODEL,
            "prompt": text
        }

        if not self.session:
            self.session = aiohttp.ClientSession()

        try:
            async with self.session.post(
                f"{self.base_url}/api/embeddings",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Embedding error: {error_text}")

                result = await response.json()
                embedding = result.get("embedding", [])

                logger.debug(f"Generated embedding (dim={len(embedding)})")
                return embedding

        except Exception as e:
            logger.error(f"❌ Ollama embedding failed: {e}")
            raise

    async def reasoning_task(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7
    ) -> str:
        """Use Ollama for complex reasoning"""
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
        """Use Ollama for fast tasks"""
        return await self.generate(
            prompt=prompt,
            model=self.FAST_MODEL,
            system=system,
            temperature=temperature
        )


class LLMManager:
    """
    Manages multiple LLM providers with automatic fallback
    Primary: GROQ (fast cloud inference)
    Fallback: Ollama (local inference)
    """

    def __init__(
        self,
        primary_provider: LLMProvider = LLMProvider.GROQ,
        groq_api_key: Optional[str] = None,
        ollama_base_url: str = "http://localhost:11434"
    ):
        self.primary_provider = primary_provider
        self.groq_client = GroqClient(api_key=groq_api_key) if groq_api_key else None
        self.ollama_client = OllamaClient(base_url=ollama_base_url)

        self._primary_available = False
        self._fallback_available = False

    async def __aenter__(self):
        # Initialize both clients
        if self.groq_client:
            await self.groq_client.__aenter__()
        await self.ollama_client.__aenter__()

        # Check availability
        if self.groq_client:
            self._primary_available = await self.groq_client.health_check()
        self._fallback_available = await self.ollama_client.health_check()

        if self.primary_provider == LLMProvider.GROQ:
            if self._primary_available:
                logger.info("🚀 GROQ provider available (primary)")
            elif self._fallback_available:
                logger.warning("⚠️ GROQ unavailable, falling back to Ollama")
            else:
                logger.error("❌ No LLM providers available!")
        else:
            logger.info("🏠 Ollama provider selected (primary)")

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.groq_client:
            await self.groq_client.__aexit__(exc_type, exc_val, exc_tb)
        await self.ollama_client.__aexit__(exc_type, exc_val, exc_tb)

    def _get_active_client(self) -> BaseLLMClient:
        """Get the active client based on availability"""
        if self.primary_provider == LLMProvider.GROQ:
            if self._primary_available and self.groq_client:
                return self.groq_client
            elif self._fallback_available:
                logger.warning("Using Ollama fallback")
                return self.ollama_client
            else:
                raise Exception("No LLM providers available")
        else:
            # Primary is Ollama
            if self._fallback_available:
                return self.ollama_client
            elif self._primary_available and self.groq_client:
                logger.warning("Ollama unavailable, using GROQ")
                return self.groq_client
            else:
                raise Exception("No LLM providers available")

    async def reasoning_task(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7
    ) -> str:
        """Execute complex reasoning task with thinking display"""
        client = self._get_active_client()

        # Log what we're thinking about
        provider_name = "GROQ" if isinstance(client, GroqClient) else "Ollama"
        logger.info(f"💭 Thinking ({provider_name}): {prompt[:150]}...")

        return await client.reasoning_task(prompt, system, temperature)

    async def fast_task(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.3
    ) -> str:
        """Execute fast task"""
        client = self._get_active_client()
        return await client.fast_task(prompt, system, temperature)

    async def embed(self, text: str) -> List[float]:
        """Generate embeddings - always use Ollama for embeddings"""
        if not self._fallback_available:
            raise Exception("Ollama not available for embeddings")
        return await self.ollama_client.embed(text)

    async def health_check(self) -> Dict[str, any]:
        """Check health of all providers"""
        groq_available = False
        if self.groq_client:
            groq_available = await self.groq_client.health_check()

        ollama_available = await self.ollama_client.health_check()

        return {
            "groq": {
                "available": groq_available,
                "is_primary": self.primary_provider == LLMProvider.GROQ
            },
            "ollama": {
                "available": ollama_available,
                "is_primary": self.primary_provider == LLMProvider.OLLAMA
            },
            "active_provider": "groq" if (self.primary_provider == LLMProvider.GROQ and groq_available) else "ollama"
        }
