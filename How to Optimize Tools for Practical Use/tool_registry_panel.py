"""
Tool Registry Panel for SB Toolsmith Pro

Displays and manages registered tools.
"""

from typing import List, Optional, Callable

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QComboBox,
    QTableWidget, QTableWidgetItem, QPushButton, QHeaderView,
    QAbstractItemView, QLabel, QSpinBox, QDialog, QFormLayout,
)


class ToolRegistryPanel(QWidget):
    """Panel for managing tool registry."""

    tool_selected = Signal(str)  # tool_key
    install_requested = Signal(str)  # tool_key
    run_requested = Signal(str)  # tool_key
    remove_requested = Signal(str)  # tool_key
    edit_requested = Signal(str)  # tool_key

    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize tool registry panel."""
        super().__init__(parent)
        self._init_ui()
        self._tools = {}

    def _init_ui(self) -> None:
        """Initialize UI."""
        layout = QVBoxLayout()

        # Search and filter
        search_layout = QHBoxLayout()

        search_label = QLabel("Search:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter by tool name...")
        self.search_input.textChanged.connect(self._on_search_changed)

        sort_label = QLabel("Sort by:")
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Name (A-Z)", "Status", "Recently Updated"])
        self.sort_combo.currentTextChanged.connect(self._on_sort_changed)

        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(sort_label)
        search_layout.addWidget(self.sort_combo)
        search_layout.addStretch()

        layout.addLayout(search_layout)

        # Tool table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Tool", "Status", "Backend", "Last Run", "Size", "Actions"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)

        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)

        layout.addWidget(self.table)

        # Action buttons
        button_layout = QHBoxLayout()

        self.add_btn = QPushButton("+ Add Tool")
        self.add_btn.clicked.connect(self._on_add_tool)
        button_layout.addWidget(self.add_btn)

        self.install_btn = QPushButton("Install")
        self.install_btn.clicked.connect(self._on_install)
        self.install_btn.setEnabled(False)
        button_layout.addWidget(self.install_btn)

        self.run_btn = QPushButton("Run")
        self.run_btn.clicked.connect(self._on_run)
        self.run_btn.setEnabled(False)
        button_layout.addWidget(self.run_btn)

        self.edit_btn = QPushButton("Edit")
        self.edit_btn.clicked.connect(self._on_edit)
        self.edit_btn.setEnabled(False)
        button_layout.addWidget(self.edit_btn)

        self.remove_btn = QPushButton("Remove")
        self.remove_btn.clicked.connect(self._on_remove)
        self.remove_btn.setEnabled(False)
        button_layout.addWidget(self.remove_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def add_tool(
        self,
        tool_key: str,
        name: str,
        status: str,
        backend: str,
        last_run: str,
        size_mb: float,
    ) -> None:
        """
        Add tool to registry.
        
        Args:
            tool_key: Unique tool identifier
            name: Tool name
            status: Installation status (installed/not-installed/error)
            backend: Package manager (pip/poetry/uv)
            last_run: Last run time
            size_mb: Tool size in MB
        """
        row = self.table.rowCount()
        self.table.insertRow(row)

        # Tool name
        name_item = QTableWidgetItem(name)
        name_item.setData(Qt.UserRole, tool_key)
        self.table.setItem(row, 0, name_item)

        # Status
        status_item = QTableWidgetItem(status)
        if status == "installed":
            status_item.setBackground(Qt.green)
        elif status == "error":
            status_item.setBackground(Qt.red)
        self.table.setItem(row, 1, status_item)

        # Backend
        backend_item = QTableWidgetItem(backend)
        self.table.setItem(row, 2, backend_item)

        # Last run
        last_run_item = QTableWidgetItem(last_run)
        self.table.setItem(row, 3, last_run_item)

        # Size
        size_item = QTableWidgetItem(f"{size_mb:.1f} MB")
        self.table.setItem(row, 4, size_item)

        # Actions
        actions_widget = QWidget()
        actions_layout = QHBoxLayout()
        actions_layout.setContentsMargins(0, 0, 0, 0)

        view_btn = QPushButton("View")
        view_btn.clicked.connect(lambda: self._on_view_tool(tool_key))
        actions_layout.addWidget(view_btn)

        actions_widget.setLayout(actions_layout)
        self.table.setCellWidget(row, 5, actions_widget)

        self._tools[tool_key] = {
            "name": name,
            "status": status,
            "backend": backend,
            "last_run": last_run,
            "size_mb": size_mb,
        }

    def update_tool_status(self, tool_key: str, status: str) -> None:
        """Update tool status."""
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.data(Qt.UserRole) == tool_key:
                status_item = self.table.item(row, 1)
                status_item.setText(status)
                if status == "installed":
                    status_item.setBackground(Qt.green)
                elif status == "error":
                    status_item.setBackground(Qt.red)
                break

    def get_selected_tool(self) -> Optional[str]:
        """Get selected tool key."""
        selected = self.table.selectedItems()
        if selected:
            return selected[0].data(Qt.UserRole)
        return None

    def _on_search_changed(self, text: str) -> None:
        """Handle search input change."""
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item:
                visible = text.lower() in item.text().lower()
                self.table.setRowHidden(row, not visible)

    def _on_sort_changed(self, sort_type: str) -> None:
        """Handle sort change."""
        # TODO: Implement sorting
        pass

    def _on_selection_changed(self) -> None:
        """Handle tool selection."""
        tool_key = self.get_selected_tool()
        if tool_key:
            self.install_btn.setEnabled(True)
            self.run_btn.setEnabled(True)
            self.edit_btn.setEnabled(True)
            self.remove_btn.setEnabled(True)
            self.tool_selected.emit(tool_key)
        else:
            self.install_btn.setEnabled(False)
            self.run_btn.setEnabled(False)
            self.edit_btn.setEnabled(False)
            self.remove_btn.setEnabled(False)

    def _on_add_tool(self) -> None:
        """Handle add tool."""
        # TODO: Show add tool dialog
        pass

    def _on_install(self) -> None:
        """Handle install."""
        tool_key = self.get_selected_tool()
        if tool_key:
            self.install_requested.emit(tool_key)

    def _on_run(self) -> None:
        """Handle run."""
        tool_key = self.get_selected_tool()
        if tool_key:
            self.run_requested.emit(tool_key)

    def _on_edit(self) -> None:
        """Handle edit."""
        tool_key = self.get_selected_tool()
        if tool_key:
            self.edit_requested.emit(tool_key)

    def _on_remove(self) -> None:
        """Handle remove."""
        tool_key = self.get_selected_tool()
        if tool_key:
            self.remove_requested.emit(tool_key)

    def _on_view_tool(self, tool_key: str) -> None:
        """Handle view tool."""
        self.tool_selected.emit(tool_key)
