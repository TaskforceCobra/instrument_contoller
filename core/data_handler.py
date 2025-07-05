"""
Data handler for processing measurement data and file exports.
"""

import json
import csv
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict

import pandas as pd

from utils.logger import LoggerMixin


@dataclass
class MeasurementRecord:
    """Single measurement record."""
    timestamp: datetime
    device_name: str
    function: str
    value: float
    unit: str
    status: str
    user_label: str


class DataHandler(LoggerMixin):
    """
    Handles data processing, storage, and export functionality.
    """
    
    def __init__(self):
        """Initialize data handler."""
        super().__init__()
        
        self.measurements: List[MeasurementRecord] = []
        self.export_formats = ['CSV', 'JSON', 'TXT']
        
        self.log_info("DataHandler initialized")
    
    def add_measurement(self, device_name: str, function: str, value: float, 
                       unit: str, status: str, user_label: str = "") -> bool:
        """
        Add a new measurement to the data store.
        
        Args:
            device_name: Name of the device
            function: Measurement function
            value: Measured value
            unit: Unit of measurement
            status: Status of measurement
            user_label: User-defined label
            
        Returns:
            True if successful, False otherwise
        """
        try:
            record = MeasurementRecord(
                timestamp=datetime.now(),
                device_name=device_name,
                function=function,
                value=value,
                unit=unit,
                status=status,
                user_label=user_label
            )
            
            self.measurements.append(record)
            self.log_debug(f"Added measurement: {device_name} = {value} {unit}")
            return True
            
        except Exception as e:
            self.log_error(f"Failed to add measurement: {e}")
            return False
    
    def get_measurements(self, device_name: Optional[str] = None, 
                        limit: Optional[int] = None) -> List[MeasurementRecord]:
        """
        Get measurements with optional filtering.
        
        Args:
            device_name: Filter by device name (optional)
            limit: Limit number of records (optional)
            
        Returns:
            List of measurement records
        """
        measurements = self.measurements
        
        if device_name:
            measurements = [m for m in measurements if m.device_name == device_name]
        
        if limit:
            measurements = measurements[-limit:]
        
        return measurements
    
    def get_latest_measurements(self) -> Dict[str, MeasurementRecord]:
        """
        Get the latest measurement for each device.
        
        Returns:
            Dictionary mapping device names to latest measurements
        """
        latest = {}
        for measurement in reversed(self.measurements):
            if measurement.device_name not in latest:
                latest[measurement.device_name] = measurement
        return latest
    
    def clear_measurements(self) -> bool:
        """
        Clear all stored measurements.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            count = len(self.measurements)
            self.measurements.clear()
            self.log_info(f"Cleared {count} measurements")
            return True
        except Exception as e:
            self.log_error(f"Failed to clear measurements: {e}")
            return False
    
    def export_to_csv(self, filepath: str, device_name: Optional[str] = None) -> bool:
        """
        Export measurements to CSV file.
        
        Args:
            filepath: Path to save the CSV file
            device_name: Filter by device name (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            measurements = self.get_measurements(device_name)
            
            if not measurements:
                self.log_warning("No measurements to export")
                return False
            
            # Convert to DataFrame
            data = []
            for m in measurements:
                data.append({
                    'Timestamp': m.timestamp.strftime('%Y-%m-%d %H:%M:%S.%f'),
                    'Device': m.device_name,
                    'Function': m.function,
                    'Value': m.value,
                    'Unit': m.unit,
                    'Status': m.status,
                    'User Label': m.user_label
                })
            
            df = pd.DataFrame(data)
            df.to_csv(filepath, index=False)
            
            self.log_info(f"Exported {len(measurements)} measurements to {filepath}")
            return True
            
        except Exception as e:
            self.log_error(f"Failed to export to CSV: {e}")
            return False
    
    def export_to_json(self, filepath: str, device_name: Optional[str] = None) -> bool:
        """
        Export measurements to JSON file.
        
        Args:
            filepath: Path to save the JSON file
            device_name: Filter by device name (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            measurements = self.get_measurements(device_name)
            
            if not measurements:
                self.log_warning("No measurements to export")
                return False
            
            # Convert to JSON-serializable format
            data = []
            for m in measurements:
                data.append({
                    'timestamp': m.timestamp.isoformat(),
                    'device_name': m.device_name,
                    'function': m.function,
                    'value': m.value,
                    'unit': m.unit,
                    'status': m.status,
                    'user_label': m.user_label
                })
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.log_info(f"Exported {len(measurements)} measurements to {filepath}")
            return True
            
        except Exception as e:
            self.log_error(f"Failed to export to JSON: {e}")
            return False
    
    def export_to_txt(self, filepath: str, device_name: Optional[str] = None) -> bool:
        """
        Export measurements to plain text file.
        
        Args:
            filepath: Path to save the text file
            device_name: Filter by device name (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            measurements = self.get_measurements(device_name)
            
            if not measurements:
                self.log_warning("No measurements to export")
                return False
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("DMM Logger - Measurement Data Export\n")
                f.write("=" * 50 + "\n")
                f.write(f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total Records: {len(measurements)}\n\n")
                
                f.write("Timestamp | Device | Function | Value | Unit | Status | User Label\n")
                f.write("-" * 80 + "\n")
                
                for m in measurements:
                    timestamp_str = m.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                    f.write(f"{timestamp_str} | {m.device_name} | {m.function} | "
                           f"{m.value:.6f} | {m.unit} | {m.status} | {m.user_label}\n")
            
            self.log_info(f"Exported {len(measurements)} measurements to {filepath}")
            return True
            
        except Exception as e:
            self.log_error(f"Failed to export to TXT: {e}")
            return False
    
    def export_data(self, filepath: str, format_type: str, 
                   device_name: Optional[str] = None) -> bool:
        """
        Export data in the specified format.
        
        Args:
            filepath: Path to save the file
            format_type: Export format ('CSV', 'JSON', 'TXT')
            device_name: Filter by device name (optional)
            
        Returns:
            True if successful, False otherwise
        """
        format_type = format_type.upper()
        
        if format_type not in self.export_formats:
            self.log_error(f"Unsupported export format: {format_type}")
            return False
        
        try:
            if format_type == 'CSV':
                return self.export_to_csv(filepath, device_name)
            elif format_type == 'JSON':
                return self.export_to_json(filepath, device_name)
            elif format_type == 'TXT':
                return self.export_to_txt(filepath, device_name)
            else:
                return False
                
        except Exception as e:
            self.log_error(f"Export failed: {e}")
            return False
    
    def get_statistics(self, device_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics about the stored measurements.
        
        Args:
            device_name: Filter by device name (optional)
            
        Returns:
            Dictionary with statistics
        """
        measurements = self.get_measurements(device_name)
        
        if not measurements:
            return {
                'total_measurements': 0,
                'devices': [],
                'functions': [],
                'time_range': None
            }
        
        # Calculate statistics
        devices = list(set(m.device_name for m in measurements))
        functions = list(set(m.function for m in measurements))
        
        timestamps = [m.timestamp for m in measurements]
        time_range = {
            'start': min(timestamps),
            'end': max(timestamps),
            'duration': max(timestamps) - min(timestamps)
        }
        
        # Device-specific statistics
        device_stats = {}
        for device in devices:
            device_measurements = [m for m in measurements if m.device_name == device]
            values = [m.value for m in device_measurements if m.status == 'OK']
            
            if values:
                device_stats[device] = {
                    'count': len(device_measurements),
                    'min': min(values),
                    'max': max(values),
                    'mean': sum(values) / len(values),
                    'last_value': device_measurements[-1].value if device_measurements else None
                }
        
        return {
            'total_measurements': len(measurements),
            'devices': devices,
            'functions': functions,
            'time_range': time_range,
            'device_stats': device_stats
        }
    
    def get_measurement_count(self) -> int:
        """
        Get total number of stored measurements.
        
        Returns:
            Number of measurements
        """
        return len(self.measurements) 