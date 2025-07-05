#!/usr/bin/env python3
"""
DMM Logger - Digital Multimeter Controller
Main application entry point.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from ui.main_window import MainWindow
from utils.logger import setup_logger


def main():
    """Main application entry point."""
    # Set up logging
    logger = setup_logger('dmm_logger', 'logs/dmm_logger.log')
    logger.info("Starting DMM Logger application")
    
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("DMM Logger")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("DMM Logger")
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show main window
    main_window = MainWindow()
    main_window.show()
    
    logger.info("Main window displayed")
    
    # Run application
    try:
        exit_code = app.exec()
        logger.info(f"Application exited with code {exit_code}")
        return exit_code
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"Application error: {e}")
        return 1


if __name__ == "__main__":
    # Ensure logs directory exists
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Run the application
    sys.exit(main()) 