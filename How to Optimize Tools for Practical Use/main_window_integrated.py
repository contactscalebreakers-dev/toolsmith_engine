"""
Integrated Main Window for SB Toolsmith Pro

Complete application window with all components.
"""

import logging
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QDockWidget,
    QMenuBar,
    QMenu,
    QStatusBar,
    QMessageBox,
    QFileDialog,
)
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QIcon, QAction, QKeySequence

from .graph_editor import GraphEditorWidget
from .execution_visualizer import ExecutionVisualizer
from .terminal_widget import TerminalWidget
from .tool_registry_panel import ToolRegistryPanel
from .agent_monitor_panel import AgentMonitorPanel
from .diagnostics_panel import DiagnosticsPanel
from .ai_config_dialog import AIConfigDialog
from .graph_persistence import GraphPersistence

logger = logging.getLogger(__name__)


class MainWindowIntegrated(QMainWindow):
    """Integrated main window for SB Toolsmith Pro."""

    tool_executed = Signal(str)  # tool_name
    graph_executed = Signal(dict)  # graph_data
    settings_changed = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize main window.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        self.setWindowTitle("SB Toolsmith Pro")
        self.setWindowIconText("SB Toolsmith Pro")
        self.resize(1400, 900)

        # Initialize components
        self.graph_editor = GraphEditorWidget()
        self.execution_visualizer = ExecutionVisualizer(self.graph_editor)
        self.terminal = TerminalWidget()
        self.tool_registry = ToolRegistryPanel()
        self.agent_monitor = AgentMonitorPanel()
        self.diagnostics = DiagnosticsPanel()
        self.graph_persistence = GraphPersistence()

        # Setup UI
        self._setup_central_widget()
        self._setup_menu_bar()
        self._setup_dock_widgets()
        self._setup_status_bar()
        self._setup_connections()

        # Apply dark theme
        self._apply_dark_theme()

        logger.info("Main window initialized")

    def _setup_central_widget(self) -> None:
        """Setup central widget."""
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)

        # Add graph editor and execution visualizer
        layout.addWidget(self.graph_editor)
        layout.addWidget(self.execution_visualizer)

        self.setCentralWidget(central_widget)

    def _setup_menu_bar(self) -> None:
        """Setup menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        new_graph_action = QAction("&New Graph", self)
        new_graph_action.setShortcut(QKeySequence.New)
        new_graph_action.triggered.connect(self._new_graph)
        file_menu.addAction(new_graph_action)

        open_graph_action = QAction("&Open Graph", self)
        open_graph_action.setShortcut(QKeySequence.Open)
        open_graph_action.triggered.connect(self._open_graph)
        file_menu.addAction(open_graph_action)

        save_graph_action = QAction("&Save Graph", self)
        save_graph_action.setShortcut(QKeySequence.Save)
        save_graph_action.triggered.connect(self._save_graph)
        file_menu.addAction(save_graph_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit menu
        edit_menu = menubar.addMenu("&Edit")

        clear_graph_action = QAction("&Clear Graph", self)
        clear_graph_action.triggered.connect(self.graph_editor._clear_graph)
        edit_menu.addAction(clear_graph_action)

        # Execution menu
        exec_menu = menubar.addMenu("&Execution")

        run_action = QAction("&Run Graph", self)
        run_action.setShortcut(Qt.CTRL | Qt.Key_R)
        run_action.triggered.connect(self._run_graph)
        exec_menu.addAction(run_action)

        stop_action = QAction("&Stop Execution", self)
        stop_action.setShortcut(Qt.CTRL | Qt.SHIFT | Qt.Key_S)
        stop_action.triggered.connect(self._stop_execution)
        exec_menu.addAction(stop_action)

        # Tools menu
        tools_menu = menubar.addMenu("&Tools")

        register_tool_action = QAction("&Register Tool", self)
        register_tool_action.triggered.connect(self._register_tool)
        tools_menu.addAction(register_tool_action)

        diagnostics_action = QAction("&Diagnostics", self)
        diagnostics_action.triggered.connect(self._show_diagnostics)
        tools_menu.addAction(diagnostics_action)

        # Settings menu
        settings_menu = menubar.addMenu("&Settings")

        ai_config_action = QAction("&AI Configuration", self)
        ai_config_action.triggered.connect(self._show_ai_config)
        settings_menu.addAction(ai_config_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_dock_widgets(self) -> None:
        """Setup dock widgets."""
        # Terminal dock
        terminal_dock = QDockWidget("Terminal", self)
        terminal_dock.setWidget(self.terminal)
        self.addDockWidget(Qt.BottomDockWidgetArea, terminal_dock)

        # Tool registry dock
        registry_dock = QDockWidget("Tool Registry", self)
        registry_dock.setWidget(self.tool_registry)
        self.addDockWidget(Qt.RightDockWidgetArea, registry_dock)

        # Agent monitor dock
        monitor_dock = QDockWidget("Agent Monitor", self)
        monitor_dock.setWidget(self.agent_monitor)
        self.addDockWidget(Qt.RightDockWidgetArea, monitor_dock)

        # Diagnostics dock
        diagnostics_dock = QDockWidget("Diagnostics", self)
        diagnostics_dock.setWidget(self.diagnostics)
        self.addDockWidget(Qt.RightDockWidgetArea, diagnostics_dock)

        # Tab the right dock widgets
        self.tabifyDockWidget(registry_dock, monitor_dock)
        self.tabifyDockWidget(monitor_dock, diagnostics_dock)

    def _setup_status_bar(self) -> None:
        """Setup status bar."""
        self.statusBar().showMessage("Ready")

    def _setup_connections(self) -> None:
        """Setup signal connections."""
        self.graph_editor.graph_changed.connect(self._on_graph_changed)
        self.tool_registry.tool_selected.connect(self._on_tool_selected)

    def _apply_dark_theme(self) -> None:
        """Apply dark theme."""
        dark_stylesheet = """
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QMenuBar {
                background-color: #2b2b2b;
                color: #ffffff;
                border-bottom: 1px solid #3d3d3d;
            }
            QMenuBar::item:selected {
                background-color: #3d3d3d;
            }
            QMenu {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #3d3d3d;
            }
            QMenu::item:selected {
                background-color: #3d3d3d;
            }
            QDockWidget {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #3d3d3d;
            }
            QDockWidget::title {
                background-color: #3d3d3d;
                padding: 4px;
            }
            QStatusBar {
                background-color: #2b2b2b;
                color: #ffffff;
                border-top: 1px solid #3d3d3d;
            }
        """
        self.setStyleSheet(dark_stylesheet)

    def _new_graph(self) -> None:
        """Create new graph."""
        self.graph_editor._clear_graph()
        self.statusBar().showMessage("New graph created")
        logger.info("New graph created")

    def _open_graph(self) -> None:
        """Open graph from file."""
        graphs = self.graph_persistence.list_graphs()

        if not graphs:
            QMessageBox.information(self, "No Graphs", "No saved graphs found.")
            return

        # Simple selection dialog
        from PySide6.QtWidgets import QInputDialog

        graph_name, ok = QInputDialog.getItem(
            self,
            "Open Graph",
            "Select graph:",
            graphs,
            0,
            False,
        )

        if ok and graph_name:
            graph_data = self.graph_persistence.load_graph(graph_name)
            if graph_data:
                self.graph_editor.load_graph(graph_data)
                self.statusBar().showMessage(f"Graph loaded: {graph_name}")
                logger.info(f"Graph loaded: {graph_name}")
            else:
                QMessageBox.warning(self, "Error", "Failed to load graph.")

    def _save_graph(self) -> None:
        """Save graph to file."""
        from PySide6.QtWidgets import QInputDialog

        graph_name, ok = QInputDialog.getText(
            self,
            "Save Graph",
            "Graph name:",
        )

        if ok and graph_name:
            graph_data = self.graph_editor.get_graph()
            if self.graph_persistence.save_graph(graph_name, graph_data):
                self.statusBar().showMessage(f"Graph saved: {graph_name}")
                logger.info(f"Graph saved: {graph_name}")
            else:
                QMessageBox.warning(self, "Error", "Failed to save graph.")

    def _run_graph(self) -> None:
        """Run graph execution."""
        graph_data = self.graph_editor.get_graph()

        if not graph_data.get("nodes"):
            QMessageBox.warning(self, "Empty Graph", "Graph has no nodes.")
            return

        self.execution_visualizer.start_execution()
        self.statusBar().showMessage("Executing graph...")
        self.graph_executed.emit(graph_data)

        logger.info("Graph execution started")

    def _stop_execution(self) -> None:
        """Stop graph execution."""
        self.execution_visualizer.end_execution(success=False)
        self.statusBar().showMessage("Execution stopped")
        logger.info("Graph execution stopped")

    def _register_tool(self) -> None:
        """Register new tool."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Tool File",
            "",
            "Python Files (*.py);;Archives (*.zip *.tar.gz);;All Files (*)",
        )

        if file_path:
            self.tool_registry.add_tool(file_path)
            self.statusBar().showMessage(f"Tool registered: {file_path}")
            logger.info(f"Tool registered: {file_path}")

    def _show_diagnostics(self) -> None:
        """Show diagnostics panel."""
        # Bring diagnostics dock to front
        for dock in self.findChildren(QDockWidget):
            if "Diagnostics" in dock.windowTitle():
                dock.raise_()
                dock.show()
                break

    def _show_ai_config(self) -> None:
        """Show AI configuration dialog."""
        dialog = AIConfigDialog(self)
        if dialog.exec():
            self.settings_changed.emit()
            self.statusBar().showMessage("AI configuration updated")
            logger.info("AI configuration updated")

    def _show_about(self) -> None:
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About SB Toolsmith Pro",
            "SB Toolsmith Pro v1.0\n\n"
            "AI-native execution operating system\n"
            "for Python tool orchestration.\n\n"
            "© 2024 SB Toolsmith",
        )

    def _on_graph_changed(self) -> None:
        """Handle graph change."""
        stats = self.graph_editor.get_stats()
        self.statusBar().showMessage(
            f"Nodes: {stats['total_nodes']} | Edges: {stats['total_edges']}"
        )

    def _on_tool_selected(self, tool_name: str) -> None:
        """Handle tool selection."""
        self.statusBar().showMessage(f"Selected tool: {tool_name}")
        self.tool_executed.emit(tool_name)

    def closeEvent(self, event) -> None:
        """Handle window close."""
        reply = QMessageBox.question(
            self,
            "Exit",
            "Are you sure you want to exit?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            logger.info("Application closing")
            event.accept()
        else:
            event.ignore()

    def get_stats(self) -> dict:
        """Get application statistics."""
        return {
            "graph_editor": self.graph_editor.get_stats(),
            "execution_visualizer": self.execution_visualizer.get_stats(),
            "terminal": self.terminal.get_stats() if hasattr(self.terminal, 'get_stats') else {},
            "tool_registry": self.tool_registry.get_stats() if hasattr(self.tool_registry, 'get_stats') else {},
        }
