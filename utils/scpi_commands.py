"""
SCPI Command definitions for DMM Logger application.
"""

from typing import Dict, List, Optional


class SCPICommands:
    """
    Manages SCPI commands for different measurement functions.
    """
    
    # Measurement functions and their corresponding SCPI commands
    MEASUREMENT_FUNCTIONS = {
        'DC Voltage': {
            'command': 'MEAS:VOLT:DC?',
            'description': 'Measure DC voltage',
            'unit': 'V',
            'ranges': ['AUTO', '0.1', '1', '10', '100', '1000']
        },
        'AC Voltage': {
            'command': 'MEAS:VOLT:AC?',
            'description': 'Measure AC voltage',
            'unit': 'V',
            'ranges': ['AUTO', '0.1', '1', '10', '100', '750']
        },
        'DC Current': {
            'command': 'MEAS:CURR:DC?',
            'description': 'Measure DC current',
            'unit': 'A',
            'ranges': ['AUTO', '0.001', '0.01', '0.1', '1', '3']
        },
        'AC Current': {
            'command': 'MEAS:CURR:AC?',
            'description': 'Measure AC current',
            'unit': 'A',
            'ranges': ['AUTO', '0.001', '0.01', '0.1', '1', '3']
        },
        'Resistance (2-wire)': {
            'command': 'MEAS:RES?',
            'description': 'Measure resistance (2-wire)',
            'unit': 'Ω',
            'ranges': ['AUTO', '100', '1K', '10K', '100K', '1M', '10M', '100M']
        },
        'Resistance (4-wire)': {
            'command': 'MEAS:FRES?',
            'description': 'Measure resistance (4-wire)',
            'unit': 'Ω',
            'ranges': ['AUTO', '100', '1K', '10K', '100K', '1M', '10M', '100M']
        },
        'Frequency': {
            'command': 'MEAS:FREQ?',
            'description': 'Measure frequency',
            'unit': 'Hz',
            'ranges': ['AUTO', '1', '10', '100', '1K', '10K', '100K', '1M']
        },
        'Temperature': {
            'command': 'MEAS:TEMP?',
            'description': 'Measure temperature',
            'unit': '°C',
            'ranges': ['AUTO', 'RTD', 'THERMISTOR', 'THERMOCOUPLE']
        }
    }
    
    # Common SCPI commands
    COMMON_COMMANDS = {
        'Reset': '*RST',
        'Clear Status': '*CLS',
        'Self Test': '*TST?',
        'Identification': '*IDN?',
        'Operation Complete': '*OPC?',
        'Wait': '*WAI'
    }
    
    # Configuration commands
    CONFIG_COMMANDS = {
        'Set Range': 'CONF:{function}:{range}',
        'Set Resolution': 'CONF:{function}:{resolution}',
        'Set Integration Time': 'CONF:{function}:NPLC {nplc}',
        'Set Auto Zero': 'CONF:{function}:AZER {state}',
        'Set Filter': 'CONF:{function}:FILT {state}'
    }
    
    @classmethod
    def get_function_list(cls) -> List[str]:
        """
        Get list of available measurement functions.
        
        Returns:
            List of function names
        """
        return list(cls.MEASUREMENT_FUNCTIONS.keys())
    
    @classmethod
    def get_command_for_function(cls, function: str) -> Optional[str]:
        """
        Get SCPI command for a specific measurement function.
        
        Args:
            function: Measurement function name
            
        Returns:
            SCPI command string or None if function not found
        """
        if function in cls.MEASUREMENT_FUNCTIONS:
            return cls.MEASUREMENT_FUNCTIONS[function]['command']
        return None
    
    @classmethod
    def get_unit_for_function(cls, function: str) -> Optional[str]:
        """
        Get unit for a specific measurement function.
        
        Args:
            function: Measurement function name
            
        Returns:
            Unit string or None if function not found
        """
        if function in cls.MEASUREMENT_FUNCTIONS:
            return cls.MEASUREMENT_FUNCTIONS[function]['unit']
        return None
    
    @classmethod
    def get_ranges_for_function(cls, function: str) -> List[str]:
        """
        Get available ranges for a specific measurement function.
        
        Args:
            function: Measurement function name
            
        Returns:
            List of available ranges
        """
        if function in cls.MEASUREMENT_FUNCTIONS:
            return cls.MEASUREMENT_FUNCTIONS[function]['ranges']
        return []
    
    @classmethod
    def get_description_for_function(cls, function: str) -> Optional[str]:
        """
        Get description for a specific measurement function.
        
        Args:
            function: Measurement function name
            
        Returns:
            Description string or None if function not found
        """
        if function in cls.MEASUREMENT_FUNCTIONS:
            return cls.MEASUREMENT_FUNCTIONS[function]['description']
        return None
    
    @classmethod
    def format_command_with_range(cls, function: str, range_value: str) -> Optional[str]:
        """
        Format SCPI command with specific range.
        
        Args:
            function: Measurement function name
            range_value: Range value to set
            
        Returns:
            Formatted SCPI command or None if function not found
        """
        base_command = cls.get_command_for_function(function)
        if base_command and range_value != 'AUTO':
            # Convert measurement command to configuration command
            if 'MEAS:' in base_command:
                config_cmd = base_command.replace('MEAS:', 'CONF:')
                return f"{config_cmd} {range_value}"
        return base_command
    
    @classmethod
    def get_common_command(cls, command_name: str) -> Optional[str]:
        """
        Get common SCPI command by name.
        
        Args:
            command_name: Name of the common command
            
        Returns:
            SCPI command string or None if command not found
        """
        return cls.COMMON_COMMANDS.get(command_name)
    
    @classmethod
    def get_all_common_commands(cls) -> Dict[str, str]:
        """
        Get all common SCPI commands.
        
        Returns:
            Dictionary of common commands
        """
        return cls.COMMON_COMMANDS.copy() 