"""
Main application window for DMM Logger.
"""

import os
from typing import Optional
from datetime import datetime

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QSplitter, QPushButton, QLabel, 
                             QStatusBar, QMenuBar, QFileDialog, QMessageBox,
                             QGroupBox, QGridLayout, QSpinBox, QComboBox,
                             QTextEdit, QProgressBar, QFrame, QScrollArea)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QFont, QIcon, QPalette, QColor

from .device_table import DeviceTableWidget
from core.device_manager import DeviceManager, DeviceConfig
from core.data_handler import DataHandler
from core.graph_manager import GraphManager, RealTimeGraphWidget
from utils.scpi_commands import SCPICommands
from utils.logger import setup_logger


class ModernButton(QPushButton):
    """Modern styled button with hover effects."""
    
    def __init__(self, text: str, icon_name: str = "", parent=None):
        super().__init__(text, parent)
        self.setup_style(icon_name)
    
    def setup_style(self, icon_name: str):
        """Set up modern button styling."""
        # Set icon if provided
        if icon_name:
            # Use text-based icons for simplicity
            icon_map = {
                "refresh": "🔄",
                "play": "▶️",
                "stop": "⏹️",
                "add": "➕",
                "remove": "➖",
                "connect": "🔌",
                "disconnect": "🔌",
                "export": "📤",
                "clear": "🗑️"
            }
            if icon_name in icon_map:
                self.setText(f"{icon_map[icon_name]} {self.text()}")
        
        # Dark navy blue modern styling
        self.setStyleSheet("""
            QPushButton {
                background-color: #1a2340;
                color: #ffffff;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 500;
                font-size: 12px;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #223060;
            }
            QPushButton:pressed {
                background-color: #10162a;
            }
            QPushButton:disabled {
                background-color: #7f8c8d;
                color: #bdc3c7;
            }
        """)
        
        # Set cursor
        self.setCursor(Qt.CursorShape.PointingHandCursor)


