"""
Graph Editor for SB Toolsmith Pro

Visual DAG editor with drag-drop nodes and connections.
"""

import logging
from typing import Optional, Dict, Any, List, Tuple, Set
from dataclasses import dataclass

from PySide6.QtWidgets import (
    QWidget,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsItem,
    QGraphicsEllipseItem,
    QGraphicsLineItem,
    QGraphicsTextItem,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QComboBox,
    QLabel,
)
from PySide6.QtCore import Qt, QPointF, QRectF, Signal, QSize
from PySide6.QtGui import (
    QPen,
    QBrush,
    QColor,
    QFont,
    QPainter,
    QMouseEvent,
)

logger = logging.getLogger(__name__)


@dataclass
class NodePosition:
    """Node position in graph."""

    x: float
    y: float

    def to_tuple(self) -> Tuple[float, float]:
        """Convert to tuple."""
        return (self.x, self.y)


class GraphNode(QGraphicsEllipseItem):
    """Visual representation of DAG node."""

    def __init__(
        self,
        node_id: str,
        label: str,
        x: float = 0,
        y: float = 0,
        radius: float = 30,
    ):
        """
        Initialize graph node.
        
        Args:
            node_id: Unique node identifier
            label: Node label
            x: X position
            y: Y position
            radius: Node radius
        """
        super().__init__(x - radius, y - radius, radius * 2, radius * 2)

        self.node_id = node_id
        self.label = label
        self.radius = radius
        self.connected_edges: Set[str] = set()

        # Set appearance
        self.setBrush(QBrush(QColor(66, 135, 245)))
        self.setPen(QPen(QColor(255, 255, 255), 2))
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)

        # Add label
        self.text_item = QGraphicsTextItem(label, self)
        self.text_item.setDefaultTextColor(QColor(255, 255, 255))
        font = QFont()
        font.setPointSize(9)
        font.setBold(True)
        self.text_item.setFont(font)

        # Center text
        text_rect = self.text_item.boundingRect()
        self.text_item.setPos(
            -text_rect.width() / 2,
            -text_rect.height() / 2,
        )

    def get_center(self) -> QPointF:
        """Get node center position."""
        return self.scenePos() + QPointF(self.radius, self.radius)

    def set_selected(self, selected: bool) -> None:
        """Set selection state."""
        if selected:
            self.setBrush(QBrush(QColor(100, 180, 255)))
            self.setPen(QPen(QColor(255, 255, 0), 3))
        else:
            self.setBrush(QBrush(QColor(66, 135, 245)))
            self.setPen(QPen(QColor(255, 255, 255), 2))

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press."""
        self.set_selected(True)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Handle mouse release."""
        super().mouseReleaseEvent(event)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "node_id": self.node_id,
            "label": self.label,
            "x": self.scenePos().x() + self.radius,
            "y": self.scenePos().y() + self.radius,
            "radius": self.radius,
        }


class GraphEdge(QGraphicsLineItem):
    """Visual representation of DAG edge."""

    def __init__(
        self,
        edge_id: str,
        from_node: GraphNode,
        to_node: GraphNode,
    ):
        """
        Initialize graph edge.
        
        Args:
            edge_id: Unique edge identifier
            from_node: Source node
            to_node: Target node
        """
        super().__init__()

        self.edge_id = edge_id
        self.from_node = from_node
        self.to_node = to_node

        # Set appearance
        self.setPen(QPen(QColor(200, 200, 200), 2))
        self.setAcceptHoverEvents(True)

        self._update_position()

    def _update_position(self) -> None:
        """Update edge position based on nodes."""
        from_pos = self.from_node.get_center()
        to_pos = self.to_node.get_center()
        self.setLine(from_pos.x(), from_pos.y(), to_pos.x(), to_pos.y())

    def paint(self, painter: QPainter, option: Any, widget: Any) -> None:
        """Paint edge with arrow."""
        # Draw line
        super().paint(painter, option, widget)

        # Draw arrow
        from_pos = self.from_node.get_center()
        to_pos = self.to_node.get_center()

        # Calculate arrow
        dx = to_pos.x() - from_pos.x()
        dy = to_pos.y() - from_pos.y()
        length = (dx * dx + dy * dy) ** 0.5

        if length > 0:
            # Normalize
            dx /= length
            dy /= length

            # Arrow position (near target)
            arrow_size = 10
            arrow_x = to_pos.x() - dx * arrow_size
            arrow_y = to_pos.y() - dy * arrow_size

            # Arrow points
            angle = 0.5
            p1_x = arrow_x - dx * arrow_size + dy * arrow_size * angle
            p1_y = arrow_y - dy * arrow_size - dx * arrow_size * angle
            p2_x = arrow_x - dx * arrow_size - dy * arrow_size * angle
            p2_y = arrow_y - dy * arrow_size + dx * arrow_size * angle

            # Draw arrow
            painter.drawLine(int(to_pos.x()), int(to_pos.y()), int(p1_x), int(p1_y))
            painter.drawLine(int(to_pos.x()), int(to_pos.y()), int(p2_x), int(p2_y))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "edge_id": self.edge_id,
            "from_node": self.from_node.node_id,
            "to_node": self.to_node.node_id,
        }


