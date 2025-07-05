"""
Graph manager for real-time plotting and data visualization.
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import numpy as np

from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton, QLabel
import pyqtgraph as pg

from utils.logger import LoggerMixin


class GraphManager(QObject, LoggerMixin):
    """
    Manages real-time plotting and data visualization.
    """
    
    # Signals
    graph_updated = pyqtSignal()
    data_point_added = pyqtSignal(str, float, datetime)  # device_name, value, timestamp
    
    def __init__(self):
        """Initialize graph manager."""
        super().__init__()
        LoggerMixin.__init__(self)
        
        self.data: Dict[str, List[Tuple[datetime, float]]] = {}
        self.max_points = 1000  # Maximum data points to keep per device
        self.time_window = timedelta(minutes=10)  # Time window for display
        
        self.log_info("GraphManager initialized")
    
    def add_data_point(self, device_name: str, value: float, timestamp: Optional[datetime] = None):
        """
        Add a data point for a device.
        
        Args:
            device_name: Name of the device
            value: Measured value
            timestamp: Timestamp (defaults to current time)
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        if device_name not in self.data:
            self.data[device_name] = []
        
        self.data[device_name].append((timestamp, value))
        
        # Limit data points
        if len(self.data[device_name]) > self.max_points:
            self.data[device_name] = self.data[device_name][-self.max_points:]
        
        self.data_point_added.emit(device_name, value, timestamp)
        self.graph_updated.emit()
        
        self.log_debug(f"Added data point: {device_name} = {value} at {timestamp}")
    
    def get_data_for_device(self, device_name: str, 
                          time_window: Optional[timedelta] = None) -> Tuple[List[datetime], List[float]]:
        """
        Get data for a specific device within a time window.
        
        Args:
            device_name: Name of the device
            time_window: Time window to filter data (optional)
            
        Returns:
            Tuple of (timestamps, values)
        """
        if device_name not in self.data:
            return [], []
        
        data = self.data[device_name]
        
        if time_window:
            cutoff_time = datetime.now() - time_window
            data = [(ts, val) for ts, val in data if ts >= cutoff_time]
        
        if not data:
            return [], []
        
        timestamps, values = zip(*data)
        return list(timestamps), list(values)
    
    def get_all_data(self, time_window: Optional[timedelta] = None) -> Dict[str, Tuple[List[datetime], List[float]]]:
        """
        Get data for all devices within a time window.
        
        Args:
            time_window: Time window to filter data (optional)
            
        Returns:
            Dictionary mapping device names to (timestamps, values) tuples
        """
        result = {}
        for device_name in self.data.keys():
            result[device_name] = self.get_data_for_device(device_name, time_window)
        return result
    
    def clear_data(self, device_name: Optional[str] = None):
        """
        Clear data for a device or all devices.
        
        Args:
            device_name: Name of the device to clear (None for all devices)
        """
        if device_name is None:
            self.data.clear()
            self.log_info("Cleared all graph data")
        elif device_name in self.data:
            self.data[device_name].clear()
            self.log_info(f"Cleared data for {device_name}")
        
        self.graph_updated.emit()
    
    def get_device_list(self) -> List[str]:
        """
        Get list of devices with data.
        
        Returns:
            List of device names
        """
        return list(self.data.keys())
    
    def get_data_statistics(self, device_name: str) -> Dict[str, Any]:
        """
        Get statistics for a device's data.
        
        Args:
            device_name: Name of the device
            
        Returns:
            Dictionary with statistics
        """
        if device_name not in self.data or not self.data[device_name]:
            return {
                'count': 0,
                'min': None,
                'max': None,
                'mean': None,
                'std': None
            }
        
        values = [val for _, val in self.data[device_name]]
        
        return {
            'count': len(values),
            'min': min(values) if values else None,
            'max': max(values) if values else None,
            'mean': np.mean(values) if values else None,
            'std': np.std(values) if values else None
        }


