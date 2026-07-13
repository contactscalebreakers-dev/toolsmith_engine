"""
Ollama LLM Provider for SB Toolsmith Pro

Local LLM integration via Ollama API.
"""

import asyncio
import json
import logging
from typing import Optional, List, Dict, Any, AsyncGenerator

import aiohttp

logger = logging.getLogger(__name__)


class OllamaProvider:
    """Ollama local LLM provider."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "mistral",
        timeout: float = 300.0,
    ):
        """
        Initialize Ollama provider.
        
        Args:
            base_url: Ollama API base URL
            model: Model name (mistral, llama2, neural-chat, etc.)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self._session: Optional[aiohttp.ClientSession] = None
        self._available_models: List[str] = []

    async def initialize(self) -> bool:
        """
        Initialize provider and verify connection.
        
        Returns:
            True if connection successful
        """
        try:
            self._session = aiohttp.ClientSession()
            
            # Test connection
            async with self._session.get(
                f"{self.base_url}/api/tags",
                timeout=aiohttp.ClientTimeout(total=5),
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self._available_models = [m["name"] for m in data.get("models", [])]
                    logger.info(f"Ollama connected. Available models: {self._available_models}")
                    return True
                else:
                    logger.error(f"Ollama connection failed: {resp.status}")
                    return False

        except Exception as e:
            logger.error(f"Failed to initialize Ollama: {e}")
            return False

    async def close(self) -> None:
        """Close provider."""
        if self._session:
            await self._session.close()

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate text completion.
        
        Args:
            prompt: Input prompt
            system: System message
            temperature: Sampling temperature (0-1)
            top_p: Top-p sampling parameter
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
        """
        if not self._session:
            raise RuntimeError("Provider not initialized")

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            async with self._session.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "top_p": top_p,
                    },
                },
                timeout=aiohttp.ClientTimeout(total=self.timeout),
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("message", {}).get("content", "")
                else:
                    logger.error(f"Ollama generation failed: {resp.status}")
                    return ""

        except asyncio.TimeoutError:
            logger.error("Ollama request timeout")
            return ""
        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            return ""

    async def generate_stream(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        top_p: float = 0.9,
    ) -> AsyncGenerator[str, None]:
        """
        Generate text with streaming.
        
        Args:
            prompt: Input prompt
            system: System message
            temperature: Sampling temperature
            top_p: Top-p sampling
            
        Yields:
            Generated text chunks
        """
        if not self._session:
            raise RuntimeError("Provider not initialized")

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            async with self._session.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": True,
                    "options": {
                        "temperature": temperature,
                        "top_p": top_p,
                    },
                },
                timeout=aiohttp.ClientTimeout(total=self.timeout),
            ) as resp:
                if resp.status == 200:
                    async for line in resp.content:
                        if line:
                            try:
                                data = json.loads(line)
                                content = data.get("message", {}).get("content", "")
                                if content:
                                    yield content
                            except json.JSONDecodeError:
                                continue
                else:
                    logger.error(f"Ollama streaming failed: {resp.status}")

        except asyncio.TimeoutError:
            logger.error("Ollama streaming timeout")
        except Exception as e:
            logger.error(f"Ollama streaming error: {e}")

    async def embed(self, text: str) -> Optional[List[float]]:
        """
        Generate embeddings for text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector or None
        """
        if not self._session:
            raise RuntimeError("Provider not initialized")

        try:
            async with self._session.post(
                f"{self.base_url}/api/embeddings",
                json={
                    "model": self.model,
                    "prompt": text,
                },
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("embedding")
                else:
                    logger.error(f"Ollama embedding failed: {resp.status}")
                    return None

        except Exception as e:
            logger.error(f"Ollama embedding error: {e}")
            return None

    async def pull_model(self, model_name: str) -> bool:
        """
        Pull a model from Ollama registry.
        
        Args:
            model_name: Model name to pull
            
        Returns:
            True if successful
        """
        if not self._session:
            raise RuntimeError("Provider not initialized")

        try:
            async with self._session.post(
                f"{self.base_url}/api/pull",
                json={"name": model_name},
                timeout=aiohttp.ClientTimeout(total=3600),  # 1 hour
            ) as resp:
                if resp.status == 200:
                    logger.info(f"Successfully pulled model: {model_name}")
                    self._available_models.append(model_name)
                    return True
                else:
                    logger.error(f"Failed to pull model: {resp.status}")
                    return False

        except Exception as e:
            logger.error(f"Model pull error: {e}")
            return False

    def get_available_models(self) -> List[str]:
        """Get list of available models."""
        return self._available_models

    async def is_healthy(self) -> bool:
        """Check if provider is healthy."""
        if not self._session:
            return False

        try:
            async with self._session.get(
                f"{self.base_url}/api/tags",
                timeout=aiohttp.ClientTimeout(total=5),
            ) as resp:
                return resp.status == 200
        except:
            return False
