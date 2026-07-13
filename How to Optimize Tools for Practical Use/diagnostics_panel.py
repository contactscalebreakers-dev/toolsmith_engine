"""
Diagnostics Panel for SB Toolsmith Pro

Displays tool health and diagnostic information.
"""

from typing import Optional, Dict, Any, List

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar,
    QTreeWidget, QTreeWidgetItem, QGroupBox, QScrollArea,
)


class DiagnosticsPanel(QWidget):
    """Panel for displaying tool diagnostics."""

    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize diagnostics panel."""
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize UI."""
        layout = QVBoxLayout()

        # Title
        title = QLabel("Diagnostics")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()

        # Health status
        health_group = QGroupBox("Health Status")
        health_layout = QVBoxLayout()

        self.health_bar = QProgressBar()
        self.health_bar.setRange(0, 100)
        self.health_bar.setValue(100)
        health_layout.addWidget(QLabel("Overall Health:"))
        health_layout.addWidget(self.health_bar)

        self.health_label = QLabel("Healthy")
        self.health_label.setStyleSheet("color: green; font-weight: bold;")
        health_layout.addWidget(self.health_label)

        health_group.setLayout(health_layout)
        scroll_layout.addWidget(health_group)

        # Dependencies
        deps_group = QGroupBox("Dependencies")
        deps_layout = QVBoxLayout()

        self.deps_tree = QTreeWidget()
        self.deps_tree.setHeaderLabels(["Package", "Version", "Status"])
        self.deps_tree.setMaximumHeight(150)
        deps_layout.addWidget(self.deps_tree)

        deps_group.setLayout(deps_layout)
        scroll_layout.addWidget(deps_group)

        # Environment
        env_group = QGroupBox("Environment")
        env_layout = QVBoxLayout()

        self.env_tree = QTreeWidget()
        self.env_tree.setHeaderLabels(["Variable", "Value"])
        self.env_tree.setMaximumHeight(150)
        env_layout.addWidget(self.env_tree)

        env_group.setLayout(env_layout)
        scroll_layout.addWidget(env_group)

        # Issues
        issues_group = QGroupBox("Issues")
        issues_layout = QVBoxLayout()

        self.issues_tree = QTreeWidget()
        self.issues_tree.setHeaderLabels(["Severity", "Issue", "Suggestion"])
        self.issues_tree.setMaximumHeight(150)
        issues_layout.addWidget(self.issues_tree)

        issues_group.setLayout(issues_layout)
        scroll_layout.addWidget(issues_group)

        scroll_layout.addStretch()
        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)

        layout.addWidget(scroll)
        self.setLayout(layout)

    def set_health_status(self, health_percent: int, status: str) -> None:
        """
        Set health status.
        
        Args:
            health_percent: Health percentage (0-100)
            status: Status text
        """
        self.health_bar.setValue(health_percent)
        self.health_label.setText(status)

        if health_percent >= 80:
            self.health_label.setStyleSheet("color: green; font-weight: bold;")
        elif health_percent >= 50:
            self.health_label.setStyleSheet("color: orange; font-weight: bold;")
        else:
            self.health_label.setStyleSheet("color: red; font-weight: bold;")

    def add_dependency(
        self,
        package: str,
        version: str,
        status: str,
    ) -> None:
        """
        Add dependency to list.
        
        Args:
            package: Package name
            version: Package version
            status: Installation status
        """
        item = QTreeWidgetItem()
        item.setText(0, package)
        item.setText(1, version)
        item.setText(2, status)

        if status == "installed":
            item.setBackground(2, QColor(144, 238, 144))  # Green
        elif status == "missing":
            item.setBackground(2, QColor(255, 127, 127))  # Red
        elif status == "outdated":
            item.setBackground(2, QColor(255, 255, 153))  # Yellow

        self.deps_tree.addTopLevelItem(item)

    def add_environment_variable(self, name: str, value: str) -> None:
        """Add environment variable."""
        item = QTreeWidgetItem()
        item.setText(0, name)
        item.setText(1, str(value)[:100])  # Truncate long values
        self.env_tree.addTopLevelItem(item)

    def add_issue(
        self,
        severity: str,
        issue: str,
        suggestion: str,
    ) -> None:
        """
        Add issue to list.
        
        Args:
            severity: Issue severity (critical, high, medium, low)
            issue: Issue description
            suggestion: Suggested fix
        """
        item = QTreeWidgetItem()
        item.setText(0, severity)
        item.setText(1, issue)
        item.setText(2, suggestion)

        if severity == "critical":
            item.setBackground(0, QColor(255, 0, 0))
        elif severity == "high":
            item.setBackground(0, QColor(255, 127, 0))
        elif severity == "medium":
            item.setBackground(0, QColor(255, 255, 0))
        else:
            item.setBackground(0, QColor(144, 238, 144))

        self.issues_tree.addTopLevelItem(item)

    def clear_all(self) -> None:
        """Clear all diagnostics."""
        self.deps_tree.clear()
        self.env_tree.clear()
        self.issues_tree.clear()
        self.health_bar.setValue(100)
        self.health_label.setText("Healthy")
        self.health_label.setStyleSheet("color: green; font-weight: bold;")

    def get_issue_count(self) -> int:
        """Get number of issues."""
        return self.issues_tree.topLevelItemCount()

    def get_critical_issue_count(self) -> int:
        """Get number of critical issues."""
        count = 0
        for i in range(self.issues_tree.topLevelItemCount()):
            item = self.issues_tree.topLevelItem(i)
            if item and item.text(0) == "critical":
                count += 1
        return count
