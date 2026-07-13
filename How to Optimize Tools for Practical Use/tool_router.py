"""
Tool Router for SB Toolsmith Pro

Intelligent tool selection based on semantic understanding.
"""

import logging
from typing import Optional, List, Dict, Any, Tuple

from .embeddings import EmbeddingStore

logger = logging.getLogger(__name__)


class ToolRouter:
    """Route requests to appropriate tools."""

    def __init__(self, provider: Any):
        """
        Initialize tool router.
        
        Args:
            provider: LLM provider
        """
        self.provider = provider
        self.embedding_store = EmbeddingStore(provider)
        self._tool_registry: Dict[str, Dict[str, Any]] = {}
        self._tool_embeddings_loaded = False

    async def register_tool(
        self,
        tool_key: str,
        name: str,
        description: str,
        capabilities: List[str],
        tags: List[str] = None,
    ) -> bool:
        """
        Register a tool for routing.
        
        Args:
            tool_key: Unique tool identifier
            name: Tool name
            description: Tool description
            capabilities: List of capabilities
            tags: Optional tags
            
        Returns:
            True if successful
        """
        self._tool_registry[tool_key] = {
            "name": name,
            "description": description,
            "capabilities": capabilities,
            "tags": tags or [],
        }

        # Add to embedding store
        embedding_text = f"{name} {description} {' '.join(capabilities)} {' '.join(tags or [])}"
        success = await self.embedding_store.add(tool_key, embedding_text)

        if success:
            logger.info(f"Registered tool: {tool_key}")
        else:
            logger.warning(f"Failed to embed tool: {tool_key}")

        return success

    async def route(
        self,
        query: str,
        top_k: int = 3,
        threshold: float = 0.5,
    ) -> List[Tuple[str, str, float]]:
        """
        Route query to appropriate tools.
        
        Args:
            query: User query
            top_k: Number of tools to return
            threshold: Minimum similarity threshold
            
        Returns:
            List of (tool_key, tool_name, confidence) tuples
        """
        if not self._tool_registry:
            logger.warning("No tools registered")
            return []

        try:
            # Search embeddings
            results = await self.embedding_store.search_text(
                query,
                top_k=top_k,
                threshold=threshold,
            )

            # Convert to router format
            routed = []
            for tool_key, _, similarity in results:
                if tool_key in self._tool_registry:
                    tool_name = self._tool_registry[tool_key]["name"]
                    routed.append((tool_key, tool_name, similarity))

            logger.info(f"Routed query to {len(routed)} tools")
            return routed

        except Exception as e:
            logger.error(f"Routing error: {e}")
            return []

    async def route_with_reasoning(
        self,
        query: str,
        top_k: int = 3,
    ) -> Dict[str, Any]:
        """
        Route with LLM reasoning.
        
        Args:
            query: User query
            top_k: Number of tools to consider
            
        Returns:
            Routing decision with reasoning
        """
        # Get candidate tools
        candidates = await self.route(query, top_k=top_k, threshold=0.3)

        if not candidates:
            return {
                "query": query,
                "selected_tool": None,
                "reasoning": "No suitable tools found",
                "confidence": 0.0,
            }

        # Build tool descriptions
        tool_descriptions = []
        for tool_key, tool_name, similarity in candidates:
            tool_info = self._tool_registry[tool_key]
            desc = f"- {tool_name}: {tool_info['description']} (Capabilities: {', '.join(tool_info['capabilities'])})"
            tool_descriptions.append(desc)

        # Ask LLM for reasoning
        prompt = f"""Given the following query and available tools, select the most appropriate tool.

Query: {query}

Available Tools:
{chr(10).join(tool_descriptions)}

Respond with:
1. Selected tool name
2. Reasoning (1-2 sentences)
3. Confidence (0-100%)"""

        reasoning = await self.provider.generate(
            prompt,
            system="You are a tool selection assistant. Select the most appropriate tool for the given query.",
            temperature=0.3,
        )

        # Parse response
        selected_tool = candidates[0][0] if candidates else None
        confidence = candidates[0][2] if candidates else 0.0

        return {
            "query": query,
            "selected_tool": selected_tool,
            "selected_tool_name": candidates[0][1] if candidates else None,
            "candidates": [(k, n, float(c)) for k, n, c in candidates],
            "reasoning": reasoning,
            "confidence": confidence,
        }

    def get_tool_info(self, tool_key: str) -> Optional[Dict[str, Any]]:
        """Get tool information."""
        return self._tool_registry.get(tool_key)

    def list_tools(self) -> List[Dict[str, Any]]:
        """List all registered tools."""
        return list(self._tool_registry.values())

    def get_capabilities(self, tool_key: str) -> List[str]:
        """Get tool capabilities."""
        tool = self._tool_registry.get(tool_key)
        return tool["capabilities"] if tool else []

    def get_stats(self) -> Dict[str, Any]:
        """Get router statistics."""
        return {
            "registered_tools": len(self._tool_registry),
            "embedding_store_size": self.embedding_store.size(),
            "embedding_stats": self.embedding_store.get_stats(),
        }
