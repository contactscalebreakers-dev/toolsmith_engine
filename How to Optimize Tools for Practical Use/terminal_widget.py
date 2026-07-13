"""
Terminal Widget for SB Toolsmith Pro

ANSI-aware terminal emulator with color support and scrollback.
"""

import re
from typing import Optional

from PySide6.QtCore import Qt, QSize, Signal, QTimer
from PySide6.QtGui import QColor, QFont, QTextCursor, QTextCharFormat
from PySide6.QtWidgets import QPlainTextEdit, QWidget, QVBoxLayout, QHBoxLayout, QPushButton


class ANSIParser:
    """Parse ANSI escape codes."""

    # ANSI color codes
    COLORS = {
        "30": QColor(0, 0, 0),  # Black
        "31": QColor(255, 0, 0),  # Red
        "32": QColor(0, 255, 0),  # Green
        "33": QColor(255, 255, 0),  # Yellow
        "34": QColor(0, 0, 255),  # Blue
        "35": QColor(255, 0, 255),  # Magenta
        "36": QColor(0, 255, 255),  # Cyan
        "37": QColor(255, 255, 255),  # White
        "90": QColor(128, 128, 128),  # Bright Black
        "91": QColor(255, 128, 128),  # Bright Red
        "92": QColor(128, 255, 128),  # Bright Green
        "93": QColor(255, 255, 128),  # Bright Yellow
        "94": QColor(128, 128, 255),  # Bright Blue
        "95": QColor(255, 128, 255),  # Bright Magenta
        "96": QColor(128, 255, 255),  # Bright Cyan
        "97": QColor(255, 255, 255),  # Bright White
    }

    @staticmethod
    def parse(text: str) -> list:
        """
        Parse ANSI escape codes.
        
        Returns:
            List of (text, format_dict) tuples
        """
        # Pattern for ANSI escape codes
        pattern = r"\x1b\[([0-9;]*?)m"
        
        parts = []
        last_end = 0
        current_format = {
            "color": QColor(255, 255, 255),
            "bold": False,
            "italic": False,
            "underline": False,
        }

        for match in re.finditer(pattern, text):
            # Add text before escape code
            if match.start() > last_end:
                parts.append((text[last_end:match.start()], current_format.copy()))

            # Parse escape code
            codes = match.group(1).split(";")
            for code in codes:
                if code == "0":  # Reset
                    current_format = {
                        "color": QColor(255, 255, 255),
                        "bold": False,
                        "italic": False,
                        "underline": False,
                    }
                elif code == "1":  # Bold
                    current_format["bold"] = True
                elif code == "3":  # Italic
                    current_format["italic"] = True
                elif code == "4":  # Underline
                    current_format["underline"] = True
                elif code in ANSIParser.COLORS:
                    current_format["color"] = ANSIParser.COLORS[code]

            last_end = match.end()

        # Add remaining text
        if last_end < len(text):
            parts.append((text[last_end:], current_format.copy()))

        return parts


class TerminalWidget(QWidget):
    """Terminal widget with ANSI color support."""

    output_updated = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize terminal widget."""
        super().__init__(parent)
        self._init_ui()
        self._max_lines = 10000
        self._line_count = 0

    def _init_ui(self) -> None:
        """Initialize UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Terminal display
        self.terminal = QPlainTextEdit()
        self.terminal.setReadOnly(True)
        self.terminal.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: 'Courier New', monospace;
                font-size: 10pt;
                padding: 5px;
            }
        """)

        # Set monospace font
        font = QFont("Courier New", 10)
        font.setFixedPitch(True)
        self.terminal.setFont(font)

        layout.addWidget(self.terminal)

        # Control buttons
        button_layout = QHBoxLayout()
        
        self.copy_btn = QPushButton("Copy")
        self.copy_btn.clicked.connect(self._copy_output)
        button_layout.addWidget(self.copy_btn)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self._clear_output)
        button_layout.addWidget(self.clear_btn)

        self.scroll_to_end_btn = QPushButton("Scroll to End")
        self.scroll_to_end_btn.clicked.connect(self._scroll_to_end)
        button_layout.addWidget(self.scroll_to_end_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def append_output(self, text: str, color: Optional[QColor] = None) -> None:
        """
        Append text to terminal.
        
        Args:
            text: Text to append
            color: Optional text color
        """
        cursor = self.terminal.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.terminal.setTextCursor(cursor)

        # Parse ANSI codes
        parts = ANSIParser.parse(text)

        for part_text, format_dict in parts:
            if not part_text:
                continue

            # Create format
            fmt = QTextCharFormat()
            fmt.setForeground(format_dict.get("color", QColor(255, 255, 255)))
            
            if format_dict.get("bold"):
                fmt.setFontWeight(600)
            if format_dict.get("italic"):
                fmt.setFontItalic(True)
            if format_dict.get("underline"):
                fmt.setFontUnderline(True)

            # Insert text
            cursor.insertText(part_text, fmt)

        self.terminal.setTextCursor(cursor)
        self._line_count += text.count("\n")

        # Trim if too many lines
        if self._line_count > self._max_lines:
            self._trim_output()

        self.output_updated.emit(text)

    def append_success(self, text: str) -> None:
        """Append success message (green)."""
        self.append_output(f"\x1b[32m{text}\x1b[0m")

    def append_error(self, text: str) -> None:
        """Append error message (red)."""
        self.append_output(f"\x1b[31m{text}\x1b[0m")

    def append_warning(self, text: str) -> None:
        """Append warning message (yellow)."""
        self.append_output(f"\x1b[33m{text}\x1b[0m")

    def append_info(self, text: str) -> None:
        """Append info message (cyan)."""
        self.append_output(f"\x1b[36m{text}\x1b[0m")

    def _copy_output(self) -> None:
        """Copy terminal output to clipboard."""
        from PySide6.QtGui import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(self.terminal.toPlainText())

    def _clear_output(self) -> None:
        """Clear terminal output."""
        self.terminal.clear()
        self._line_count = 0

    def _scroll_to_end(self) -> None:
        """Scroll to end of output."""
        cursor = self.terminal.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.terminal.setTextCursor(cursor)
        self.terminal.ensureCursorVisible()

    def _trim_output(self) -> None:
        """Trim output to max lines."""
        doc = self.terminal.document()
        block_count = doc.blockCount()

        if block_count > self._max_lines:
            # Remove first 10% of blocks
            blocks_to_remove = int(block_count * 0.1)
            
            cursor = self.terminal.textCursor()
            cursor.movePosition(QTextCursor.Start)
            
            for _ in range(blocks_to_remove):
                cursor.select(QTextCursor.BlockUnderCursor)
                cursor.removeSelectedText()
                cursor.deleteChar()

            self._line_count = doc.blockCount()

    def get_output(self) -> str:
        """Get all terminal output."""
        return self.terminal.toPlainText()

    def set_max_lines(self, max_lines: int) -> None:
        """Set maximum number of lines to keep."""
        self._max_lines = max_lines