class GraphEditorWidget(QWidget):
    """Graph editor widget."""

    node_added = Signal(str, str)  # node_id, label
    node_removed = Signal(str)  # node_id
    edge_added = Signal(str, str, str)  # edge_id, from_node, to_node
    edge_removed = Signal(str)  # edge_id
    graph_changed = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize graph editor.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        self._nodes: Dict[str, GraphNode] = {}
        self._edges: Dict[str, GraphEdge] = {}
        self._selected_node: Optional[GraphNode] = None
        self._node_counter = 0
        self._edge_counter = 0

        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize UI."""
        layout = QVBoxLayout(self)

        # Toolbar
        toolbar_layout = QHBoxLayout()

        add_node_btn = QPushButton("Add Node")
        add_node_btn.clicked.connect(self._add_node)
        toolbar_layout.addWidget(add_node_btn)

        remove_node_btn = QPushButton("Remove Node")
        remove_node_btn.clicked.connect(self._remove_selected_node)
        toolbar_layout.addWidget(remove_node_btn)

        connect_btn = QPushButton("Connect")
        connect_btn.clicked.connect(self._connect_nodes)
        toolbar_layout.addWidget(connect_btn)

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self._clear_graph)
        toolbar_layout.addWidget(clear_btn)

        layout.addLayout(toolbar_layout)

        # Graph view
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, 800, 600)
        self.scene.setBackgroundBrush(QBrush(QColor(40, 40, 40)))

        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        layout.addWidget(self.view)

        self.setLayout(layout)

    def _add_node(self) -> None:
        """Add new node."""
        node_id = f"node_{self._node_counter}"
        label = f"Node {self._node_counter}"
        self._node_counter += 1

        # Random position
        import random

        x = random.randint(100, 700)
        y = random.randint(100, 500)

        node = GraphNode(node_id, label, x, y)
        self.scene.addItem(node)
        self._nodes[node_id] = node

        self.node_added.emit(node_id, label)
        self.graph_changed.emit()

        logger.info(f"Node added: {node_id}")

    def _remove_selected_node(self) -> None:
        """Remove selected node."""
        if not self._selected_node:
            return

        node_id = self._selected_node.node_id

        # Remove connected edges
        for edge_id in list(self._selected_node.connected_edges):
            self._remove_edge(edge_id)

        # Remove node
        self.scene.removeItem(self._selected_node)
        del self._nodes[node_id]
        self._selected_node = None

        self.node_removed.emit(node_id)
        self.graph_changed.emit()

        logger.info(f"Node removed: {node_id}")

    def _connect_nodes(self) -> None:
        """Connect two selected nodes."""
        selected_nodes = [
            node for node in self._nodes.values()
            if node.isSelected()
        ]

        if len(selected_nodes) != 2:
            logger.warning("Select exactly 2 nodes to connect")
            return

        from_node = selected_nodes[0]
        to_node = selected_nodes[1]

        edge_id = f"edge_{self._edge_counter}"
        self._edge_counter += 1

        edge = GraphEdge(edge_id, from_node, to_node)
        self.scene.addItem(edge)
        self._edges[edge_id] = edge

        from_node.connected_edges.add(edge_id)
        to_node.connected_edges.add(edge_id)

        self.edge_added.emit(edge_id, from_node.node_id, to_node.node_id)
        self.graph_changed.emit()

        logger.info(f"Edge added: {edge_id}")

    def _remove_edge(self, edge_id: str) -> None:
        """Remove edge."""
        if edge_id not in self._edges:
            return

        edge = self._edges[edge_id]
        self.scene.removeItem(edge)
        del self._edges[edge_id]

        edge.from_node.connected_edges.discard(edge_id)
        edge.to_node.connected_edges.discard(edge_id)

        self.edge_removed.emit(edge_id)
        self.graph_changed.emit()

        logger.info(f"Edge removed: {edge_id}")

    def _clear_graph(self) -> None:
        """Clear entire graph."""
        self.scene.clear()
        self._nodes.clear()
        self._edges.clear()
        self._selected_node = None
        self._node_counter = 0
        self._edge_counter = 0

        self.graph_changed.emit()
        logger.info("Graph cleared")

    def get_graph(self) -> Dict[str, Any]:
        """Get graph as dictionary."""
        return {
            "nodes": [node.to_dict() for node in self._nodes.values()],
            "edges": [edge.to_dict() for edge in self._edges.values()],
        }

    def load_graph(self, graph_data: Dict[str, Any]) -> None:
        """Load graph from dictionary."""
        self._clear_graph()

        # Load nodes
        node_map = {}
        for node_data in graph_data.get("nodes", []):
            node_id = node_data["node_id"]
            label = node_data["label"]
            x = node_data["x"]
            y = node_data["y"]

            node = GraphNode(node_id, label, x, y)
            self.scene.addItem(node)
            self._nodes[node_id] = node
            node_map[node_id] = node

        # Load edges
        for edge_data in graph_data.get("edges", []):
            edge_id = edge_data["edge_id"]
            from_node_id = edge_data["from_node"]
            to_node_id = edge_data["to_node"]

            if from_node_id in node_map and to_node_id in node_map:
                edge = GraphEdge(
                    edge_id,
                    node_map[from_node_id],
                    node_map[to_node_id],
                )
                self.scene.addItem(edge)
                self._edges[edge_id] = edge

                node_map[from_node_id].connected_edges.add(edge_id)
                node_map[to_node_id].connected_edges.add(edge_id)

        logger.info(f"Graph loaded: {len(self._nodes)} nodes, {len(self._edges)} edges")

    def get_stats(self) -> Dict[str, Any]:
        """Get editor statistics."""
        return {
            "total_nodes": len(self._nodes),
            "total_edges": len(self._edges),
            "selected_node": self._selected_node.node_id if self._selected_node else None,
        }
