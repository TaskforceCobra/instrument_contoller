"""
Device manager for handling DMM connections and SCPI communication.
"""

import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime

import pyvisa
from PyQt6.QtCore import QObject, pyqtSignal, QTimer

from utils.scpi_commands import SCPICommands
from utils.logger import LoggerMixin


@dataclass
class DeviceConfig:
    """Configuration for a DMM device."""
    name: str
    address: str
    function: str
    range_value: str
    samples: int
    user_label: str
    scpi_command: str
    enabled: bool = True


@dataclass
class MeasurementData:
    """Measurement data structure."""
    timestamp: datetime
    value: float
    unit: str
    status: str
    device_name: str
    function: str


class DeviceManager(QObject, LoggerMixin):
    """
    Manages DMM device connections and SCPI communication.
    """
    
    # Signals
    device_connected = pyqtSignal(str, str)  # device_name, device_id
    device_disconnected = pyqtSignal(str)    # device_name
    measurement_received = pyqtSignal(str, float, str, str)  # device_name, value, unit, status
    error_occurred = pyqtSignal(str, str)    # device_name, error_message
    
    def __init__(self):
        """Initialize device manager."""
        super().__init__()
        LoggerMixin.__init__(self)
        
        self.rm = None
        self.devices: Dict[str, Any] = {}  # device_name -> pyvisa resource
        self.device_configs: Dict[str, DeviceConfig] = {}
        self.measurement_timer = QTimer()
        self.measurement_timer.timeout.connect(self._acquire_measurements)
        self.is_acquiring = False
        
        self.log_info("DeviceManager initialized")
    
    def initialize_visa(self) -> bool:
        """
        Initialize VISA resource manager.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.rm = pyvisa.ResourceManager()
            self.log_info(f"VISA Resource Manager initialized: {self.rm}")
            return True
        except Exception as e:
            self.log_error(f"Failed to initialize VISA: {e}")
            return False
    
    def list_available_devices(self) -> List[str]:
        """
        List all available GPIB devices.
        
        Returns:
            List of device addresses
        """
        if not self.rm:
            self.log_error("VISA not initialized")
            return []
        
        try:
            devices = self.rm.list_resources()
            gpib_devices = [dev for dev in devices if 'GPIB' in dev]
            self.log_info(f"Found {len(gpib_devices)} GPIB devices: {gpib_devices}")
            return gpib_devices
        except Exception as e:
            self.log_error(f"Failed to list devices: {e}")
            return []
    
    def connect_device(self, device_name: str, address: str) -> bool:
        """
        Connect to a DMM device.
        
        Args:
            device_name: Name for the device
            address: GPIB address
            
        Returns:
            True if successful, False otherwise
        """
        if not self.rm:
            self.log_error("VISA not initialized")
            return False
        
        try:
            # Open connection
            device = self.rm.open_resource(address)
            device.timeout = 5000  # 5 second timeout
            
            # Test connection
            device_id = device.query('*IDN?').strip()  # type: ignore
            
            self.devices[device_name] = device
            self.log_info(f"Connected to {device_name} at {address}: {device_id}")
            
            # Emit signal
            self.device_connected.emit(device_name, device_id)
            
            return True
            
        except Exception as e:
            self.log_error(f"Failed to connect to {device_name} at {address}: {e}")
            self.error_occurred.emit(device_name, str(e))
            return False
    
    def disconnect_device(self, device_name: str) -> bool:
        """
        Disconnect from a DMM device.
        
        Args:
            device_name: Name of the device to disconnect
            
        Returns:
            True if successful, False otherwise
        """
        if device_name not in self.devices:
            self.log_warning(f"Device {device_name} not found")
            return False
        
        try:
            device = self.devices[device_name]
            device.close()
            del self.devices[device_name]
            
            # Remove config if exists
            if device_name in self.device_configs:
                del self.device_configs[device_name]
            
            self.log_info(f"Disconnected from {device_name}")
            self.device_disconnected.emit(device_name)
            
            return True
            
        except Exception as e:
            self.log_error(f"Failed to disconnect {device_name}: {e}")
            return False
    
    def add_device_config(self, config: DeviceConfig) -> bool:
        """
        Add or update device configuration.
        
        Args:
            config: Device configuration
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.device_configs[config.name] = config
            self.log_info(f"Added/updated config for {config.name}: {config.function}")
            return True
        except Exception as e:
            self.log_error(f"Failed to add config for {config.name}: {e}")
            return False
    
    def remove_device_config(self, device_name: str) -> bool:
        """
        Remove device configuration.
        
        Args:
            device_name: Name of the device
            
        Returns:
            True if successful, False otherwise
        """
        if device_name in self.device_configs:
            del self.device_configs[device_name]
            self.log_info(f"Removed config for {device_name}")
            return True
        return False
    
    def start_acquisition(self, interval_ms: int = 1000) -> bool:
        """
        Start data acquisition from all configured devices.
        
        Args:
            interval_ms: Measurement interval in milliseconds
            
        Returns:
            True if successful, False otherwise
        """
        if not self.device_configs:
            self.log_warning("No devices configured for acquisition")
            return False
        
        try:
            self.measurement_timer.start(interval_ms)
            self.is_acquiring = True
            self.log_info(f"Started acquisition with {interval_ms}ms interval")
            return True
        except Exception as e:
            self.log_error(f"Failed to start acquisition: {e}")
            return False
    
    def stop_acquisition(self) -> bool:
        """
        Stop data acquisition.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.measurement_timer.stop()
            self.is_acquiring = False
            self.log_info("Stopped acquisition")
            return True
        except Exception as e:
            self.log_error(f"Failed to stop acquisition: {e}")
            return False
    
    def _acquire_measurements(self):
        """Acquire measurements from all configured devices."""
        if not self.is_acquiring:
            return
        
        for device_name, config in self.device_configs.items():
            if not config.enabled or device_name not in self.devices:
                continue
            
            try:
                device = self.devices[device_name]
                
                # Send SCPI command and get response
                response = device.query(config.scpi_command)
                
                # Parse response
                try:
                    value = float(response.strip())
                    unit = SCPICommands.get_unit_for_function(config.function) or ''
                    status = 'OK'
                except ValueError:
                    value = 0.0
                    unit = ''
                    status = 'ERROR'
                    self.log_error(f"Invalid response from {device_name}: {response}")
                
                # Emit measurement signal
                self.measurement_received.emit(device_name, value, unit, status)
                
            except Exception as e:
                self.log_error(f"Failed to acquire measurement from {device_name}: {e}")
                self.error_occurred.emit(device_name, str(e))
    
    def send_command(self, device_name: str, command: str) -> Optional[str]:
        """
        Send a custom SCPI command to a device.
        
        Args:
            device_name: Name of the device
            command: SCPI command to send
            
        Returns:
            Response from device or None if failed
        """
        if device_name not in self.devices:
            self.log_error(f"Device {device_name} not found")
            return None
        
        try:
            device = self.devices[device_name]
            response = device.query(command)
            self.log_info(f"Command sent to {device_name}: {command} -> {response}")
            return response
        except Exception as e:
            self.log_error(f"Failed to send command to {device_name}: {e}")
            self.error_occurred.emit(device_name, str(e))
            return None
    
    def get_device_status(self, device_name: str) -> Dict[str, Any]:
        """
        Get status information for a device.
        
        Args:
            device_name: Name of the device
            
        Returns:
            Dictionary with device status information
        """
        status: Dict[str, Any] = {
            'connected': device_name in self.devices,
            'configured': device_name in self.device_configs,
            'acquiring': self.is_acquiring
        }
        
        if device_name in self.devices:
            try:
                device = self.devices[device_name]
                status['id'] = device.query('*IDN?').strip()  # type: ignore
                status['timeout'] = device.timeout
            except Exception as e:
                status['error'] = str(e)
        
        if device_name in self.device_configs:
            config = self.device_configs[device_name]
            status['function'] = config.function
            status['range'] = config.range_value
            status['samples'] = config.samples
            status['enabled'] = config.enabled
        
        return status
    
    def cleanup(self):
        """Clean up resources."""
        self.stop_acquisition()
        
        for device_name in list(self.devices.keys()):
            self.disconnect_device(device_name)
        
        if self.rm:
            self.rm.close()
        
        self.log_info("DeviceManager cleanup completed") 