class ModernGroupBox(QGroupBox):
    """Modern styled group box."""
    
    def __init__(self, title: str, parent=None):
        super().__init__(title, parent)
        self.setup_style()
    
    def setup_style(self):
        """Set up modern group box styling."""
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                color: #2c3e50;
                border: 2px solid #ecf0f1;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #f8f9fa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                background-color: #f8f9fa;
            }
        """)


class MainWindow(QMainWindow):
    """
    Main application window for DMM Logger.
    """
    
    def __init__(self):
        """Initialize the main window."""
        super().__init__()
        
        # Initialize components
        self.logger = setup_logger('main_window', 'logs/dmm_logger.log')
        self.device_manager = DeviceManager()
        self.data_handler = DataHandler()
        self.graph_manager = GraphManager()
        
        # UI components
        self.device_table = None
        self.graph_widget = None
        self.status_label = None
        self.progress_bar = None
        self.log_text = None
        
        # State
        self.is_acquiring = False
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(1000)  # Update every second
        
        self.setup_ui()
        self.setup_connections()
        self.setup_menu()
        
        # Initialize VISA
        if not self.device_manager.initialize_visa():
            QMessageBox.warning(self, "VISA Error", 
                              "Failed to initialize VISA. GPIB functionality may not work.")
        
        self.logger.info("MainWindow initialized")
    
    def setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle("DMM Logger - Digital Multimeter Controller")
        self.setGeometry(100, 100, 1600, 1000)
        self.setStyleSheet("""
            QMainWindow { background-color: #f5f6fa; }
            QLabel { color: #2c3e50; font-size: 12px; }
            QComboBox, QSpinBox, QTextEdit, QProgressBar {
                font-size: 12px;
            }
        """)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Main vertical splitter: top (table+controls), bottom (graph)
        main_splitter = QSplitter(Qt.Orientation.Vertical)
        main_layout.addWidget(main_splitter)

        # --- Top panel: device table (left, stretch) + controls (right, fixed) ---
        top_panel = QWidget()
        top_layout = QHBoxLayout(top_panel)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(10)

        # Device table (left, stretch)
        table_group = ModernGroupBox("Device Configuration")
        table_layout = QVBoxLayout(table_group)
        table_layout.setSpacing(8)
        self.device_table = DeviceTableWidget()
        table_layout.addWidget(self.device_table)
        # Table buttons
        table_buttons_layout = QHBoxLayout()
        table_buttons_layout.setSpacing(8)
        add_button = ModernButton("Add Device", "add"); add_button.clicked.connect(self.add_device)
        remove_button = ModernButton("Remove Device", "remove"); remove_button.clicked.connect(self.remove_device)
        refresh_button = ModernButton("Refresh Devices", "refresh"); refresh_button.clicked.connect(self.refresh_devices)
        self.connect_toggle_button = ModernButton("Connect All", "connect")
        self.connect_toggle_button.clicked.connect(self.toggle_connect_all)
        table_buttons_layout.addWidget(add_button)
        table_buttons_layout.addWidget(remove_button)
        table_buttons_layout.addWidget(refresh_button)
        table_buttons_layout.addWidget(self.connect_toggle_button)
        table_layout.addLayout(table_buttons_layout)
        # Make table group stretch
        top_layout.addWidget(table_group, stretch=3)

        # Controls panel (right, fixed width)
        controls_panel = QWidget()
        controls_panel.setFixedWidth(400)
        controls_layout = QVBoxLayout(controls_panel)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(10)
        # Acquisition group
        acq_group = ModernGroupBox("Data Acquisition")
        acq_layout = QGridLayout(acq_group)
        acq_layout.setSpacing(10)
        acq_layout.addWidget(QLabel("Interval (ms):"), 0, 0)
        self.interval_spin = QSpinBox(); self.interval_spin.setRange(100, 10000); self.interval_spin.setValue(1000); self.interval_spin.setSuffix(" ms")
        acq_layout.addWidget(self.interval_spin, 0, 1)
        self.start_stop_button = ModernButton("Start Acquisition", "play"); self.start_stop_button.clicked.connect(self.toggle_acquisition)
        acq_layout.addWidget(self.start_stop_button, 1, 0, 1, 2)
        self.progress_bar = QProgressBar(); self.progress_bar.setVisible(False)
        acq_layout.addWidget(self.progress_bar, 2, 0, 1, 2)
        controls_layout.addWidget(acq_group)
        # Data management group
        data_group = ModernGroupBox("Data Management")
        data_layout = QGridLayout(data_group)
        data_layout.setSpacing(10)
        data_layout.addWidget(QLabel("Export Format:"), 0, 0)
        self.export_format_combo = QComboBox(); self.export_format_combo.addItems(['CSV', 'JSON', 'TXT'])
        data_layout.addWidget(self.export_format_combo, 0, 1)
        # Export and Clear buttons side by side
        export_button = ModernButton("Export Data", "export"); export_button.clicked.connect(self.export_data)
        clear_button = ModernButton("Clear Data", "clear"); clear_button.clicked.connect(self.clear_data)
        button_hbox = QHBoxLayout()
        button_hbox.addWidget(export_button)
        button_hbox.addWidget(clear_button)
        data_layout.addLayout(button_hbox, 1, 0, 1, 2)
        controls_layout.addWidget(data_group)
        # Log group
        log_group = ModernGroupBox("Application Log")
        log_layout = QVBoxLayout(log_group); log_layout.setSpacing(8)
        self.log_text = QTextEdit(); self.log_text.setReadOnly(True); self.log_text.setMaximumHeight(80)
        log_layout.addWidget(self.log_text)
        controls_layout.addWidget(log_group)
        controls_layout.addStretch()
        top_layout.addWidget(controls_panel, stretch=1)
        main_splitter.addWidget(top_panel)

        # --- Bottom panel: graph (full width, expands) ---
        bottom_panel = QWidget()
        bottom_layout = QVBoxLayout(bottom_panel)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(10)
        graph_group = ModernGroupBox("Real-time Data Visualization")
        graph_layout = QVBoxLayout(graph_group); graph_layout.setSpacing(8)
        self.graph_widget = RealTimeGraphWidget(self.graph_manager)
        graph_layout.addWidget(self.graph_widget)
        bottom_layout.addWidget(graph_group)
        # Data statistics group below the graph
        stats_group = ModernGroupBox("Data Statistics")
        stats_layout = QVBoxLayout(stats_group); stats_layout.setSpacing(8)
        self.stats_label = QLabel("No data available")
        self.stats_label.setStyleSheet("""QLabel { padding: 10px; background-color: #ecf0f1; border-radius: 4px; font-family: 'Consolas', monospace; font-size: 11px; }""")
        stats_layout.addWidget(self.stats_label)
        bottom_layout.addWidget(stats_group)
        main_splitter.addWidget(bottom_panel)
        # Set splitter so graph gets most space
        main_splitter.setSizes([350, 650])
        self.setup_status_bar()
        self.device_manager.measurement_received.connect(self.on_measurement_received)
        self.device_manager.error_occurred.connect(self.on_device_error)
        self.device_manager.device_connected.connect(self.on_device_connected)
        self.device_manager.device_disconnected.connect(self.on_device_disconnected)
        self.update_connect_toggle_button() # Initialize button state
    
    def create_left_panel(self) -> QWidget:
        """Create the left panel with device management and controls."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Device table group
        table_group = ModernGroupBox("Device Configuration")
        table_layout = QVBoxLayout(table_group)
        table_layout.setSpacing(8)
        
        # Device table
        self.device_table = DeviceTableWidget()
        table_layout.addWidget(self.device_table)
        
        # Device table buttons
        table_buttons_layout = QHBoxLayout()
        table_buttons_layout.setSpacing(8)
        
        add_button = ModernButton("Add Device", "add")
        add_button.clicked.connect(self.add_device)
        table_buttons_layout.addWidget(add_button)
        
        remove_button = ModernButton("Remove Device", "remove")
        remove_button.clicked.connect(self.remove_device)
        table_buttons_layout.addWidget(remove_button)
        
        refresh_button = ModernButton("Refresh Devices", "refresh")
        refresh_button.clicked.connect(self.refresh_devices)
        table_buttons_layout.addWidget(refresh_button)
        
        table_buttons_layout.addStretch()
        
        connect_button = ModernButton("Connect All", "connect")
        connect_button.clicked.connect(self.connect_all_devices)
        table_buttons_layout.addWidget(connect_button)
        
        disconnect_button = ModernButton("Disconnect All", "disconnect")
        disconnect_button.clicked.connect(self.disconnect_all_devices)
        table_buttons_layout.addWidget(disconnect_button)
        
        table_layout.addLayout(table_buttons_layout)
        layout.addWidget(table_group)
        
        # Acquisition control group
        acq_group = ModernGroupBox("Data Acquisition")
        acq_layout = QGridLayout(acq_group)
        acq_layout.setSpacing(10)
        
        # Interval control
        acq_layout.addWidget(QLabel("Interval (ms):"), 0, 0)
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(100, 10000)
        self.interval_spin.setValue(1000)
        self.interval_spin.setSuffix(" ms")
        acq_layout.addWidget(self.interval_spin, 0, 1)
        
        # Start/Stop button
        self.start_stop_button = ModernButton("Start Acquisition", "play")
        self.start_stop_button.clicked.connect(self.toggle_acquisition)
        acq_layout.addWidget(self.start_stop_button, 1, 0, 1, 2)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        acq_layout.addWidget(self.progress_bar, 2, 0, 1, 2)
        
        layout.addWidget(acq_group)
        
        # Data management group
        data_group = ModernGroupBox("Data Management")
        data_layout = QGridLayout(data_group)
        data_layout.setSpacing(10)
        
        # Export format
        data_layout.addWidget(QLabel("Export Format:"), 0, 0)
        self.export_format_combo = QComboBox()
        self.export_format_combo.addItems(['CSV', 'JSON', 'TXT'])
        data_layout.addWidget(self.export_format_combo, 0, 1)
        
        # Export button
        export_button = ModernButton("Export Data", "export")
        export_button.clicked.connect(self.export_data)
        data_layout.addWidget(export_button, 1, 0, 1, 2)
        
        # Clear data button
        clear_button = ModernButton("Clear Data", "clear")
        clear_button.clicked.connect(self.clear_data)
        data_layout.addWidget(clear_button, 2, 0, 1, 2)
        
        layout.addWidget(data_group)
        
        layout.addStretch()
        return panel
    
    def create_right_panel(self) -> QWidget:
        """Create the right panel with graph and data."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Create vertical splitter for top/bottom
        right_splitter = QSplitter(Qt.Orientation.Vertical)
        layout.addWidget(right_splitter)
        
        # Top panel - Graph
        top_panel = self.create_top_panel()
        right_splitter.addWidget(top_panel)
        
        # Bottom panel - Log and Statistics
        bottom_panel = self.create_bottom_panel()
        right_splitter.addWidget(bottom_panel)
        
        # Set vertical splitter proportions (90% top, 10% bottom)
        right_splitter.setSizes([900, 100])
        
        return panel
    
    def create_top_panel(self) -> QWidget:
        """Create the top panel with graph."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Graph group
        graph_group = ModernGroupBox("Real-time Data Visualization")
        graph_layout = QVBoxLayout(graph_group)
        graph_layout.setSpacing(8)
        
        # Graph widget
        self.graph_widget = RealTimeGraphWidget(self.graph_manager)
        graph_layout.addWidget(self.graph_widget)
        
        layout.addWidget(graph_group)
        return panel
    
    def create_bottom_panel(self) -> QWidget:
        """Create the bottom panel with log and statistics."""
        panel = QWidget()
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Log group (left side)
        log_group = ModernGroupBox("Application Log")
        log_layout = QVBoxLayout(log_group)
        log_layout.setSpacing(8)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        log_layout.addWidget(self.log_text)
        
        layout.addWidget(log_group)
        
        # Statistics group (right side)
        stats_group = ModernGroupBox("Data Statistics")
        stats_layout = QVBoxLayout(stats_group)
        stats_layout.setSpacing(8)
        
        self.stats_label = QLabel("No data available")
        self.stats_label.setStyleSheet("""
            QLabel {
                padding: 10px;
                background-color: #ecf0f1;
                border-radius: 4px;
                font-family: 'Consolas', monospace;
                font-size: 11px;
            }
        """)
        stats_layout.addWidget(self.stats_label)
        
        layout.addWidget(stats_group)
        
        return panel
    
    def setup_status_bar(self):
        """Set up the status bar."""
        status_bar = self.statusBar()
        if status_bar:
            status_bar.setStyleSheet("""
                QStatusBar {
                    background-color: #2c3e50;
                    color: white;
                    font-size: 11px;
                    padding: 4px;
                }
            """)
            
            # Status label
            self.status_label = QLabel("Ready")
            status_bar.addWidget(self.status_label)
            
            # Measurement count
            self.measurement_count_label = QLabel("Measurements: 0")
            status_bar.addPermanentWidget(self.measurement_count_label)
            
            # Device count
            self.device_count_label = QLabel("Devices: 0")
            status_bar.addPermanentWidget(self.device_count_label)
    
    def setup_menu(self):
        """Set up the menu bar."""
        # Remove all menus for a clean top bar
        self.setMenuBar(QMenuBar(self))
        menubar = self.menuBar()
        if menubar is not None:
            menubar.clear()
        # Do not add any menus or actions
    
    def setup_connections(self):
        """Set up signal connections."""
        if self.device_table:
            self.device_table.device_config_changed.connect(self.on_device_config_changed)
            self.device_table.device_added.connect(self.on_device_added)
            self.device_table.device_removed.connect(self.on_device_removed)
    
    def add_device(self):
        """Add a new device to the table."""
        if self.device_table:
            row = self.device_table.add_device_row()
            self.device_table.selectRow(row)
            self.logger.info("Added new device row")
    
    def remove_device(self):
        """Remove the selected device from the table."""
        if not self.device_table:
            return
        current_row = self.device_table.currentRow()
        if current_row >= 0:
            item = self.device_table.item(current_row, 0)
            device_name = item.text() if item else ""
            if device_name:
                # Disconnect device if connected
                self.device_manager.disconnect_device(device_name)
            
            self.device_table.remove_device_row(current_row)
        else:
            QMessageBox.information(self, "No Selection", "Please select a device to remove.")
    
    def connect_all_devices(self):
        """Connect all configured devices."""
        if not self.device_table:
            return
        configs = self.device_table.get_device_configs()
        connected_count = 0
        
        for device_name, config in configs.items():
            if config.address.strip():
                if self.device_manager.connect_device(device_name, config.address):
                    connected_count += 1
                    # Add device config to device manager
                    self.device_manager.add_device_config(config)
        
        if connected_count > 0:
            QMessageBox.information(self, "Connection Status", 
                                  f"Successfully connected to {connected_count} device(s).")
        else:
            QMessageBox.warning(self, "Connection Status", "No devices were connected.")
        self.update_connect_toggle_button()
    
    def disconnect_all_devices(self):
        """Disconnect all devices."""
        devices = list(self.device_manager.devices.keys())
        for device_name in devices:
            self.device_manager.disconnect_device(device_name)
        
        QMessageBox.information(self, "Disconnection Status", 
                              f"Disconnected from {len(devices)} device(s).")
        self.update_connect_toggle_button()
    
    def toggle_acquisition(self):
        """Toggle data acquisition on/off."""
        if self.is_acquiring:
            self.stop_acquisition()
        else:
            self.start_acquisition()
    
    def start_acquisition(self):
        """Start data acquisition."""
        if not self.device_table:
            QMessageBox.warning(self, "No Device Table", "Device table not initialized.")
            return
        configs = self.device_table.get_device_configs()
        enabled_configs = {name: config for name, config in configs.items() 
                          if config.enabled and name in self.device_manager.devices}
        
        if not enabled_configs:
            QMessageBox.warning(self, "No Devices", 
                              "No enabled devices are connected. Please connect devices first.")
            return
        
        # Add configurations to device manager
        for config in enabled_configs.values():
            self.device_manager.add_device_config(config)
        
        # Start acquisition
        interval = self.interval_spin.value()
        if self.device_manager.start_acquisition(interval):
            self.is_acquiring = True
            if self.start_stop_button:
                self.start_stop_button.setText("⏹️ Stop Acquisition")
            if self.progress_bar:
                self.progress_bar.setVisible(True)
            if self.status_label:
                self.status_label.setText("Acquiring data...")
            self.logger.info(f"Started acquisition with {interval}ms interval")
        else:
            QMessageBox.critical(self, "Acquisition Error", "Failed to start acquisition.")
    
    def stop_acquisition(self):
        """Stop data acquisition."""
        if self.device_manager.stop_acquisition():
            self.is_acquiring = False
            if self.start_stop_button:
                self.start_stop_button.setText("▶️ Start Acquisition")
            if self.progress_bar:
                self.progress_bar.setVisible(False)
            if self.status_label:
                self.status_label.setText("Acquisition stopped")
            self.logger.info("Stopped acquisition")
        else:
            QMessageBox.critical(self, "Acquisition Error", "Failed to stop acquisition.")
    
    def export_data(self):
        """Export collected data."""
        if self.data_handler.get_measurement_count() == 0:
            QMessageBox.warning(self, "No Data", "No data available for export.")
            return
        
        format_type = self.export_format_combo.currentText()
        default_name = f"dmm_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if format_type == 'CSV':
            default_name += '.csv'
        elif format_type == 'JSON':
            default_name += '.json'
        else:  # TXT
            default_name += '.txt'
        
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Export Data", default_name,
            f"{format_type} Files (*.{format_type.lower()})"
        )
        
        if filepath:
            if self.data_handler.export_data(filepath, format_type):
                QMessageBox.information(self, "Export Success", 
                                      f"Data exported successfully to {filepath}")
            else:
                QMessageBox.critical(self, "Export Error", "Failed to export data.")
    
    def clear_data(self):
        """Clear all collected data."""
        reply = QMessageBox.question(self, "Clear Data", 
                                   "Are you sure you want to clear all collected data?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self.data_handler.clear_measurements()
            self.graph_manager.clear_data()
            self.update_status()
            self.logger.info("Cleared all data")
    
    def refresh_devices(self):
        """Refresh the list of available GPIB devices."""
        devices = self.device_manager.list_available_devices()
        if devices:
            device_list = "\n".join(devices)
            QMessageBox.information(self, "Available Devices", 
                                  f"Found {len(devices)} GPIB device(s):\n\n{device_list}")
        else:
            QMessageBox.warning(self, "No Devices", "No GPIB devices found.")
    
    def on_measurement_received(self, device_name: str, value: float, unit: str, status: str):
        """Handle received measurement data."""
        # Add to data handler
        config = self.device_manager.device_configs.get(device_name)
        user_label = config.user_label if config else ""
        function = config.function if config else ""
        
        self.data_handler.add_measurement(device_name, function, value, unit, status, user_label)
        
        # Add to graph manager
        self.graph_manager.add_data_point(device_name, value)
        
        # Update log
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_message = f"[{timestamp}] {device_name}: {value:.6f} {unit} ({status})"
        if self.log_text:
            self.log_text.append(log_message)
            
            # Auto-scroll log
            scrollbar = self.log_text.verticalScrollBar()
            if scrollbar:
                scrollbar.setValue(scrollbar.maximum())
    
    def on_device_error(self, device_name: str, error_message: str):
        """Handle device errors."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_message = f"[{timestamp}] ERROR {device_name}: {error_message}"
        if self.log_text:
            self.log_text.append(log_message)
        
        # Show error in status bar temporarily
        if self.status_label:
            self.status_label.setText(f"Error: {device_name} - {error_message}")
            QTimer.singleShot(5000, lambda: self.status_label.setText("Ready") if self.status_label else None)
    
    def on_device_connected(self, device_name: str, device_id: str):
        """Handle device connection."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_message = f"[{timestamp}] Connected: {device_name} ({device_id})"
        if self.log_text:
            self.log_text.append(log_message)
    
    def on_device_disconnected(self, device_name: str):
        """Handle device disconnection."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_message = f"[{timestamp}] Disconnected: {device_name}"
        if self.log_text:
            self.log_text.append(log_message)
    
    def on_device_config_changed(self, device_name: str, config: DeviceConfig):
        """Handle device configuration changes."""
        self.device_manager.add_device_config(config)
        self.logger.info(f"Updated config for {device_name}")
    
    def on_device_added(self, device_name: str, config: DeviceConfig):
        """Handle device addition."""
        self.logger.info(f"Added device: {device_name}")
    
    def on_device_removed(self, device_name: str):
        """Handle device removal."""
        self.logger.info(f"Removed device: {device_name}")
    
    def update_status(self):
        """Update status bar information."""
        # Update measurement count
        count = self.data_handler.get_measurement_count()
        if self.measurement_count_label:
            self.measurement_count_label.setText(f"Measurements: {count}")
        
        # Update device count
        device_count = len(self.device_manager.devices)
        if self.device_count_label:
            self.device_count_label.setText(f"Devices: {device_count}")
        
        # Update progress bar if acquiring
        if self.is_acquiring and self.progress_bar:
            self.progress_bar.setValue((count % 100))
    
    def toggle_connect_all(self):
        """Toggle connect/disconnect all devices."""
        if self.any_devices_connected():
            self.disconnect_all_devices()
        else:
            self.connect_all_devices()
        self.update_connect_toggle_button()

    def any_devices_connected(self) -> bool:
        """Return True if any devices are currently connected."""
        return len(self.device_manager.devices) > 0

    def update_connect_toggle_button(self):
        """Update the connect/disconnect all toggle button label and icon."""
        if self.any_devices_connected():
            self.connect_toggle_button.setText("🔌 Disconnect All")
        else:
            self.connect_toggle_button.setText("🔌 Connect All")
    
    def closeEvent(self, event):
        """Handle application close event."""
        # Stop acquisition
        if self.is_acquiring:
            self.device_manager.stop_acquisition()
        
        # Clean up device manager
        self.device_manager.cleanup()
        
        self.logger.info("Application closing")
        event.accept() 