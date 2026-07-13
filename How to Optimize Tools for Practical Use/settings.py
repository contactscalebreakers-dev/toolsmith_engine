"""
Settings Manager for SB Toolsmith Pro

Application configuration and preferences.
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class AISettings:
    """AI provider settings."""

    provider: str = "ollama"  # ollama or openai
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "mistral"
    ollama_timeout: int = 30
    openai_api_key: str = ""
    openai_model: str = "gpt-3.5-turbo"
    openai_base_url: Optional[str] = None
    temperature: float = 0.7
    enabled: bool = False


@dataclass
class RuntimeSettings:
    """Runtime settings."""

    max_memory_mb: int = 512
    max_cpu_percent: float = 80.0
    max_runtime_seconds: int = 300
    max_processes: int = 10
    network_enabled: bool = False
    file_access_restricted: bool = True


@dataclass
class UISettings:
    """UI settings."""

    theme: str = "dark"
    window_width: int = 1400
    window_height: int = 900
    show_grid: bool = True
    auto_layout: bool = False
    font_size: int = 10


@dataclass
class AppSettings:
    """Application settings."""

    ai: AISettings
    runtime: RuntimeSettings
    ui: UISettings
    auto_save: bool = True
    auto_save_interval: int = 60
    debug_mode: bool = False
    log_level: str = "INFO"


class SettingsManager:
    """Manage application settings."""

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize settings manager.
        
        Args:
            config_dir: Configuration directory
        """
        self.config_dir = config_dir or Path.home() / ".sb-toolsmith" / "config"
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self.settings_file = self.config_dir / "settings.json"
        self.settings = self._load_settings()

    def _load_settings(self) -> AppSettings:
        """Load settings from file."""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, "r") as f:
                    data = json.load(f)

                return AppSettings(
                    ai=AISettings(**data.get("ai", {})),
                    runtime=RuntimeSettings(**data.get("runtime", {})),
                    ui=UISettings(**data.get("ui", {})),
                    auto_save=data.get("auto_save", True),
                    auto_save_interval=data.get("auto_save_interval", 60),
                    debug_mode=data.get("debug_mode", False),
                    log_level=data.get("log_level", "INFO"),
                )
            else:
                return AppSettings(
                    ai=AISettings(),
                    runtime=RuntimeSettings(),
                    ui=UISettings(),
                )

        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
            return AppSettings(
                ai=AISettings(),
                runtime=RuntimeSettings(),
                ui=UISettings(),
            )

    def save_settings(self) -> bool:
        """Save settings to file."""
        try:
            data = {
                "ai": asdict(self.settings.ai),
                "runtime": asdict(self.settings.runtime),
                "ui": asdict(self.settings.ui),
                "auto_save": self.settings.auto_save,
                "auto_save_interval": self.settings.auto_save_interval,
                "debug_mode": self.settings.debug_mode,
                "log_level": self.settings.log_level,
            }

            with open(self.settings_file, "w") as f:
                json.dump(data, f, indent=2)

            logger.info("Settings saved")
            return True

        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            return False

    def get_ai_settings(self) -> AISettings:
        """Get AI settings."""
        return self.settings.ai

    def set_ai_settings(self, ai_settings: AISettings) -> bool:
        """Set AI settings."""
        self.settings.ai = ai_settings
        return self.save_settings()

    def get_runtime_settings(self) -> RuntimeSettings:
        """Get runtime settings."""
        return self.settings.runtime

    def set_runtime_settings(self, runtime_settings: RuntimeSettings) -> bool:
        """Set runtime settings."""
        self.settings.runtime = runtime_settings
        return self.save_settings()

    def get_ui_settings(self) -> UISettings:
        """Get UI settings."""
        return self.settings.ui

    def set_ui_settings(self, ui_settings: UISettings) -> bool:
        """Set UI settings."""
        self.settings.ui = ui_settings
        return self.save_settings()

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get individual setting."""
        try:
            parts = key.split(".")
            value = self.settings

            for part in parts:
                if hasattr(value, part):
                    value = getattr(value, part)
                else:
                    return default

            return value

        except:
            return default

    def set_setting(self, key: str, value: Any) -> bool:
        """Set individual setting."""
        try:
            parts = key.split(".")
            obj = self.settings

            for part in parts[:-1]:
                if hasattr(obj, part):
                    obj = getattr(obj, part)
                else:
                    return False

            if hasattr(obj, parts[-1]):
                setattr(obj, parts[-1], value)
                return self.save_settings()

            return False

        except:
            return False

    def reset_to_defaults(self) -> bool:
        """Reset settings to defaults."""
        self.settings = AppSettings(
            ai=AISettings(),
            runtime=RuntimeSettings(),
            ui=UISettings(),
        )
        return self.save_settings()

    def get_all_settings(self) -> Dict[str, Any]:
        """Get all settings as dictionary."""
        return {
            "ai": asdict(self.settings.ai),
            "runtime": asdict(self.settings.runtime),
            "ui": asdict(self.settings.ui),
            "auto_save": self.settings.auto_save,
            "auto_save_interval": self.settings.auto_save_interval,
            "debug_mode": self.settings.debug_mode,
            "log_level": self.settings.log_level,
        }
