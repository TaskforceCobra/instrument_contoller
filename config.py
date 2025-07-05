"""
Configuration settings for DMM Logger application.
"""

import os
from pathlib import Path

# Application information
APP_NAME = "DMM Logger"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Digital Multimeter Controller"

# File paths
PROJECT_ROOT = Path(__file__).parent
LOGS_DIR = PROJECT_ROOT / "logs"
EXPORTS_DIR = PROJECT_ROOT / "exports"

# Ensure directories exist
LOGS_DIR.mkdir(exist_ok=True)
EXPORTS_DIR.mkdir(exist_ok=True)

# Default log file
DEFAULT_LOG_FILE = LOGS_DIR / "dmm_logger.log"

# GPIB settings
DEFAULT_GPIB_TIMEOUT = 5000  # milliseconds
DEFAULT_MEASUREMENT_INTERVAL = 1000  # milliseconds

# Data settings
MAX_DATA_POINTS = 1000  # Maximum data points to keep per device
DEFAULT_TIME_WINDOW = 600  # seconds (10 minutes)

# UI settings
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 900
MIN_WINDOW_WIDTH = 800
MIN_WINDOW_HEIGHT = 600

# Table settings
TABLE_FONT_FAMILY = "Consolas"
TABLE_FONT_SIZE = 9

# Graph settings
GRAPH_UPDATE_INTERVAL = 100  # milliseconds
GRAPH_LINE_WIDTH = 2

# Export settings
SUPPORTED_EXPORT_FORMATS = ['CSV', 'JSON', 'TXT']
DEFAULT_EXPORT_FORMAT = 'CSV'

# SCPI settings
DEFAULT_SCPI_TIMEOUT = 5.0  # seconds
MAX_SCPI_RETRIES = 3

# Error handling
MAX_ERROR_MESSAGES = 100
ERROR_DISPLAY_TIMEOUT = 5000  # milliseconds

# Development settings
DEBUG_MODE = os.getenv('DMM_LOGGER_DEBUG', 'False').lower() == 'true'
TEST_MODE = os.getenv('DMM_LOGGER_TEST', 'False').lower() == 'true' 