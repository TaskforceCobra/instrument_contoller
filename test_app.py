#!/usr/bin/env python3
"""
Test script for DMM Logger application.
This script tests the application startup without requiring GPIB hardware.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QTimer

from ui.main_window import MainWindow
from utils.logger import setup_logger


def test_application():
    """Test the application startup and basic functionality."""
    # Set up logging
    logger = setup_logger('test_app', 'logs/test_app.log')
    logger.info("Starting DMM Logger test application")
    
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("DMM Logger Test")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("DMM Logger")
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show main window
    main_window = MainWindow()
    main_window.show()
    
    logger.info("Main window displayed")
    
    # Show test message
    QMessageBox.information(main_window, "Test Mode", 
                          "DMM Logger is running in test mode.\n\n"
                          "This means:\n"
                          "- No actual GPIB hardware is required\n"
                          "- You can explore the interface\n"
                          "- Device connections will be simulated\n"
                          "- Data export and graphing will work with sample data\n\n"
                          "To use with real hardware, ensure GPIB drivers are installed.")
    
    # Set up a timer to add some test data after 5 seconds
    def add_test_data():
        try:
            # Ensure UI is fully initialized
            if main_window.device_table is None:
                logger.warning("Device table not yet initialized, retrying...")
                QTimer.singleShot(1000, add_test_data)
                return
                
            # Add a test device
            main_window.device_table.add_device_row(
                device_name="Test DMM 1",
                address="GPIB0::1::INSTR",
                function="DC Voltage",
                range_value="AUTO",
                samples=1,
                user_label="Test Device"
            )
            
            # Add some test measurements
            for i in range(10):
                value = 5.0 + (i * 0.1)  # Simulate voltage readings
                main_window.data_handler.add_measurement(
                    "Test DMM 1", "DC Voltage", value, "V", "OK", "Test Device"
                )
                main_window.graph_manager.add_data_point("Test DMM 1", value)
            
            logger.info("Added test data")
            
        except Exception as e:
            logger.error(f"Failed to add test data: {e}")
    
    # Schedule test data addition
    QTimer.singleShot(5000, add_test_data)
    
    # Run application
    try:
        exit_code = app.exec()
        logger.info(f"Test application exited with code {exit_code}")
        return exit_code
    except KeyboardInterrupt:
        logger.info("Test application interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"Test application error: {e}")
        return 1


if __name__ == "__main__":
    # Ensure logs directory exists
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Run the test application
    sys.exit(test_application()) 