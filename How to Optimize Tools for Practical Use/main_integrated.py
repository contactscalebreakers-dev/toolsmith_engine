"""
SB Toolsmith Pro - Main Entry Point

AI-native execution operating system for Python tool orchestration.
"""

import sys
import asyncio
import logging
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

from core.event_bus import EventBus
from core.scheduler import Scheduler
from ui.main_window_integrated import MainWindowIntegrated
from config.settings import SettingsManager
from utils.logging_config import setup_logging

logger = logging.getLogger(__name__)


class Application:
    """SB Toolsmith Pro application."""

    def __init__(self):
        """Initialize application."""
        self.event_bus = EventBus()
        self.scheduler = Scheduler()
        self.settings = SettingsManager()

        # Setup logging
        setup_logging(
            log_level=self.settings.settings.log_level,
            debug=self.settings.settings.debug_mode,
        )

        logger.info("SB Toolsmith Pro initialized")

    def run(self) -> int:
        """Run application."""
        try:
            # Create Qt application
            qt_app = QApplication(sys.argv)

            # Create main window
            main_window = MainWindowIntegrated()
            main_window.show()

            logger.info("Application started")

            # Run event loop
            return qt_app.exec()

        except Exception as e:
            logger.error(f"Application error: {e}", exc_info=True)
            return 1


def main() -> int:
    """Main entry point."""
    app = Application()
    return app.run()


if __name__ == "__main__":
    sys.exit(main())
