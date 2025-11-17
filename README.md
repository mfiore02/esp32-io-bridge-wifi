# ESP32 IO Bridge WiFi

MicroPython-based firmware that provides WiFi connectivity and IO bridging functionality for ESP32 microcontrollers.

## Features

- WiFi Station and Access Point modes
- GPIO control via network interface
- Web-based control interface
- Configurable via JSON
- Comprehensive logging system
- Modular, reusable code architecture

## Project Status

**Current Phase**: Foundation Complete ✓

### Completed
- ✓ Project structure and directory organization
- ✓ Logger utility module with multiple log levels
- ✓ Configuration management with JSON support
- ✓ Boot initialization script
- ✓ Main application entry point
- ✓ Deployment automation script

### In Progress
- WiFi connectivity modules
- IO bridge functionality
- Web server for remote access

## Quick Start

### Prerequisites

1. **ESP32 with MicroPython firmware installed**
   - Download firmware from: https://micropython.org/download/ESP32_GENERIC/
   - Flash using esptool: `esptool.py --chip esp32 --port /dev/ttyUSB0 erase_flash`
   - Flash firmware: `esptool.py --chip esp32 --port /dev/ttyUSB0 write_flash -z 0x1000 firmware.bin`

2. **Development tools**
   - Python 3.9+
   - mpremote: `pip install mpremote`
   - esptool: `pip install esptool`

### Configuration

Edit `src/config.json` and update WiFi credentials:

```json
{
  "wifi": {
    "ssid": "YOUR_WIFI_SSID",
    "password": "YOUR_WIFI_PASSWORD"
  }
}
```

### Deployment

Deploy to your ESP32 device:

```bash
# Make sure your ESP32 is connected via USB
./tools/deploy.sh /dev/ttyUSB0
```

### Manual Deployment

```bash
# Copy libraries
mpremote connect /dev/ttyUSB0 cp -r lib/ :lib/

# Copy application files
mpremote connect /dev/ttyUSB0 cp src/boot.py :boot.py
mpremote connect /dev/ttyUSB0 cp src/main.py :main.py
mpremote connect /dev/ttyUSB0 cp src/config.json :config.json

# Reset device
mpremote connect /dev/ttyUSB0 soft-reset
```

### Monitoring

Connect to the REPL to monitor output:

```bash
mpremote connect /dev/ttyUSB0
```

## Project Structure

```
esp32-io-bridge-wifi/
├── lib/                        # Reusable library modules
│   ├── utils/                  # Utility modules
│   │   ├── logger.py          # Logging system ✓
│   │   └── config.py          # Configuration management ✓
│   ├── wifi/                   # WiFi modules (planned)
│   ├── io_bridge/             # IO bridge modules (planned)
│   └── web/                    # Web server modules (planned)
├── src/                        # Application code
│   ├── boot.py                # Boot configuration ✓
│   ├── main.py                # Application entry point ✓
│   └── config.json            # Configuration file ✓
├── tools/                      # Development tools
│   └── deploy.sh              # Deployment script ✓
├── tests/                      # Unit tests (planned)
├── CLAUDE.md                   # AI assistant development guide
└── README.md                   # This file
```

## Development

### Adding a New Module

1. Create module in `lib/` for reusable code
2. Use type hints for all functions
3. Add comprehensive docstrings
4. Update `__init__.py` to export public API
5. Test on device with mpremote

### Testing

```bash
# Run tests on device
mpremote run tests/test_wifi.py
```

### Code Style

- Follow PEP 8 naming conventions
- Use type hints on all functions
- Document all public APIs
- Keep modules focused and single-purpose

## Documentation

- **CLAUDE.md**: Comprehensive development guide for AI assistants
- **API Documentation**: See inline docstrings
- **MicroPython Docs**: https://docs.micropython.org/

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]

## Roadmap

### Phase 1: Foundation ✓
- Project structure and utilities

### Phase 2: WiFi Connectivity (Next)
- WiFi station mode with auto-reconnect
- Access point mode
- Network status monitoring

### Phase 3: IO Bridge
- GPIO control
- UART bridging
- Communication protocol

### Phase 4: Web Interface
- Asynchronous web server
- REST API
- Web-based control panel

## Support

For issues and questions, please refer to CLAUDE.md for development guidance.
