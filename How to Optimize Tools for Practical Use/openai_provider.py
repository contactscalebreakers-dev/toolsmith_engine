"""
OpenAI LLM Provider for SB Toolsmith Pro

Cloud-based LLM integration via OpenAI API.
"""

import asyncio
import logging
from typing import Optional, List, Dict, Any, AsyncGenerator

try:
    import openai
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)


class OpenAIProvider:
    """OpenAI cloud LLM provider."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-3.5-turbo",
        timeout: float = 60.0,
        base_url: Optional[str] = None,
    ):
        """
        Initialize OpenAI provider.
        
        Args:
            api_key: OpenAI API key
            model: Model name (gpt-3.5-turbo, gpt-4, etc.)
            timeout: Request timeout in seconds
            base_url: Optional custom base URL (for OpenAI-compatible APIs)
        """
        if not OPENAI_AVAILABLE:
            raise RuntimeError("openai package not installed")

        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.base_url = base_url

        # Initialize async client
        client_kwargs = {
            "api_key": api_key,
            "timeout": timeout,
        }
        if base_url:
            client_kwargs["base_url"] = base_url

        self.client = AsyncOpenAI(**client_kwargs)

    async def initialize(self) -> bool:
        """
        Initialize provider and verify connection.
        
        Returns:
            True if connection successful
        """
        try:
            # Test connection by listing models
            models = await self.client.models.list()
            logger.info(f"OpenAI connected. Available models: {len(list(models))}")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize OpenAI: {e}")
            return False

    async def close(self) -> None:
        """Close provider."""
        await self.client.close()

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
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content

        except asyncio.TimeoutError:
            logger.error("OpenAI request timeout")
            return ""
        except Exception as e:
            logger.error(f"OpenAI generation error: {e}")
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
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                top_p=top_p,
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except asyncio.TimeoutError:
            logger.error("OpenAI streaming timeout")
        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}")

    async def embed(self, text: str) -> Optional[List[float]]:
        """
        Generate embeddings for text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector or None
        """
        try:
            response = await self.client.embeddings.create(
                model="text-embedding-3-small",
                input=text,
            )
            return response.data[0].embedding

        except Exception as e:
            logger.error(f"OpenAI embedding error: {e}")
            return None

    async def is_healthy(self) -> bool:
        """Check if provider is healthy."""
        try:
            await self.client.models.list()
            return True
        except:
            return False
