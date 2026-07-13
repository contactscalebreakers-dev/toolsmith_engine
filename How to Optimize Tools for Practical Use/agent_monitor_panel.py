"""
Agent Monitor Panel for SB Toolsmith Pro

Displays agent activity and decision traces.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QLabel, QPushButton, QTabWidget, QPlainTextEdit, QHeaderView,
)


class AgentMonitorPanel(QWidget):
    """Panel for monitoring agent activity."""

    agent_selected = Signal(str)  # agent_id

    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize agent monitor panel."""
        super().__init__(parent)
        self._init_ui()
        self._agents = {}
        self._executions = {}

    def _init_ui(self) -> None:
        """Initialize UI."""
        layout = QVBoxLayout()

        # Title
        title = QLabel("Agent Monitor")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Tabs
        self.tabs = QTabWidget()

        # Activity tab
        self.activity_tree = QTreeWidget()
        self.activity_tree.setHeaderLabels(["Agent", "Status", "Duration", "Result"])
        self.activity_tree.itemSelectionChanged.connect(self._on_agent_selected)
        self.tabs.addTab(self.activity_tree, "Activity")

        # Decisions tab
        self.decisions_tree = QTreeWidget()
        self.decisions_tree.setHeaderLabels(["Time", "Agent", "Decision", "Confidence"])
        self.tabs.addTab(self.decisions_tree, "Decisions")

        # Execution details tab
        self.details_text = QPlainTextEdit()
        self.details_text.setReadOnly(True)
        self.tabs.addTab(self.details_text, "Details")

        layout.addWidget(self.tabs)

        # Control buttons
        button_layout = QHBoxLayout()

        self.clear_btn = QPushButton("Clear History")
        self.clear_btn.clicked.connect(self._clear_history)
        button_layout.addWidget(self.clear_btn)

        self.export_btn = QPushButton("Export Log")
        self.export_btn.clicked.connect(self._export_log)
        button_layout.addWidget(self.export_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def add_agent_execution(
        self,
        agent_id: str,
        agent_type: str,
        status: str,
        duration: float,
        result: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add agent execution record.
        
        Args:
            agent_id: Agent identifier
            agent_type: Agent type (planner, installer, etc.)
            status: Execution status (completed, failed, etc.)
            duration: Execution duration in seconds
            result: Execution result data
        """
        # Create tree item
        item = QTreeWidgetItem()
        item.setText(0, f"{agent_type} ({agent_id})")
        item.setText(1, status)
        item.setText(2, f"{duration:.2f}s")
        item.setText(3, "View" if result else "-")
        item.setData(0, Qt.UserRole, agent_id)

        # Color by status
        if status == "completed":
            item.setBackground(1, QColor(144, 238, 144))  # Light green
        elif status == "failed":
            item.setBackground(1, QColor(255, 127, 127))  # Light red
        elif status == "running":
            item.setBackground(1, QColor(255, 255, 153))  # Light yellow

        self.activity_tree.addTopLevelItem(item)

        # Store execution data
        self._executions[agent_id] = {
            "type": agent_type,
            "status": status,
            "duration": duration,
            "result": result,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def add_agent_decision(
        self,
        agent_id: str,
        decision: str,
        reasoning: str,
        confidence: float,
    ) -> None:
        """
        Add agent decision record.
        
        Args:
            agent_id: Agent identifier
            decision: Decision type
            reasoning: Decision reasoning
            confidence: Confidence level (0-1)
        """
        item = QTreeWidgetItem()
        item.setText(0, datetime.utcnow().strftime("%H:%M:%S"))
        item.setText(1, agent_id)
        item.setText(2, decision)
        item.setText(3, f"{confidence:.0%}")

        # Color by confidence
        if confidence >= 0.9:
            item.setBackground(3, QColor(144, 238, 144))  # Green
        elif confidence >= 0.7:
            item.setBackground(3, QColor(255, 255, 153))  # Yellow
        else:
            item.setBackground(3, QColor(255, 127, 127))  # Red

        self.decisions_tree.addTopLevelItem(item)

        # Store decision
        if agent_id not in self._agents:
            self._agents[agent_id] = []

        self._agents[agent_id].append({
            "decision": decision,
            "reasoning": reasoning,
            "confidence": confidence,
            "timestamp": datetime.utcnow().isoformat(),
        })

    def _on_agent_selected(self) -> None:
        """Handle agent selection."""
        selected = self.activity_tree.selectedItems()
        if selected:
            agent_id = selected[0].data(0, Qt.UserRole)
            if agent_id:
                self.agent_selected.emit(agent_id)
                self._show_execution_details(agent_id)

    def _show_execution_details(self, agent_id: str) -> None:
        """Show execution details."""
        execution = self._executions.get(agent_id)
        if not execution:
            self.details_text.setPlainText("No details available")
            return

        details = f"""
Agent: {agent_id}
Type: {execution['type']}
Status: {execution['status']}
Duration: {execution['duration']:.2f}s
Timestamp: {execution['timestamp']}

Result:
{self._format_result(execution.get('result'))}
"""
        self.details_text.setPlainText(details)

    def _format_result(self, result: Optional[Dict[str, Any]]) -> str:
        """Format result for display."""
        if not result:
            return "No result"

        lines = []
        for key, value in result.items():
            if isinstance(value, dict):
                lines.append(f"{key}:")
                for k, v in value.items():
                    lines.append(f"  {k}: {v}")
            elif isinstance(value, list):
                lines.append(f"{key}: {len(value)} items")
            else:
                lines.append(f"{key}: {value}")

        return "\n".join(lines)

    def _clear_history(self) -> None:
        """Clear history."""
        self.activity_tree.clear()
        self.decisions_tree.clear()
        self.details_text.clear()
        self._agents.clear()
        self._executions.clear()

    def _export_log(self) -> None:
        """Export log to file."""
        # TODO: Implement log export
        pass

    def get_agent_count(self) -> int:
        """Get number of monitored agents."""
        return len(self._agents)

    def get_execution_count(self) -> int:
        """Get number of recorded executions."""
        return len(self._executions)
