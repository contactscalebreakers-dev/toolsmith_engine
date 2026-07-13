"""
Graph Persistence for SB Toolsmith Pro

Save and load DAG graphs.
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class GraphPersistence:
    """Persist and load DAG graphs."""

    def __init__(self, storage_dir: Optional[Path] = None):
        """
        Initialize graph persistence.
        
        Args:
            storage_dir: Directory for storing graphs
        """
        self.storage_dir = storage_dir or Path.home() / ".sb-toolsmith" / "graphs"
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save_graph(
        self,
        graph_name: str,
        graph_data: Dict[str, Any],
        description: Optional[str] = None,
    ) -> bool:
        """
        Save graph to file.
        
        Args:
            graph_name: Name of graph
            graph_data: Graph data (nodes, edges)
            description: Optional description
            
        Returns:
            True if successful
        """
        try:
            file_path = self.storage_dir / f"{graph_name}.json"

            # Add metadata
            data = {
                "name": graph_name,
                "description": description or "",
                "version": "1.0",
                "graph": graph_data,
            }

            with open(file_path, "w") as f:
                json.dump(data, f, indent=2)

            logger.info(f"Graph saved: {graph_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to save graph: {e}")
            return False

    def load_graph(self, graph_name: str) -> Optional[Dict[str, Any]]:
        """
        Load graph from file.
        
        Args:
            graph_name: Name of graph
            
        Returns:
            Graph data or None
        """
        try:
            file_path = self.storage_dir / f"{graph_name}.json"

            if not file_path.exists():
                logger.warning(f"Graph not found: {graph_name}")
                return None

            with open(file_path, "r") as f:
                data = json.load(f)

            logger.info(f"Graph loaded: {graph_name}")
            return data.get("graph")

        except Exception as e:
            logger.error(f"Failed to load graph: {e}")
            return None

    def delete_graph(self, graph_name: str) -> bool:
        """Delete graph file."""
        try:
            file_path = self.storage_dir / f"{graph_name}.json"

            if file_path.exists():
                file_path.unlink()
                logger.info(f"Graph deleted: {graph_name}")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to delete graph: {e}")
            return False

    def list_graphs(self) -> List[str]:
        """List all saved graphs."""
        try:
            graphs = []

            for file_path in self.storage_dir.glob("*.json"):
                graphs.append(file_path.stem)

            return sorted(graphs)

        except Exception as e:
            logger.error(f"Failed to list graphs: {e}")
            return []

    def get_graph_info(self, graph_name: str) -> Optional[Dict[str, Any]]:
        """Get graph metadata."""
        try:
            file_path = self.storage_dir / f"{graph_name}.json"

            if not file_path.exists():
                return None

            with open(file_path, "r") as f:
                data = json.load(f)

            # Get file stats
            stat = file_path.stat()

            return {
                "name": data.get("name"),
                "description": data.get("description"),
                "version": data.get("version"),
                "size_bytes": stat.st_size,
                "modified": stat.st_mtime,
                "node_count": len(data.get("graph", {}).get("nodes", [])),
                "edge_count": len(data.get("graph", {}).get("edges", [])),
            }

        except Exception as e:
            logger.error(f"Failed to get graph info: {e}")
            return None

    def export_graph(
        self,
        graph_name: str,
        export_path: Path,
    ) -> bool:
        """
        Export graph to external file.
        
        Args:
            graph_name: Name of graph
            export_path: Path to export to
            
        Returns:
            True if successful
        """
        try:
            file_path = self.storage_dir / f"{graph_name}.json"

            if not file_path.exists():
                return False

            with open(file_path, "r") as src:
                data = json.load(src)

            with open(export_path, "w") as dst:
                json.dump(data, dst, indent=2)

            logger.info(f"Graph exported: {graph_name} -> {export_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export graph: {e}")
            return False

    def import_graph(
        self,
        import_path: Path,
        graph_name: Optional[str] = None,
    ) -> bool:
        """
        Import graph from external file.
        
        Args:
            import_path: Path to import from
            graph_name: Name for imported graph
            
        Returns:
            True if successful
        """
        try:
            if not import_path.exists():
                return False

            with open(import_path, "r") as f:
                data = json.load(f)

            # Use provided name or extract from data
            name = graph_name or data.get("name", import_path.stem)

            # Save to storage
            file_path = self.storage_dir / f"{name}.json"

            with open(file_path, "w") as f:
                json.dump(data, f, indent=2)

            logger.info(f"Graph imported: {import_path} -> {name}")
            return True

        except Exception as e:
            logger.error(f"Failed to import graph: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get persistence statistics."""
        graphs = self.list_graphs()

        total_size = 0
        total_nodes = 0
        total_edges = 0

        for graph_name in graphs:
            info = self.get_graph_info(graph_name)
            if info:
                total_size += info.get("size_bytes", 0)
                total_nodes += info.get("node_count", 0)
                total_edges += info.get("edge_count", 0)

        return {
            "total_graphs": len(graphs),
            "total_size_bytes": total_size,
            "total_nodes": total_nodes,
            "total_edges": total_edges,
            "storage_dir": str(self.storage_dir),
        }
