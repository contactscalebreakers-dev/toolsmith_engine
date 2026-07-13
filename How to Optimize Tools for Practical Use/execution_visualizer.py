"""
Execution Visualizer for SB Toolsmith Pro

Real-time execution visualization on graph.
"""

import logging
from typing import Optional, Dict, Any, Set
from enum import Enum

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor

from .graph_editor import GraphEditorWidget, GraphNode

logger = logging.getLogger(__name__)


class NodeExecutionState(Enum):
    """Node execution state."""

    IDLE = "idle"
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"


class ExecutionVisualizer(QWidget):
    """Visualize execution on graph."""

    execution_started = Signal()
    execution_completed = Signal(bool)  # success

    def __init__(self, graph_editor: GraphEditorWidget, parent: Optional[QWidget] = None):
        """
        Initialize execution visualizer.
        
        Args:
            graph_editor: Graph editor widget
            parent: Parent widget
        """
        super().__init__(parent)

        self.graph_editor = graph_editor
        self._node_states: Dict[str, NodeExecutionState] = {}
        self._executing_nodes: Set[str] = set()
        self._completed_nodes: Set[str] = set()
        self._failed_nodes: Set[str] = set()

        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize UI."""
        layout = QVBoxLayout(self)

        # Status label
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Stats label
        self.stats_label = QLabel("Nodes: 0 | Completed: 0 | Failed: 0")
        layout.addWidget(self.stats_label)

        self.setLayout(layout)

    def set_node_state(
        self,
        node_id: str,
        state: NodeExecutionState,
    ) -> None:
        """
        Set node execution state.
        
        Args:
            node_id: Node ID
            state: Execution state
        """
        self._node_states[node_id] = state

        # Update node appearance
        if node_id in self.graph_editor._nodes:
            node = self.graph_editor._nodes[node_id]
            self._update_node_appearance(node, state)

        # Track state
        if state == NodeExecutionState.RUNNING:
            self._executing_nodes.add(node_id)
        elif state == NodeExecutionState.SUCCESS:
            self._executing_nodes.discard(node_id)
            self._completed_nodes.add(node_id)
        elif state == NodeExecutionState.FAILED:
            self._executing_nodes.discard(node_id)
            self._failed_nodes.add(node_id)

        self._update_stats()

    def _update_node_appearance(
        self,
        node: GraphNode,
        state: NodeExecutionState,
    ) -> None:
        """Update node visual appearance."""
        if state == NodeExecutionState.IDLE:
            node.setBrush(QColor(66, 135, 245))
        elif state == NodeExecutionState.PENDING:
            node.setBrush(QColor(200, 200, 0))
        elif state == NodeExecutionState.RUNNING:
            node.setBrush(QColor(0, 200, 255))
        elif state == NodeExecutionState.SUCCESS:
            node.setBrush(QColor(0, 200, 0))
        elif state == NodeExecutionState.FAILED:
            node.setBrush(QColor(255, 0, 0))
        elif state == NodeExecutionState.TIMEOUT:
            node.setBrush(QColor(255, 100, 0))

    def _update_stats(self) -> None:
        """Update statistics display."""
        total_nodes = len(self.graph_editor._nodes)
        completed = len(self._completed_nodes)
        failed = len(self._failed_nodes)

        # Update progress
        if total_nodes > 0:
            progress = int((completed + failed) / total_nodes * 100)
            self.progress_bar.setValue(progress)

        # Update stats label
        self.stats_label.setText(
            f"Nodes: {total_nodes} | Completed: {completed} | Failed: {failed}"
        )

        # Update status
        if self._executing_nodes:
            self.status_label.setText(
                f"Running ({len(self._executing_nodes)} nodes)..."
            )
        elif failed > 0:
            self.status_label.setText(f"Failed ({failed} nodes)")
        elif completed == total_nodes and total_nodes > 0:
            self.status_label.setText("Completed")
        else:
            self.status_label.setText("Ready")

    def start_execution(self) -> None:
        """Start execution visualization."""
        self._executing_nodes.clear()
        self._completed_nodes.clear()
        self._failed_nodes.clear()
        self._node_states.clear()

        # Reset all nodes to pending
        for node_id, node in self.graph_editor._nodes.items():
            self.set_node_state(node_id, NodeExecutionState.PENDING)

        self.execution_started.emit()
        logger.info("Execution visualization started")

    def end_execution(self, success: bool = True) -> None:
        """End execution visualization."""
        self.execution_completed.emit(success)
        logger.info(f"Execution visualization ended: {'success' if success else 'failed'}")

    def reset(self) -> None:
        """Reset visualization."""
        self._node_states.clear()
        self._executing_nodes.clear()
        self._completed_nodes.clear()
        self._failed_nodes.clear()

        # Reset all nodes to idle
        for node in self.graph_editor._nodes.values():
            self._update_node_appearance(node, NodeExecutionState.IDLE)

        self.progress_bar.setValue(0)
        self.status_label.setText("Ready")
        self._update_stats()

    def get_stats(self) -> Dict[str, Any]:
        """Get visualization statistics."""
        return {
            "total_nodes": len(self.graph_editor._nodes),
            "executing_nodes": len(self._executing_nodes),
            "completed_nodes": len(self._completed_nodes),
            "failed_nodes": len(self._failed_nodes),
            "node_states": {
                node_id: state.value
                for node_id, state in self._node_states.items()
            },
        }
