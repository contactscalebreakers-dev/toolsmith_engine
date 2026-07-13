"""
SB Toolsmith Pro - Main Application Entry Point

Initializes the application, sets up logging, and starts the UI.
"""

import asyncio
import logging
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from core import initialize_event_bus, shutdown_event_bus
from ui.main_window import create_main_window
from utils.logging_config import setup_logging


def setup_application() -> None:
    """Set up application environment."""
    # Create necessary directories
    (PROJECT_ROOT / "logs").mkdir(exist_ok=True)
    (PROJECT_ROOT / "data").mkdir(exist_ok=True)
    (PROJECT_ROOT / "plugins").mkdir(exist_ok=True)
    (PROJECT_ROOT / "workspaces").mkdir(exist_ok=True)


async def async_main() -> int:
    """
    Async main function.
    
    Returns:
        Exit code
    """
    logger = logging.getLogger(__name__)
    logger.info("SB Toolsmith Pro starting")
    
    # Initialize event bus
    event_bus = await initialize_event_bus()
    logger.info("Event bus initialized")
    
    try:
        # Create Qt application
        app = QApplication(sys.argv)
        
        # Create main window
        main_window = create_main_window()
        main_window.show()
        
        logger.info("Main window displayed")
        
        # Run Qt event loop
        exit_code = app.exec()
        
        return exit_code
        
    finally:
        # Cleanup
        await shutdown_event_bus()
        logger.info("Event bus shutdown")


def main() -> int:
    """
    Main entry point.
    
    Returns:
        Exit code
    """
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Setup application
        setup_application()
        
        # Run async main
        exit_code = asyncio.run(async_main())
        
        logger.info(f"Application exiting with code {exit_code}")
        return exit_code
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
