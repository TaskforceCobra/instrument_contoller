"""
Device table widget for managing DMM devices and configurations.
"""

from typing import Dict, List, Optional, Any
from PyQt6.QtWidgets import (QTableWidget, QTableWidgetItem, QComboBox, 
                             QLineEdit, QSpinBox, QHeaderView, QMessageBox)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont

from core.device_manager import DeviceConfig
from utils.scpi_commands import SCPICommands
from utils.logger import LoggerMixin


class FunctionComboBox(QComboBox):
    """ComboBox for selecting measurement functions."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_functions()
    
    def setup_functions(self):
        """Set up available measurement functions."""
        functions = SCPICommands.get_function_list()
        self.addItems(functions)
    
    def get_current_function(self) -> str:
        """Get currently selected function."""
        return self.currentText()
    
    def set_function(self, function: str):
        """Set the selected function."""
        index = self.findText(function)
        if index >= 0:
            self.setCurrentIndex(index)


class RangeComboBox(QComboBox):
    """ComboBox for selecting measurement ranges."""
    
    def __init__(self, function: str = "DC Voltage", parent=None):
        super().__init__(parent)
        self.setup_ranges(function)
    
    def setup_ranges(self, function: str):
        """Set up available ranges for the given function."""
        self.clear()
        ranges = SCPICommands.get_ranges_for_function(function)
        self.addItems(ranges)
    
    def get_current_range(self) -> str:
        """Get currently selected range."""
        return self.currentText()
    
    def set_range(self, range_value: str):
        """Set the selected range."""
        index = self.findText(range_value)
        if index >= 0:
            self.setCurrentIndex(index)


class DeviceTableWidget(QTableWidget, LoggerMixin):
    """
    Table widget for managing DMM devices and their configurations.
    """
    
    # Signals
    device_config_changed = pyqtSignal(str, DeviceConfig)  # device_name, config
    device_added = pyqtSignal(str, DeviceConfig)           # device_name, config
    device_removed = pyqtSignal(str)                       # device_name
    
    def __init__(self, parent=None):
        """Initialize the device table widget."""
        super().__init__(parent)
        LoggerMixin.__init__(self)
        
        self.device_configs: Dict[str, DeviceConfig] = {}
        self.function_combos: Dict[int, FunctionComboBox] = {}
        self.range_combos: Dict[int, RangeComboBox] = {}
        
        self.setup_table()
        self.setup_connections()
        
        self.log_info("DeviceTableWidget initialized")
    
    def setup_table(self):
        """Set up the table structure."""
        # Set up columns
        headers = [
            "Device Name", "GPIB Address", "Function", "Range", 
            "Samples", "User Label", "SCPI Command", "Enabled"
        ]
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        
        # Set up rows
        self.setRowCount(0)
        
        # Configure table properties
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        
        # Set column widths
        header = self.horizontalHeader()
        if header:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Device Name
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # GPIB Address
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Function
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Range
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Samples
            header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)          # User Label
            header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)          # SCPI Command
            header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents) # Enabled
        
        # Set font
        font = QFont("Consolas", 9)
        self.setFont(font)
    
    def setup_connections(self):
        """Set up signal connections."""
        self.cellChanged.connect(self.on_cell_changed)
    
    def add_device_row(self, device_name: str = "", address: str = "", 
                      function: str = "DC Voltage", range_value: str = "AUTO",
                      samples: int = 1, user_label: str = "", enabled: bool = True) -> int:
        """
        Add a new device row to the table.
        
        Args:
            device_name: Name of the device
            address: GPIB address
            function: Measurement function
            range_value: Measurement range
            samples: Number of samples
            user_label: User-defined label
            enabled: Whether device is enabled
            
        Returns:
            Row index of the added device
        """
        row = self.rowCount()
        self.insertRow(row)
        
        # Device Name
        name_item = QTableWidgetItem(device_name)
        self.setItem(row, 0, name_item)
        
        # GPIB Address
        address_item = QTableWidgetItem(address)
        self.setItem(row, 1, address_item)
        
        # Function (ComboBox)
        function_combo = FunctionComboBox()
        function_combo.set_function(function)
        function_combo.currentTextChanged.connect(
            lambda text, r=row: self.on_function_changed(r, text)
        )
        self.setCellWidget(row, 2, function_combo)
        self.function_combos[row] = function_combo
        
        # Range (ComboBox)
        range_combo = RangeComboBox(function)
        range_combo.set_range(range_value)
        range_combo.currentTextChanged.connect(
            lambda text, r=row: self.on_range_changed(r, text)
        )
        self.setCellWidget(row, 3, range_combo)
        self.range_combos[row] = range_combo
        
        # Samples (SpinBox)
        samples_spin = QSpinBox()
        samples_spin.setRange(1, 1000)
        samples_spin.setValue(samples)
        samples_spin.valueChanged.connect(
            lambda value, r=row: self.on_samples_changed(r, value)
        )
        self.setCellWidget(row, 4, samples_spin)
        
        # User Label
        label_item = QTableWidgetItem(user_label)
        self.setItem(row, 5, label_item)
        
        # SCPI Command
        scpi_command = SCPICommands.get_command_for_function(function)
        scpi_item = QTableWidgetItem(scpi_command or "")
        self.setItem(row, 6, scpi_item)
        
        # Enabled (CheckBox)
        enabled_item = QTableWidgetItem()
        enabled_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
        enabled_item.setCheckState(Qt.CheckState.Checked if enabled else Qt.CheckState.Unchecked)
        self.setItem(row, 7, enabled_item)
        
        # Create device config
        config = DeviceConfig(
            name=device_name,
            address=address,
            function=function,
            range_value=range_value,
            samples=samples,
            user_label=user_label,
            scpi_command=scpi_command or "",
            enabled=enabled
        )
        
        if device_name:
            self.device_configs[device_name] = config
        
        self.log_info(f"Added device row {row}: {device_name}")
        return row
    
    def remove_device_row(self, row: int) -> bool:
        """
        Remove a device row from the table.
        
        Args:
            row: Row index to remove
            
        Returns:
            True if successful, False otherwise
        """
        if row < 0 or row >= self.rowCount():
            return False
        
        try:
            item = self.item(row, 0)
            device_name = item.text() if item else ""
            
            # Remove from table
            self.removeRow(row)
            
            # Remove from configs
            if device_name in self.device_configs:
                del self.device_configs[device_name]
            
            # Remove from combo boxes
            if row in self.function_combos:
                del self.function_combos[row]
            if row in self.range_combos:
                del self.range_combos[row]
            
            # Update combo box indices
            self._update_combo_indices(row)
            
            self.device_removed.emit(device_name)
            self.log_info(f"Removed device row {row}: {device_name}")
            return True
            
        except Exception as e:
            self.log_error(f"Failed to remove device row {row}: {e}")
            return False
    
    def _update_combo_indices(self, removed_row: int):
        """Update combo box indices after row removal."""
        # Update function combos
        new_function_combos = {}
        for row, combo in self.function_combos.items():
            if row < removed_row:
                new_function_combos[row] = combo
            elif row > removed_row:
                new_function_combos[row - 1] = combo
        self.function_combos = new_function_combos
        
        # Update range combos
        new_range_combos = {}
        for row, combo in self.range_combos.items():
            if row < removed_row:
                new_range_combos[row] = combo
            elif row > removed_row:
                new_range_combos[row - 1] = combo
        self.range_combos = new_range_combos
    
    def get_device_configs(self) -> Dict[str, DeviceConfig]:
        """
        Get all device configurations from the table.
        
        Returns:
            Dictionary of device configurations
        """
        configs = {}
        
        for row in range(self.rowCount()):
            try:
                item0 = self.item(row, 0)
                device_name = item0.text().strip() if item0 else ""
                if not device_name:
                    continue
                
                item1 = self.item(row, 1)
                address = item1.text().strip() if item1 else ""
                function = self.function_combos[row].get_current_function()
                range_value = self.range_combos[row].get_current_range()
                from PyQt6.QtWidgets import QSpinBox
                widget = self.cellWidget(row, 4)
                samples = widget.value() if isinstance(widget, QSpinBox) else 1
                item5 = self.item(row, 5)
                user_label = item5.text().strip() if item5 else ""
                item6 = self.item(row, 6)
                scpi_command = item6.text().strip() if item6 else ""
                item7 = self.item(row, 7)
                enabled = item7.checkState() == Qt.CheckState.Checked if item7 else False
                
                config = DeviceConfig(
                    name=device_name,
                    address=address,
                    function=function,
                    range_value=range_value,
                    samples=samples,
                    user_label=user_label,
                    scpi_command=scpi_command,
                    enabled=enabled
                )
                
                configs[device_name] = config
                
            except Exception as e:
                self.log_error(f"Failed to get config for row {row}: {e}")
        
        return configs
    
    def update_device_configs(self, configs: Dict[str, DeviceConfig]):
        """
        Update the table with device configurations.
        
        Args:
            configs: Dictionary of device configurations
        """
        # Clear existing rows
        self.setRowCount(0)
        self.function_combos.clear()
        self.range_combos.clear()
        
        # Add rows for each config
        for config in configs.values():
            self.add_device_row(
                device_name=config.name,
                address=config.address,
                function=config.function,
                range_value=config.range_value,
                samples=config.samples,
                user_label=config.user_label,
                enabled=config.enabled
            )
    
    def on_cell_changed(self, row: int, column: int):
        """Handle cell value changes."""
        try:
            item = self.item(row, 0)
            device_name = item.text().strip() if item else ""
            if not device_name:
                return
            
            # Get current config
            config = self.get_device_configs().get(device_name)
            if config:
                self.device_config_changed.emit(device_name, config)
                
        except Exception as e:
            self.log_error(f"Failed to handle cell change at ({row}, {column}): {e}")
    
    def on_function_changed(self, row: int, function: str):
        """Handle function selection change."""
        try:
            # Update SCPI command
            scpi_command = SCPICommands.get_command_for_function(function)
            if scpi_command:
                self.setItem(row, 6, QTableWidgetItem(scpi_command))
            
            # Update range combo
            if row in self.range_combos:
                self.range_combos[row].setup_ranges(function)
            
            # Trigger cell change
            self.on_cell_changed(row, 2)
            
        except Exception as e:
            self.log_error(f"Failed to handle function change for row {row}: {e}")
    
    def on_range_changed(self, row: int, range_value: str):
        """Handle range selection change."""
        try:
            # Update SCPI command with range
            if row in self.function_combos:
                function = self.function_combos[row].get_current_function()
                scpi_command = SCPICommands.format_command_with_range(function, range_value)
                if scpi_command:
                    self.setItem(row, 6, QTableWidgetItem(scpi_command))
            
            # Trigger cell change
            self.on_cell_changed(row, 3)
            
        except Exception as e:
            self.log_error(f"Failed to handle range change for row {row}: {e}")
    
    def on_samples_changed(self, row: int, samples: int):
        """Handle samples value change."""
        try:
            self.on_cell_changed(row, 4)
        except Exception as e:
            self.log_error(f"Failed to handle samples change for row {row}: {e}")
    
    def validate_device_config(self, device_name: str, address: str) -> bool:
        """
        Validate device configuration.
        
        Args:
            device_name: Name of the device
            address: GPIB address
            
        Returns:
            True if valid, False otherwise
        """
        if not device_name.strip():
            QMessageBox.warning(self, "Validation Error", "Device name cannot be empty.")
            return False
        
        if not address.strip():
            QMessageBox.warning(self, "Validation Error", "GPIB address cannot be empty.")
            return False
        
        # Check for duplicate device names
        for row in range(self.rowCount()):
            if row != self.currentRow():
                item = self.item(row, 0)
                existing_name = item.text().strip() if item else ""
                if existing_name == device_name.strip():
                    QMessageBox.warning(self, "Validation Error", 
                                      f"Device name '{device_name}' already exists.")
                    return False
        
        return True 