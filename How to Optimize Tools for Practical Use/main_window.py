"""
Main Application Window for SB Toolsmith Pro

Windows 11 native dark-mode UI with docking system, terminal, and agent monitor.
"""

import sys
import logging
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QMenuBar,
    QMenu,
    QStatusBar,
    QDockWidget,
    QLabel,
    QSplitter,
)
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QIcon, QAction, QKeySequence

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    Main application window with docking system and integrated panels.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize main window.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.setWindowTitle("SB Toolsmith Pro")
        self.setWindowIcon(QIcon("resources/icon.png"))
        self.resize(1400, 900)
        
        # Set dark theme stylesheet
        self._apply_dark_theme()
        
        # Create UI
        self._create_menu_bar()
        self._create_central_widget()
        self._create_dock_widgets()
        self._create_status_bar()
        
        # Restore window state if available
        self._restore_window_state()
        
        logger.info("Main window initialized")

    def _apply_dark_theme(self) -> None:
        """Apply Windows 11 dark theme stylesheet."""
        stylesheet = """
        QMainWindow {
            background-color: #1e1e1e;
            color: #ffffff;
        }
        QMenuBar {
            background-color: #2d2d2d;
            color: #ffffff;
            border-bottom: 1px solid #3d3d3d;
        }
        QMenuBar::item:selected {
            background-color: #3d3d3d;
        }
        QMenu {
            background-color: #2d2d2d;
            color: #ffffff;
            border: 1px solid #3d3d3d;
        }
        QMenu::item:selected {
            background-color: #0078d4;
        }
        QDockWidget {
            background-color: #1e1e1e;
            color: #ffffff;
            border: 1px solid #3d3d3d;
        }
        QDockWidget::title {
            background-color: #2d2d2d;
            padding: 4px;
            border-bottom: 1px solid #3d3d3d;
        }
        QStatusBar {
            background-color: #2d2d2d;
            color: #ffffff;
            border-top: 1px solid #3d3d3d;
        }
        QLabel {
            color: #ffffff;
        }
        QPushButton {
            background-color: #0078d4;
            color: #ffffff;
            border: none;
            border-radius: 4px;
            padding: 6px 12px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #1084d7;
        }
        QPushButton:pressed {
            background-color: #006acc;
        }
        QLineEdit, QTextEdit, QPlainTextEdit {
            background-color: #252526;
            color: #ffffff;
            border: 1px solid #3d3d3d;
            border-radius: 4px;
            padding: 4px;
        }
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
            border: 1px solid #0078d4;
        }
        QComboBox {
            background-color: #252526;
            color: #ffffff;
            border: 1px solid #3d3d3d;
            border-radius: 4px;
            padding: 4px;
        }
        QComboBox::drop-down {
            border: none;
        }
        QComboBox::down-arrow {
            image: url(resources/arrow-down.png);
        }
        """
        self.setStyleSheet(stylesheet)

    def _create_menu_bar(self) -> None:
        """Create application menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        new_action = QAction("&New Tool", self)
        new_action.setShortcut(QKeySequence.New)
        new_action.triggered.connect(self._on_new_tool)
        file_menu.addAction(new_action)
        
        open_action = QAction("&Open", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self._on_open)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        
        undo_action = QAction("&Undo", self)
        undo_action.setShortcut(QKeySequence.Undo)
        edit_menu.addAction(undo_action)
        
        redo_action = QAction("&Redo", self)
        redo_action.setShortcut(QKeySequence.Redo)
        edit_menu.addAction(redo_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        
        install_action = QAction("&Install Dependencies", self)
        install_action.triggered.connect(self._on_install)
        tools_menu.addAction(install_action)
        
        run_action = QAction("&Run Tool", self)
        run_action.setShortcut(Qt.CTRL | Qt.Key_R)
        run_action.triggered.connect(self._on_run)
        tools_menu.addAction(run_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)

    def _create_central_widget(self) -> None:
        """Create central widget with main content area."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Main content area (placeholder)
        content_label = QLabel("Welcome to SB Toolsmith Pro")
        content_label.setStyleSheet("font-size: 24px; font-weight: bold; padding: 20px;")
        layout.addWidget(content_label)
        
        central_widget.setLayout(layout)

    def _create_dock_widgets(self) -> None:
        """Create dockable panels."""
        # Tool Registry Panel
        registry_dock = QDockWidget("Tool Registry", self)
        registry_widget = QWidget()
        registry_layout = QVBoxLayout()
        registry_layout.addWidget(QLabel("Tools will appear here"))
        registry_widget.setLayout(registry_layout)
        registry_dock.setWidget(registry_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, registry_dock)
        
        # Terminal Panel
        terminal_dock = QDockWidget("Terminal", self)
        terminal_widget = QWidget()
        terminal_layout = QVBoxLayout()
        terminal_layout.addWidget(QLabel("Terminal output will appear here"))
        terminal_widget.setLayout(terminal_layout)
        terminal_dock.setWidget(terminal_widget)
        self.addDockWidget(Qt.BottomDockWidgetArea, terminal_dock)
        
        # Agent Monitor Panel
        agent_dock = QDockWidget("Agent Monitor", self)
        agent_widget = QWidget()
        agent_layout = QVBoxLayout()
        agent_layout.addWidget(QLabel("Agent activity will appear here"))
        agent_widget.setLayout(agent_layout)
        agent_dock.setWidget(agent_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, agent_dock)

    def _create_status_bar(self) -> None:
        """Create status bar."""
        status_bar = self.statusBar()
        status_bar.showMessage("Ready")

    def _restore_window_state(self) -> None:
        """Restore window state from settings."""
        # TODO: Implement window state restoration from database
        pass

    # Menu action handlers
    def _on_new_tool(self) -> None:
        """Handle new tool action."""
        logger.info("New tool action triggered")

    def _on_open(self) -> None:
        """Handle open action."""
        logger.info("Open action triggered")

    def _on_install(self) -> None:
        """Handle install action."""
        logger.info("Install action triggered")

    def _on_run(self) -> None:
        """Handle run action."""
        logger.info("Run action triggered")

    def _on_about(self) -> None:
        """Handle about action."""
        logger.info("About action triggered")

    def closeEvent(self, event):
        """Handle window close event."""
        logger.info("Main window closing")
        event.accept()


def create_main_window() -> MainWindow:
    """Factory function to create main window."""
    return MainWindow()
