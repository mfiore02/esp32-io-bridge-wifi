# ESP32 IO Bridge WiFi

MicroPython-based firmware that provides WiFi connectivity and IO bridging functionality for ESP32 microcontrollers.

## Features

- WiFi Station and Access Point modes
- GPIO control via network interface
- MQTT client for remote control and monitoring
- Hardware interrupt support
- PWM and ADC capabilities
- Configurable via JSON
- Comprehensive logging system
- Modular, reusable code architecture

## Project Status

**Current Phase**: MQTT Communication Complete ✓

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

### Phase 4: MQTT Communication ✓
- ✓ MQTT client with publish/subscribe support
- ✓ GPIO remote control via MQTT topics
- ✓ Device status publishing
- ✓ Automatic reconnection on WiFi restore
- ✓ Configurable topics and QoS levels
- ✓ GPIO state publishing with retain flag
- ✓ Command subscription for GPIO control
- ✓ Integrated into main application
- ✓ Unit test suite (35 tests, 100% passing)
- **✓ Total: 171 tests, 100% passing**

### Next Phase
- Web server for HTTP access
- REST API for GPIO control
- WebSocket support for real-time updates
- Web-based dashboard

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

## MQTT Usage

The ESP32 IO Bridge supports MQTT for remote GPIO control and monitoring.

### Setup MQTT Broker

You'll need an MQTT broker on your network. Options include:

**Mosquitto (Recommended for home server)**:
```bash
# Install on Linux/Raspberry Pi
sudo apt-get install mosquitto mosquitto-clients
sudo systemctl enable mosquitto
sudo systemctl start mosquitto
```

**Docker**:
```bash
docker run -d -p 1883:1883 -p 9001:9001 --name mosquitto eclipse-mosquitto
```

### Configure MQTT in config.json

```json
{
  "mqtt": {
    "enabled": true,
    "broker": "192.168.1.100",
    "port": 1883,
    "client_id": "esp32-bridge-01",
    "username": "",
    "password": "",
    "topic_prefix": "esp32"
  }
}
```

### MQTT Topics

**Device Status**:
- `esp32/{client_id}/status` - Device online/offline status (retained)

**GPIO Control**:
- `esp32/{client_id}/gpio/{pin}/set` - Set GPIO pin (subscribe)
  - Payload: `0` or `1` for digital output
  - Payload: `2-1023` for PWM output
- `esp32/{client_id}/gpio/{pin}/state` - GPIO pin state (publish, retained)

### Control GPIO via MQTT

**Using mosquitto_pub**:
```bash
# Turn on GPIO pin 2
mosquitto_pub -h 192.168.1.100 -t "esp32/esp32-bridge-01/gpio/2/set" -m "1"

# Turn off GPIO pin 2
mosquitto_pub -h 192.168.1.100 -t "esp32/esp32-bridge-01/gpio/2/set" -m "0"

# Set PWM on pin 5 (50% duty cycle = 512)
mosquitto_pub -h 192.168.1.100 -t "esp32/esp32-bridge-01/gpio/5/set" -m "512"
```

**Subscribe to device status**:
```bash
# Monitor device status
mosquitto_sub -h 192.168.1.100 -t "esp32/esp32-bridge-01/status"

# Monitor all GPIO states
mosquitto_sub -h 192.168.1.100 -t "esp32/esp32-bridge-01/gpio/+/state"

# Monitor everything from device
mosquitto_sub -h 192.168.1.100 -t "esp32/esp32-bridge-01/#"
```

### Python MQTT Client Example

```python
import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    # Subscribe to GPIO states
    client.subscribe("esp32/esp32-bridge-01/gpio/+/state")

def on_message(client, userdata, msg):
    print(f"Topic: {msg.topic}, Payload: {msg.payload.decode()}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("192.168.1.100", 1883, 60)

# Control GPIO pin 2
client.publish("esp32/esp32-bridge-01/gpio/2/set", "1")

client.loop_forever()
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
│   ├── mqtt/                   # MQTT communication modules
│   │   ├── __init__.py        # MQTT package ✓
│   │   └── client.py          # MQTT client with GPIO integration ✓
│   └── web/                    # Web server modules (planned)
├── src/                        # Application code
│   ├── boot.py                # Boot configuration ✓
│   ├── main.py                # Application entry point with MQTT ✓
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
│   ├── test_mqtt_client.py    # MQTT client tests (35 tests) ✓
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

The project includes a comprehensive test suite with 171 unit tests covering all implemented modules.

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

**MQTT Client Module** (35 tests):
- MQTT configuration constants (QoS levels, defaults)
- Client initialization with/without authentication
- Connection and disconnection handling
- Publish to topics with QoS and retain flags
- Subscribe to topics
- Message checking and handling
- GPIO command subscription and parsing
- Custom message handlers
- Status publishing (online/offline)
- GPIO state publishing
- Sensor data publishing
- Error handling and recovery
- Edge cases (invalid formats, connection failures)

#### Test Results

```
Total Tests:   171
Passing:       171
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

### Phase 4: MQTT Communication ✓
- ✓ MQTT client with publish/subscribe support
- ✓ GPIO remote control via MQTT topics
- ✓ Device status publishing and monitoring
- ✓ Automatic reconnection on WiFi restore
- ✓ Configurable topics, QoS, and authentication
- ✓ Integrated into main application

### Phase 5: Web Interface (Next)
- Asynchronous web server
- REST API for device control
- Web-based control panel
- WebSocket support for real-time updates

## Support

For issues and questions, please refer to CLAUDE.md for development guidance.
