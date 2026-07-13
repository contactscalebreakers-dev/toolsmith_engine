"""
AI Configuration Dialog for SB Toolsmith Pro

Configure LLM providers and AI settings.
"""

from typing import Optional, Dict, Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QSpinBox, QDoubleSpinBox, QCheckBox, QPushButton, QTabWidget,
    QFormLayout, QGroupBox, QMessageBox,
)


class AIConfigDialog(QDialog):
    """Dialog for configuring AI providers."""

    config_saved = Signal(dict)

    def __init__(self, parent: Optional[QDialog] = None):
        """Initialize AI config dialog."""
        super().__init__(parent)
        self.setWindowTitle("AI Configuration")
        self.setMinimumWidth(600)
        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize UI."""
        layout = QVBoxLayout()

        # Title
        title = QLabel("AI Provider Configuration")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Tabs
        self.tabs = QTabWidget()

        # Ollama tab
        self.tabs.addTab(self._create_ollama_tab(), "Ollama (Local)")

        # OpenAI tab
        self.tabs.addTab(self._create_openai_tab(), "OpenAI (Cloud)")

        layout.addWidget(self.tabs)

        # Buttons
        button_layout = QHBoxLayout()

        self.test_btn = QPushButton("Test Connection")
        self.test_btn.clicked.connect(self._test_connection)
        button_layout.addWidget(self.test_btn)

        button_layout.addStretch()

        self.save_btn = QPushButton("Save Configuration")
        self.save_btn.clicked.connect(self._save_config)
        button_layout.addWidget(self.save_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def _create_ollama_tab(self) -> QWidget:
        """Create Ollama configuration tab."""
        widget = QWidget()
        layout = QFormLayout()

        # Base URL
        self.ollama_url = QLineEdit()
        self.ollama_url.setText("http://localhost:11434")
        layout.addRow("Base URL:", self.ollama_url)

        # Model
        self.ollama_model = QComboBox()
        self.ollama_model.addItems([
            "mistral",
            "llama2",
            "neural-chat",
            "dolphin-mixtral",
            "openchat",
        ])
        layout.addRow("Model:", self.ollama_model)

        # Timeout
        self.ollama_timeout = QSpinBox()
        self.ollama_timeout.setRange(10, 3600)
        self.ollama_timeout.setValue(300)
        self.ollama_timeout.setSuffix(" seconds")
        layout.addRow("Timeout:", self.ollama_timeout)

        # Temperature
        self.ollama_temp = QDoubleSpinBox()
        self.ollama_temp.setRange(0.0, 2.0)
        self.ollama_temp.setValue(0.7)
        self.ollama_temp.setSingleStep(0.1)
        layout.addRow("Temperature:", self.ollama_temp)

        # Auto-pull models
        self.ollama_auto_pull = QCheckBox("Auto-pull missing models")
        self.ollama_auto_pull.setChecked(True)
        layout.addRow("", self.ollama_auto_pull)

        widget.setLayout(layout)
        return widget

    def _create_openai_tab(self) -> QWidget:
        """Create OpenAI configuration tab."""
        widget = QWidget()
        layout = QFormLayout()

        # API Key
        self.openai_key = QLineEdit()
        self.openai_key.setEchoMode(QLineEdit.Password)
        layout.addRow("API Key:", self.openai_key)

        # Model
        self.openai_model = QComboBox()
        self.openai_model.addItems([
            "gpt-3.5-turbo",
            "gpt-4",
            "gpt-4-turbo",
        ])
        layout.addRow("Model:", self.openai_model)

        # Base URL (for OpenAI-compatible APIs)
        self.openai_base_url = QLineEdit()
        self.openai_base_url.setPlaceholderText("Leave empty for default")
        layout.addRow("Base URL (optional):", self.openai_base_url)

        # Timeout
        self.openai_timeout = QSpinBox()
        self.openai_timeout.setRange(10, 600)
        self.openai_timeout.setValue(60)
        self.openai_timeout.setSuffix(" seconds")
        layout.addRow("Timeout:", self.openai_timeout)

        # Temperature
        self.openai_temp = QDoubleSpinBox()
        self.openai_temp.setRange(0.0, 2.0)
        self.openai_temp.setValue(0.7)
        self.openai_temp.setSingleStep(0.1)
        layout.addRow("Temperature:", self.openai_temp)

        # Enable
        self.openai_enabled = QCheckBox("Enable OpenAI provider")
        self.openai_enabled.setChecked(False)
        layout.addRow("", self.openai_enabled)

        widget.setLayout(layout)
        return widget

    def _test_connection(self) -> None:
        """Test provider connection."""
        provider_index = self.tabs.currentIndex()

        if provider_index == 0:
            # Test Ollama
            QMessageBox.information(
                self,
                "Connection Test",
                "Testing Ollama connection...\n\n(Implementation pending)",
            )
        else:
            # Test OpenAI
            if not self.openai_key.text():
                QMessageBox.warning(
                    self,
                    "Configuration Error",
                    "Please enter your OpenAI API key.",
                )
                return

            QMessageBox.information(
                self,
                "Connection Test",
                "Testing OpenAI connection...\n\n(Implementation pending)",
            )

    def _save_config(self) -> None:
        """Save configuration."""
        config = {
            "ollama": {
                "url": self.ollama_url.text(),
                "model": self.ollama_model.currentText(),
                "timeout": self.ollama_timeout.value(),
                "temperature": self.ollama_temp.value(),
                "auto_pull": self.ollama_auto_pull.isChecked(),
            },
            "openai": {
                "api_key": self.openai_key.text(),
                "model": self.openai_model.currentText(),
                "base_url": self.openai_base_url.text() or None,
                "timeout": self.openai_timeout.value(),
                "temperature": self.openai_temp.value(),
                "enabled": self.openai_enabled.isChecked(),
            },
        }

        self.config_saved.emit(config)
        self.accept()

    def get_config(self) -> Dict[str, Any]:
        """Get current configuration."""
        return {
            "ollama": {
                "url": self.ollama_url.text(),
                "model": self.ollama_model.currentText(),
                "timeout": self.ollama_timeout.value(),
                "temperature": self.ollama_temp.value(),
                "auto_pull": self.ollama_auto_pull.isChecked(),
            },
            "openai": {
                "api_key": self.openai_key.text(),
                "model": self.openai_model.currentText(),
                "base_url": self.openai_base_url.text() or None,
                "timeout": self.openai_timeout.value(),
                "temperature": self.openai_temp.value(),
                "enabled": self.openai_enabled.isChecked(),
            },
        }

    def set_config(self, config: Dict[str, Any]) -> None:
        """Set configuration from dict."""
        if "ollama" in config:
            ollama = config["ollama"]
            self.ollama_url.setText(ollama.get("url", "http://localhost:11434"))
            self.ollama_model.setCurrentText(ollama.get("model", "mistral"))
            self.ollama_timeout.setValue(ollama.get("timeout", 300))
            self.ollama_temp.setValue(ollama.get("temperature", 0.7))
            self.ollama_auto_pull.setChecked(ollama.get("auto_pull", True))

        if "openai" in config:
            openai = config["openai"]
            self.openai_key.setText(openai.get("api_key", ""))
            self.openai_model.setCurrentText(openai.get("model", "gpt-3.5-turbo"))
            if openai.get("base_url"):
                self.openai_base_url.setText(openai["base_url"])
            self.openai_timeout.setValue(openai.get("timeout", 60))
            self.openai_temp.setValue(openai.get("temperature", 0.7))
            self.openai_enabled.setChecked(openai.get("enabled", False))