class RealTimeGraphWidget(QWidget):
    """
    Widget for displaying real-time graphs.
    """
    
    def __init__(self, graph_manager: GraphManager):
        """Initialize the graph widget."""
        super().__init__()
        
        self.graph_manager = graph_manager
        self.plot_widget = None
        self.plot_curves = {}
        self.device_colors = {}
        
        self.setup_ui()
        self.setup_connections()
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_graph)
        self.update_timer.start(100)  # Update every 100ms
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout()
        
        # Control panel
        control_layout = QHBoxLayout()
        
        # Device selector
        self.device_combo = QComboBox()
        self.device_combo.addItem("All Devices")
        control_layout.addWidget(QLabel("Device:"))
        control_layout.addWidget(self.device_combo)
        
        # Time window selector
        self.time_window_combo = QComboBox()
        self.time_window_combo.addItems(["1 min", "5 min", "10 min", "30 min", "1 hour", "All"])
        self.time_window_combo.setCurrentText("10 min")
        control_layout.addWidget(QLabel("Time Window:"))
        control_layout.addWidget(self.time_window_combo)
        
        # Clear button
        self.clear_button = QPushButton("Clear Graph")
        control_layout.addWidget(self.clear_button)
        
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        # Plot widget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setLabel('left', 'Value')
        self.plot_widget.setLabel('bottom', 'Time')
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.addLegend()
        
        layout.addWidget(self.plot_widget)
        
        self.setLayout(layout)
    
    def setup_connections(self):
        """Set up signal connections."""
        self.graph_manager.graph_updated.connect(self.update_graph)
        self.clear_button.clicked.connect(self.clear_graph)
        self.device_combo.currentTextChanged.connect(self.update_graph)
        self.time_window_combo.currentTextChanged.connect(self.update_graph)
    
    def update_graph(self):
        """Update the graph with current data."""
        if self.plot_widget is None:
            return
            
        try:
            # Get time window
            time_window_text = self.time_window_combo.currentText()
            if time_window_text == "All":
                time_window = None
            else:
                minutes = int(time_window_text.split()[0])
                if "hour" in time_window_text:
                    minutes *= 60
                time_window = timedelta(minutes=minutes)
            
            # Get data
            all_data = self.graph_manager.get_all_data(time_window)
            
            # Clear existing curves
            self.plot_widget.clear()
            
            # Add curves for each device
            for device_name, (timestamps, values) in all_data.items():
                if not timestamps or not values:
                    continue
                
                # Convert timestamps to seconds from start
                start_time = timestamps[0]
                time_seconds = [(ts - start_time).total_seconds() for ts in timestamps]
                
                # Get or create color for device
                if device_name not in self.device_colors:
                    self.device_colors[device_name] = self._get_device_color(device_name)
                
                # Create curve
                pen = pg.mkPen(color=self.device_colors[device_name], width=2)
                curve = self.plot_widget.plot(time_seconds, values, 
                                            name=device_name, pen=pen)
                self.plot_curves[device_name] = curve
            
            # Update axis labels
            if time_window:
                self.plot_widget.setLabel('bottom', f'Time (seconds, last {time_window_text})')
            else:
                self.plot_widget.setLabel('bottom', 'Time (seconds)')
                
        except Exception as e:
            self.graph_manager.log_error(f"Failed to update graph: {e}")
    
    def clear_graph(self):
        """Clear the graph data."""
        self.graph_manager.clear_data()
        if self.plot_widget:
            self.plot_widget.clear()
    
    def _get_device_color(self, device_name: str) -> Tuple[int, int, int]:
        """
        Get a color for a device.
        
        Args:
            device_name: Name of the device
            
        Returns:
            RGB color tuple
        """
        # Simple color generation based on device name
        colors = [
            (255, 0, 0),    # Red
            (0, 255, 0),    # Green
            (0, 0, 255),    # Blue
            (255, 255, 0),  # Yellow
            (255, 0, 255),  # Magenta
            (0, 255, 255),  # Cyan
            (255, 128, 0),  # Orange
            (128, 0, 255),  # Purple
        ]
        
        index = hash(device_name) % len(colors)
        return colors[index]
    
    def update_device_list(self):
        """Update the device list in the combo box."""
        current_text = self.device_combo.currentText()
        
        self.device_combo.clear()
        self.device_combo.addItem("All Devices")
        
        devices = self.graph_manager.get_device_list()
        for device in devices:
            self.device_combo.addItem(device)
        
        # Restore selection if possible
        index = self.device_combo.findText(current_text)
        if index >= 0:
            self.device_combo.setCurrentIndex(index) 