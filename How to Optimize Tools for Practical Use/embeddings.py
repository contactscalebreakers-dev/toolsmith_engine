"""
Embeddings System for SB Toolsmith Pro

Semantic search and similarity matching using embeddings.
"""

import asyncio
import logging
import math
from typing import Optional, List, Dict, Any, Tuple

logger = logging.getLogger(__name__)


class EmbeddingStore:
    """Store and query embeddings."""

    def __init__(self, provider: Any):
        """
        Initialize embedding store.
        
        Args:
            provider: LLM provider (Ollama or OpenAI)
        """
        self.provider = provider
        self._embeddings: Dict[str, Tuple[str, List[float]]] = {}
        self._cache: Dict[str, List[float]] = {}

    async def add(self, key: str, text: str) -> bool:
        """
        Add text to store.
        
        Args:
            key: Unique identifier
            text: Text to embed
            
        Returns:
            True if successful
        """
        try:
            embedding = await self.provider.embed(text)
            if embedding:
                self._embeddings[key] = (text, embedding)
                self._cache[key] = embedding
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to add embedding: {e}")
            return False

    async def add_batch(self, items: Dict[str, str]) -> int:
        """
        Add multiple texts to store.
        
        Args:
            items: Dictionary of key -> text
            
        Returns:
            Number of successfully added items
        """
        count = 0
        for key, text in items.items():
            if await self.add(key, text):
                count += 1
        return count

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        threshold: float = 0.5,
    ) -> List[Tuple[str, float]]:
        """
        Search for similar items.
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            threshold: Minimum similarity threshold
            
        Returns:
            List of (key, similarity_score) tuples
        """
        results = []

        for key, (text, embedding) in self._embeddings.items():
            similarity = self._cosine_similarity(query_embedding, embedding)
            if similarity >= threshold:
                results.append((key, similarity))

        # Sort by similarity descending
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    async def search_text(
        self,
        query_text: str,
        top_k: int = 5,
        threshold: float = 0.5,
    ) -> List[Tuple[str, str, float]]:
        """
        Search using text query.
        
        Args:
            query_text: Query text
            top_k: Number of results
            threshold: Minimum similarity
            
        Returns:
            List of (key, text, similarity) tuples
        """
        # Generate query embedding
        query_embedding = await self.provider.embed(query_text)
        if not query_embedding:
            return []

        # Search
        results = self.search(query_embedding, top_k, threshold)

        # Expand with text
        expanded = []
        for key, similarity in results:
            text, _ = self._embeddings[key]
            expanded.append((key, text, similarity))

        return expanded

    def get(self, key: str) -> Optional[str]:
        """Get text by key."""
        if key in self._embeddings:
            return self._embeddings[key][0]
        return None

    def remove(self, key: str) -> bool:
        """Remove item from store."""
        if key in self._embeddings:
            del self._embeddings[key]
            if key in self._cache:
                del self._cache[key]
            return True
        return False

    def clear(self) -> None:
        """Clear all embeddings."""
        self._embeddings.clear()
        self._cache.clear()

    def size(self) -> int:
        """Get number of stored embeddings."""
        return len(self._embeddings)

    @staticmethod
    def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Similarity score (0-1)
        """
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    def get_stats(self) -> Dict[str, Any]:
        """Get store statistics."""
        return {
            "total_embeddings": len(self._embeddings),
            "cache_size": len(self._cache),
            "memory_usage_mb": sum(
                len(text) + len(embedding) * 4
                for text, embedding in self._embeddings.values()
            ) / 1024 / 1024,
        }
