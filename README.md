# DMM Logger - Digital Multimeter Controller

A professional Windows desktop application for controlling Digital Multimeters (DMMs) via GPIB communication using SCPI commands.

## 🎯 Features

- **Real-time DMM Control**: Interface with multiple DMMs via GPIB using SCPI commands
- **Interactive Data Table**: Editable table with dropdowns for measurement functions
- **Real-time Graphing**: Live plotting of measurement data
- **SCPI Command Management**: Auto-populated and editable SCPI commands
- **Data Export**: Export to CSV, JSON, and TXT formats
- **Error Handling**: Comprehensive error logging and user feedback

## 🚀 Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd instrument_contoller
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python main.py
   ```

## 📋 Requirements

- Python 3.9 or higher
- Windows OS
- GPIB hardware interface (National Instruments GPIB-USB, etc.)
- Compatible DMM devices

## 🏗️ Project Structure

```
instrument_contoller/
├── main.py              # Application entry point
├── ui/
│   ├── __init__.py
│   ├── main_window.py   # Main application window
│   ├── device_table.py  # Device table widget
│   └── graph_widget.py  # Real-time plotting widget
├── core/
│   ├── __init__.py
│   ├── device_manager.py    # DMM connection and SCPI management
│   ├── data_handler.py      # Data processing and export
│   └── graph_manager.py     # Graphing logic
├── utils/
│   ├── __init__.py
│   ├── scpi_commands.py     # SCPI command definitions
│   └── logger.py            # Logging utilities
├── requirements.txt
└── README.md
```

## 🔧 Usage

1. **Connect DMMs**: Ensure your DMMs are connected via GPIB
2. **Add Devices**: Use the device table to add and configure DMMs
3. **Configure Functions**: Select measurement functions from dropdowns
4. **Start Acquisition**: Click "Start" to begin real-time data collection
5. **Monitor Data**: View live graphs and data in the table
6. **Export Data**: Save collected data in your preferred format

## 📊 Supported Measurement Functions

- DC Voltage
- AC Voltage
- Resistance (2-wire and 4-wire)
- DC Current
- AC Current
- Frequency
- Temperature

## 🔌 Supported Export Formats

- CSV (Comma Separated Values)
- JSON (JavaScript Object Notation)
- TXT (Plain Text)

## 🐛 Troubleshooting

- **GPIB Connection Issues**: Ensure proper GPIB drivers are installed
- **Device Not Found**: Check GPIB addresses and connections
- **Permission Errors**: Run as administrator if needed

## 📝 License

This project is licensed under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues.