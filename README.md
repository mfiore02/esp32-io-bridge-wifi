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

**Current Phase**: IO Bridge (GPIO) Complete ✓

### Phase 1: Foundation ✓
- ✓ Project structure and directory organization
- ✓ Logger utility module with multiple log levels
- ✓ Configuration management with JSON support
- ✓ Boot initialization script
- ✓ Main application entry point
- ✓ Deployment automation script
- ✓ Unit test suite (53 tests, 100% passing)

### Phase 2: WiFi Connectivity ✓
- ✓ WiFi Station mode with auto-reconnect
- ✓ WiFi Access Point mode
- ✓ Network status monitoring and signal strength
- ✓ Automatic connection management
- ✓ Integrated into main application
- ✓ Unit test suite (32 tests, 100% passing)

### Phase 3: IO Bridge (GPIO) ✓
- ✓ GPIO handler with digital I/O, PWM, and ADC support
- ✓ Hardware interrupt support with callbacks (RISING, FALLING, BOTH)
- ✓ Pin mode management (INPUT, OUTPUT, PWM, ADC)
- ✓ Pull resistor configuration (PULL_UP, PULL_DOWN, NONE)
- ✓ Pin validation and safety checks
- ✓ PWM frequency and duty cycle control
- ✓ ADC voltage reading with calibration
- ✓ Integrated into main application
- ✓ Unit test suite (51 tests, 100% passing)
- **✓ Total: 136 tests, 100% passing**

### Next Phase
- Web server for remote access
- REST API for GPIO control
- WebSocket support for real-time updates

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
│   ├── wifi/                   # WiFi connectivity modules
│   │   ├── station.py         # WiFi station mode ✓
│   │   └── access_point.py    # WiFi AP mode ✓
│   ├── io_bridge/             # IO bridge modules
│   │   ├── __init__.py        # IO bridge package ✓
│   │   └── gpio_handler.py    # GPIO control with interrupts ✓
│   └── web/                    # Web server modules (planned)
├── src/                        # Application code
│   ├── boot.py                # Boot configuration ✓
│   ├── main.py                # Application entry point with GPIO ✓
│   └── config.json            # Configuration file ✓
├── tools/                      # Development tools
│   ├── deploy.sh              # Deployment script ✓
│   ├── test_local.sh          # Local test runner ✓
│   └── test_on_device.sh      # Device test runner ✓
├── tests/                      # Unit tests
│   ├── test_logger.py         # Logger module tests (18 tests) ✓
│   ├── test_config.py         # Config module tests (35 tests) ✓
│   ├── test_wifi_station.py   # WiFi station tests (32 tests) ✓
│   ├── test_gpio_handler.py   # GPIO handler tests (51 tests) ✓
│   └── run_all_tests.py       # Master test runner ✓
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

The project includes a comprehensive test suite with 136 unit tests covering all implemented modules.

#### Run Tests Locally (Fastest)

```bash
# Run all tests locally
./tools/test_local.sh

# Run specific test file
./tools/test_local.sh test_logger.py
./tools/test_local.sh test_config.py

# Or run directly with Python
python3 tests/run_all_tests.py
```

#### Run Tests on ESP32 Device

```bash
# Deploy and run all tests on device
./tools/test_on_device.sh /dev/ttyUSB0

# Run specific test on device
./tools/test_on_device.sh /dev/ttyUSB0 test_logger.py
```

#### Test Coverage

**Logger Module** (18 tests):
- Log level constants and ordering
- Logger initialization and configuration
- Message formatting with timestamps
- Level filtering (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Multiple logger independence
- Global and local log level settings
- Edge cases (empty messages, special characters, long messages)

**Config Module** (35 tests):
- JSON file loading and saving
- Dot-notation access (e.g., `config.get('wifi.ssid')`)
- Nested value management
- Default value handling
- Key existence checking
- Configuration modification and persistence
- Edge cases (invalid JSON, Unicode, special characters)
- Data type support (strings, numbers, booleans, arrays, nested dicts)

**WiFi Station Module** (32 tests):
- WiFi status constants and state management
- Station initialization with custom parameters
- Connection status and error handling
- Network information (IP, netmask, gateway, DNS)
- Signal strength (RSSI) monitoring
- MAC address retrieval
- Network scanning
- Auto-reconnect functionality
- Edge cases (empty SSID, special characters, Unicode)

**GPIO Handler Module** (51 tests):
- Pin mode constants (INPUT, OUTPUT, PWM, ADC)
- Pull mode constants (NONE, PULL_UP, PULL_DOWN)
- Interrupt trigger constants (RISING, FALLING, BOTH)
- GPIO handler initialization with custom pin lists
- Pin validation and availability checking
- Digital I/O operations (read, write)
- PWM configuration (frequency, duty cycle)
- ADC operations (raw value, voltage reading)
- Interrupt setup with callback handlers
- Interrupt enable/disable control
- Pin status tracking and reporting
- Edge cases (invalid pins, unconfigured operations)

#### Test Results

```
Total Tests:   136
Passing:       136
Failures:      0
Success Rate:  100%
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
- ✓ Project structure and directory organization
- ✓ Logger and configuration utilities
- ✓ Boot system and main application
- ✓ Deployment and testing tools

### Phase 2: WiFi Connectivity ✓
- ✓ WiFi station mode with auto-reconnect
- ✓ WiFi access point mode
- ✓ Network status monitoring (IP, signal strength, connected clients)
- ✓ Automatic connection management
- ✓ Integrated into main application

### Phase 3: IO Bridge ✓
- ✓ GPIO control (digital I/O, PWM, ADC)
- ✓ Hardware interrupt support with callbacks
- ✓ Pin validation and safety checks
- ✓ Integrated into main application
- Future: UART bridging, I2C/SPI support

### Phase 4: Web Interface (Next)
- Asynchronous web server
- REST API for device control
- Web-based control panel
- WebSocket support for real-time updates

## Support

For issues and questions, please refer to CLAUDE.md for development guidance.
