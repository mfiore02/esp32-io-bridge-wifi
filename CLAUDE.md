# CLAUDE.md - ESP32 IO Bridge WiFi Project Guide

This document provides comprehensive guidance for AI assistants working with the ESP32 IO Bridge WiFi codebase. It covers project structure, development workflows, conventions, and best practices for MicroPython-based ESP32 development.

## Table of Contents
1. [Project Overview](#project-overview)
2. [Repository Structure](#repository-structure)
3. [Development Environment](#development-environment)
4. [Development Workflow](#development-workflow)
5. [Code Conventions](#code-conventions)
6. [Module Design](#module-design)
7. [Testing and Debugging](#testing-and-debugging)
8. [Common Tasks](#common-tasks)
9. [Git Workflow](#git-workflow)
10. [AI Assistant Guidelines](#ai-assistant-guidelines)

---

## Project Overview

**ESP32 IO Bridge WiFi** is a MicroPython-based firmware project that provides WiFi connectivity and IO bridging functionality for ESP32 microcontrollers.

### Key Technologies
- **Framework**: MicroPython
- **Target Hardware**: ESP32 family microcontrollers
- **Language**: Python 3
- **Development Environment**: VS Code
- **Device Interaction**: mpremote
- **Communication**: WiFi, potentially UART/SPI/I2C bridging

### Purpose
The firmware enables the ESP32 to act as an IO bridge, allowing remote devices to interact with GPIO pins, sensors, and peripherals over WiFi connections. The project is built with modularity in mind to minimize code duplication and enable reuse in future projects.

---

## Repository Structure

A well-organized MicroPython project should follow this structure:

```
esp32-io-bridge-wifi/
├── lib/                        # Reusable library modules
│   ├── wifi/
│   │   ├── __init__.py
│   │   ├── station.py         # WiFi station mode functionality
│   │   └── access_point.py    # WiFi AP mode functionality
│   ├── io_bridge/
│   │   ├── __init__.py
│   │   ├── gpio_handler.py    # GPIO operations
│   │   ├── uart_bridge.py     # UART bridging
│   │   └── protocol.py        # Communication protocol
│   └── utils/
│       ├── __init__.py
│       ├── config.py          # Configuration management
│       └── logger.py          # Logging utilities
├── src/                        # Application-specific code
│   ├── main.py                # Entry point (boot -> main.py)
│   ├── boot.py                # Boot configuration (runs first)
│   └── config.json            # Application configuration
├── tests/                      # Unit tests
│   ├── test_wifi.py
│   ├── test_gpio.py
│   └── test_protocol.py
├── docs/                       # Documentation
│   └── API.md
├── tools/                      # Development scripts
│   ├── deploy.py              # Deployment automation
│   └── sync.sh                # File sync scripts
├── requirements.txt            # Python dependencies (for dev tools)
├── .vscode/                    # VS Code settings
│   ├── settings.json
│   └── extensions.json
├── README.md                   # Project documentation
├── CLAUDE.md                   # This file
└── LICENSE                     # License file
```

### Key Directories

- **lib/**: Reusable library modules that can be used across projects. These should be well-abstracted and documented.
- **src/**: Application-specific code that ties together lib modules for this particular project.
- **tests/**: Unit tests for modules. MicroPython supports unittest.
- **tools/**: Development and deployment scripts.
- **boot.py**: Runs on every boot, before main.py. Use for minimal initialization.
- **main.py**: Application entry point. This is where your main logic runs.

---

## Development Environment

### Prerequisites

1. **MicroPython Firmware**
   - Install latest stable MicroPython firmware for ESP32
   - Download from: https://micropython.org/download/ESP32_GENERIC/
   - Flash with esptool: `esptool.py --chip esp32 --port /dev/ttyUSB0 erase_flash`
   - Flash firmware: `esptool.py --chip esp32 --port /dev/ttyUSB0 write_flash -z 0x1000 firmware.bin`

2. **Development Tools**
   - Python 3.9+ (preferably Python 3.11 or 3.12)
   - VS Code with extensions:
     - Python (Microsoft)
     - Pylance (Microsoft) - for type checking
     - MicroPico or RT-Thread MicroPython - for MicroPython support
     - Python Type Hint (for better typing support)
   - mpremote: `pip install mpremote`
   - esptool: `pip install esptool`

3. **Optional Tools**
   - ruff or black for code formatting
   - mypy for static type checking (development)
   - pytest for testing host-side code

### VS Code Setup

1. **Install Recommended Extensions**
   ```json
   {
     "recommendations": [
       "ms-python.python",
       "ms-python.vscode-pylance",
       "paulober.pico-w-go",
       "visualstudioexptteam.vscodeintellicode"
     ]
   }
   ```

2. **Configure Python Type Checking**
   Create/update `.vscode/settings.json`:
   ```json
   {
     "python.languageServer": "Pylance",
     "python.analysis.typeCheckingMode": "basic",
     "python.linting.enabled": true,
     "python.linting.pylintEnabled": false,
     "python.linting.mypyEnabled": true,
     "python.formatting.provider": "black",
     "[python]": {
       "editor.defaultFormatter": "ms-python.python",
       "editor.formatOnSave": true,
       "editor.codeActionsOnSave": {
         "source.organizeImports": true
       }
     }
   }
   ```

### mpremote Usage

mpremote is the primary tool for interacting with the ESP32:

```bash
# Connect to REPL
mpremote connect /dev/ttyUSB0

# Execute a command
mpremote exec "print('Hello from ESP32')"

# Copy file to device
mpremote cp main.py :main.py

# Copy directory to device
mpremote cp -r lib/ :lib/

# Read file from device
mpremote cat :main.py

# List files on device
mpremote ls

# Remove file from device
mpremote rm :old_file.py

# Run script on device
mpremote run test_script.py

# Mount local directory (for development)
mpremote mount .

# Reset device
mpremote reset

# Soft reset (Ctrl+D in REPL)
mpremote soft-reset
```

---

## Development Workflow

### Standard Development Cycle

1. **Write Code Locally**
   - Develop in VS Code with full IDE support
   - Use type hints for better code quality
   - Write modular, reusable code in `lib/`
   - Application logic goes in `src/`

2. **Sync to Device**
   ```bash
   # Sync all library modules
   mpremote cp -r lib/ :lib/

   # Sync main application
   mpremote cp src/main.py :main.py
   mpremote cp src/boot.py :boot.py

   # Sync configuration
   mpremote cp src/config.json :config.json
   ```

3. **Test on Device**
   ```bash
   # Connect to REPL
   mpremote

   # Or run a specific test
   mpremote run tests/test_wifi.py

   # Or soft reset to run main.py
   mpremote soft-reset
   ```

4. **Monitor Output**
   ```bash
   # Serial monitor with mpremote
   mpremote

   # The REPL will show print() statements and errors
   ```

5. **Iterate**
   - Make changes locally
   - Sync modified files
   - Test on device
   - Repeat

### Quick Deployment Script

Create `tools/deploy.sh`:
```bash
#!/bin/bash
PORT=${1:-/dev/ttyUSB0}

echo "Deploying to $PORT..."

# Copy libraries
mpremote connect $PORT cp -r lib/ :lib/

# Copy application
mpremote connect $PORT cp src/boot.py :boot.py
mpremote connect $PORT cp src/main.py :main.py
mpremote connect $PORT cp src/config.json :config.json

# Soft reset to run
mpremote connect $PORT soft-reset

echo "Deployment complete!"
```

---

## Code Conventions

### Python Style Guidelines

1. **Type Hints (Required)**

   Always use type hints for function signatures, variables, and return values:

   ```python
   from typing import Optional, List, Dict, Tuple, Any

   def connect_wifi(ssid: str, password: str, timeout: int = 10) -> bool:
       """Connect to WiFi network.

       Args:
           ssid: Network SSID
           password: Network password
           timeout: Connection timeout in seconds

       Returns:
           True if connected successfully, False otherwise
       """
       # Implementation
       return True

   class WiFiStation:
       def __init__(self, ssid: str, password: str) -> None:
           self.ssid: str = ssid
           self.password: str = password
           self._connected: bool = False

       def get_status(self) -> Dict[str, Any]:
           return {
               'connected': self._connected,
               'ssid': self.ssid
           }
   ```

2. **Naming Conventions**
   - Modules: `lowercase_with_underscores.py`
   - Classes: `PascalCase` (e.g., `WiFiStation`)
   - Functions/methods: `snake_case` (e.g., `connect_to_network()`)
   - Constants: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRY_COUNT`)
   - Private members: `_leading_underscore` (e.g., `_internal_state`)

3. **Documentation (Required)**

   Use docstrings for all public modules, classes, and functions:

   ```python
   def calculate_checksum(data: bytes) -> int:
       """Calculate checksum for data packet.

       Uses CRC16 algorithm for data integrity verification.

       Args:
           data: Byte array to calculate checksum for

       Returns:
           16-bit checksum value

       Example:
           >>> calculate_checksum(b'hello')
           12345
       """
       pass
   ```

4. **Error Handling**

   Use specific exceptions and provide context:

   ```python
   class WiFiConnectionError(Exception):
       """Raised when WiFi connection fails."""
       pass

   def connect_wifi(ssid: str, password: str) -> None:
       try:
           # Connection logic
           if not success:
               raise WiFiConnectionError(f"Failed to connect to {ssid}")
       except OSError as e:
           print(f"WiFi error: {e}")
           raise WiFiConnectionError(f"Connection failed: {e}") from e
   ```

5. **Imports**

   Organize imports in three groups:
   ```python
   # Standard library
   import time
   from typing import Optional, Dict

   # MicroPython specific
   import network
   import machine

   # Local modules
   from lib.utils.logger import Logger
   from lib.wifi.station import WiFiStation
   ```

### MicroPython Specific

1. **Memory Management**
   - Be conscious of memory usage (ESP32 typically has ~100KB free RAM)
   - Use `gc.collect()` to free memory when needed
   - Avoid creating large temporary objects
   - Use generators instead of lists when processing large datasets

2. **Asynchronous Operations**
   - Use `uasyncio` for concurrent operations
   - WiFi operations should be non-blocking when possible

   ```python
   import uasyncio as asyncio

   async def handle_client(reader: asyncio.StreamReader,
                           writer: asyncio.StreamWriter) -> None:
       """Handle client connection asynchronously."""
       data = await reader.read(1024)
       response = process_data(data)
       writer.write(response)
       await writer.drain()
       writer.close()
       await writer.wait_closed()
   ```

3. **Pin Configuration**
   ```python
   from machine import Pin

   # Use descriptive names and type hints
   led_pin: Pin = Pin(2, Pin.OUT)
   button_pin: Pin = Pin(0, Pin.IN, Pin.PULL_UP)
   ```

---

## Module Design

### Principles for Reusable Modules

1. **Single Responsibility**
   - Each module should do one thing well
   - Example: `wifi/station.py` handles WiFi station mode only
   - Example: `io_bridge/gpio_handler.py` handles GPIO operations only

2. **Clear Public APIs**

   Define what's public vs. private:
   ```python
   # lib/wifi/station.py
   from typing import Optional, Dict, Any

   __all__ = ['WiFiStation', 'connect', 'disconnect']  # Public API

   class WiFiStation:
       """WiFi Station mode manager."""

       def connect(self, timeout: int = 10) -> bool:
           """Public method - part of API."""
           return self._do_connect(timeout)

       def _do_connect(self, timeout: int) -> bool:
           """Private method - internal implementation."""
           pass
   ```

3. **Configuration via Parameters**

   Don't hardcode values; make modules configurable:
   ```python
   class UARTBridge:
       """UART bridge with configurable parameters."""

       def __init__(
           self,
           uart_id: int = 1,
           baudrate: int = 115200,
           tx_pin: int = 17,
           rx_pin: int = 16,
           buffer_size: int = 1024
       ) -> None:
           self.uart_id = uart_id
           self.baudrate = baudrate
           # ...
   ```

4. **Dependency Injection**

   Pass dependencies instead of importing them:
   ```python
   from typing import Protocol

   class Logger(Protocol):
       """Logger protocol for dependency injection."""
       def info(self, msg: str) -> None: ...
       def error(self, msg: str) -> None: ...

   class WiFiManager:
       def __init__(self, logger: Logger) -> None:
           self.logger = logger

       def connect(self) -> bool:
           self.logger.info("Connecting to WiFi...")
           # Connection logic
           return True
   ```

5. **Avoid Circular Dependencies**

   Structure modules in layers:
   ```
   lib/
   ├── utils/          # Layer 0: No dependencies
   │   └── logger.py
   ├── wifi/           # Layer 1: Depends on utils
   │   └── station.py
   └── io_bridge/      # Layer 2: Depends on wifi, utils
       └── protocol.py
   ```

### Example: Well-Designed Module

```python
# lib/wifi/station.py
"""WiFi Station mode management module.

This module provides WiFi station functionality with automatic
reconnection and status monitoring.
"""

from typing import Optional, Dict, Any, Callable
import network
import time

__all__ = ['WiFiStation', 'WiFiStatus']


class WiFiStatus:
    """WiFi connection status."""
    IDLE = 0
    CONNECTING = 1
    CONNECTED = 2
    FAILED = 3
    DISCONNECTED = 4


class WiFiStation:
    """Manage WiFi station mode connection.

    Example:
        >>> wifi = WiFiStation('MyNetwork', 'password')
        >>> if wifi.connect(timeout=15):
        ...     print(f"Connected! IP: {wifi.get_ip()}")
    """

    def __init__(
        self,
        ssid: str,
        password: str,
        auto_reconnect: bool = True,
        max_retries: int = 3
    ) -> None:
        """Initialize WiFi station.

        Args:
            ssid: Network SSID
            password: Network password
            auto_reconnect: Enable automatic reconnection
            max_retries: Maximum connection retry attempts
        """
        self.ssid = ssid
        self.password = password
        self.auto_reconnect = auto_reconnect
        self.max_retries = max_retries
        self._sta: network.WLAN = network.WLAN(network.STA_IF)
        self._status: int = WiFiStatus.IDLE

    def connect(self, timeout: int = 10) -> bool:
        """Connect to WiFi network.

        Args:
            timeout: Connection timeout in seconds

        Returns:
            True if connected successfully
        """
        self._sta.active(True)
        self._status = WiFiStatus.CONNECTING

        if not self._sta.isconnected():
            self._sta.connect(self.ssid, self.password)

            start_time = time.time()
            while not self._sta.isconnected():
                if time.time() - start_time > timeout:
                    self._status = WiFiStatus.FAILED
                    return False
                time.sleep(0.1)

        self._status = WiFiStatus.CONNECTED
        return True

    def disconnect(self) -> None:
        """Disconnect from WiFi network."""
        self._sta.disconnect()
        self._sta.active(False)
        self._status = WiFiStatus.DISCONNECTED

    def is_connected(self) -> bool:
        """Check if connected to WiFi."""
        return self._sta.isconnected()

    def get_ip(self) -> Optional[str]:
        """Get assigned IP address.

        Returns:
            IP address string or None if not connected
        """
        if self._sta.isconnected():
            return self._sta.ifconfig()[0]
        return None

    def get_status(self) -> Dict[str, Any]:
        """Get detailed connection status.

        Returns:
            Dictionary with status information
        """
        return {
            'connected': self._sta.isconnected(),
            'status': self._status,
            'ssid': self.ssid,
            'ip': self.get_ip(),
            'rssi': self._sta.status('rssi') if self._sta.isconnected() else None
        }
```

---

## Testing and Debugging

### Unit Testing

MicroPython supports a subset of Python's unittest:

```python
# tests/test_wifi.py
import unittest
from lib.wifi.station import WiFiStation, WiFiStatus


class TestWiFiStation(unittest.TestCase):
    """Test WiFi station functionality."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.wifi = WiFiStation('TestSSID', 'TestPassword')

    def test_initialization(self) -> None:
        """Test WiFi station initialization."""
        self.assertEqual(self.wifi.ssid, 'TestSSID')
        self.assertEqual(self.wifi.password, 'TestPassword')

    def test_status(self) -> None:
        """Test status retrieval."""
        status = self.wifi.get_status()
        self.assertIsInstance(status, dict)
        self.assertIn('connected', status)


if __name__ == '__main__':
    unittest.main()
```

Run tests on device:
```bash
mpremote run tests/test_wifi.py
```

### Debugging

1. **Print Debugging**
   ```python
   def debug_function(value: int) -> int:
       print(f"Debug: value={value}")  # Simple debugging
       result = value * 2
       print(f"Debug: result={result}")
       return result
   ```

2. **REPL Debugging**
   ```bash
   # Connect to REPL
   mpremote

   # Import and test modules interactively
   >>> from lib.wifi.station import WiFiStation
   >>> wifi = WiFiStation('MyNet', 'pass')
   >>> wifi.connect()
   >>> wifi.get_status()
   ```

3. **Exception Handling**
   ```python
   import sys

   def safe_operation() -> None:
       try:
           # Risky operation
           result = 1 / 0
       except Exception as e:
           sys.print_exception(e)  # MicroPython-specific
           # Handle error gracefully
   ```

4. **Memory Debugging**
   ```python
   import gc
   import micropython

   def check_memory() -> None:
       gc.collect()
       free = gc.mem_free()
       allocated = gc.mem_alloc()
       print(f"Memory - Free: {free}, Allocated: {allocated}")

       # Show detailed allocation info
       micropython.mem_info()
   ```

### Logging

Create a reusable logger module:

```python
# lib/utils/logger.py
"""Logging utility for MicroPython."""

from typing import Optional
import time

__all__ = ['Logger', 'LogLevel']


class LogLevel:
    """Log level constants."""
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3


class Logger:
    """Simple logger for MicroPython.

    Example:
        >>> logger = Logger('WiFi', LogLevel.INFO)
        >>> logger.info("Connected to network")
        >>> logger.error("Connection failed")
    """

    def __init__(self, name: str, level: int = LogLevel.INFO) -> None:
        """Initialize logger.

        Args:
            name: Logger name (typically module name)
            level: Minimum log level to display
        """
        self.name = name
        self.level = level

    def _log(self, level: int, level_name: str, message: str) -> None:
        """Internal logging method."""
        if level >= self.level:
            timestamp = time.time()
            print(f"[{timestamp}] {level_name} - {self.name}: {message}")

    def debug(self, message: str) -> None:
        """Log debug message."""
        self._log(LogLevel.DEBUG, "DEBUG", message)

    def info(self, message: str) -> None:
        """Log info message."""
        self._log(LogLevel.INFO, "INFO", message)

    def warning(self, message: str) -> None:
        """Log warning message."""
        self._log(LogLevel.WARNING, "WARNING", message)

    def error(self, message: str) -> None:
        """Log error message."""
        self._log(LogLevel.ERROR, "ERROR", message)
```

---

## Common Tasks

### Adding a New Module

1. **Create module structure**
   ```bash
   mkdir -p lib/my_module
   touch lib/my_module/__init__.py
   touch lib/my_module/core.py
   ```

2. **Define public API in `__init__.py`**
   ```python
   # lib/my_module/__init__.py
   """My module description."""

   from .core import MyClass, my_function

   __all__ = ['MyClass', 'my_function']
   __version__ = '1.0.0'
   ```

3. **Implement with types**
   ```python
   # lib/my_module/core.py
   from typing import List, Optional

   def my_function(param: str) -> Optional[str]:
       """Function description."""
       # Implementation
       pass
   ```

4. **Deploy to device**
   ```bash
   mpremote cp -r lib/my_module :lib/my_module
   ```

### Working with Configuration Files

```python
# lib/utils/config.py
"""Configuration management module."""

import json
from typing import Dict, Any, Optional

__all__ = ['Config']


class Config:
    """Manage JSON configuration files."""

    def __init__(self, filename: str = 'config.json') -> None:
        """Initialize config manager.

        Args:
            filename: Configuration file path
        """
        self.filename = filename
        self._data: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """Load configuration from file."""
        try:
            with open(self.filename, 'r') as f:
                self._data = json.load(f)
        except OSError:
            print(f"Config file {self.filename} not found, using defaults")
            self._data = {}

    def save(self) -> None:
        """Save configuration to file."""
        with open(self.filename, 'w') as f:
            json.dump(self._data, f)

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value.

        Args:
            key: Configuration key (supports dot notation: 'wifi.ssid')
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self._data

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """Set configuration value.

        Args:
            key: Configuration key
            value: Value to set
        """
        self._data[key] = value
```

### Async Web Server Example

```python
# lib/web/server.py
"""Asynchronous web server module."""

from typing import Callable, Dict, Awaitable
import uasyncio as asyncio

__all__ = ['WebServer', 'Request', 'Response']


class Request:
    """HTTP request."""

    def __init__(self, method: str, path: str, headers: Dict[str, str]) -> None:
        self.method = method
        self.path = path
        self.headers = headers


class Response:
    """HTTP response."""

    def __init__(self, body: str = '', status: int = 200) -> None:
        self.body = body
        self.status = status
        self.headers: Dict[str, str] = {'Content-Type': 'text/html'}


RouteHandler = Callable[[Request], Awaitable[Response]]


class WebServer:
    """Simple async web server."""

    def __init__(self, port: int = 80) -> None:
        """Initialize web server.

        Args:
            port: Server port
        """
        self.port = port
        self._routes: Dict[str, RouteHandler] = {}

    def route(self, path: str) -> Callable[[RouteHandler], RouteHandler]:
        """Route decorator.

        Example:
            @server.route('/')
            async def index(request: Request) -> Response:
                return Response('<h1>Hello</h1>')
        """
        def decorator(handler: RouteHandler) -> RouteHandler:
            self._routes[path] = handler
            return handler
        return decorator

    async def _handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter
    ) -> None:
        """Handle client connection."""
        try:
            # Parse request
            request_line = await reader.readline()
            method, path, _ = request_line.decode().split()

            # Simple routing
            handler = self._routes.get(path)
            if handler:
                request = Request(method, path, {})
                response = await handler(request)
            else:
                response = Response('<h1>404 Not Found</h1>', 404)

            # Send response
            writer.write(f'HTTP/1.1 {response.status} OK\r\n'.encode())
            for key, value in response.headers.items():
                writer.write(f'{key}: {value}\r\n'.encode())
            writer.write(b'\r\n')
            writer.write(response.body.encode())

            await writer.drain()
        finally:
            await writer.wait_closed()

    async def start(self) -> None:
        """Start the web server."""
        server = await asyncio.start_server(
            self._handle_client,
            '0.0.0.0',
            self.port
        )
        print(f"Server listening on port {self.port}")

        async with server:
            await server.wait_closed()
```

---

## Git Workflow

### Branch Strategy

- **main**: Stable, production-ready code
- **develop**: Integration branch for features
- **feature/***: Feature development branches
- **bugfix/***: Bug fix branches
- **claude/***: AI assistant development branches

### Commit Guidelines

1. **Commit Message Format**
   ```
   <type>: <subject>

   <body>

   <footer>
   ```

2. **Types**
   - `feat`: New feature or module
   - `fix`: Bug fix
   - `docs`: Documentation changes
   - `style`: Code style/formatting changes
   - `refactor`: Code refactoring
   - `test`: Test additions/changes
   - `chore`: Build process, tooling changes

3. **Examples**
   ```
   feat: add WiFi station module with auto-reconnect

   Implement WiFi station mode with automatic reconnection,
   configurable retry logic, and status monitoring. Module
   follows project conventions with full type hints and
   comprehensive documentation.

   Closes #123
   ```

### Pre-commit Checks

Before committing:
- [ ] Code includes type hints
- [ ] All functions/classes have docstrings
- [ ] Code follows naming conventions
- [ ] Modules are properly organized
- [ ] No hardcoded values (use configuration)
- [ ] Tests pass (if applicable)
- [ ] Code tested on device

---

## AI Assistant Guidelines

### When Analyzing Code

1. **Check for type hints**
   - All function signatures should have type hints
   - Variable types should be annotated when not obvious
   - Return types must be specified

2. **Review module organization**
   - Is code in the right place (lib/ vs src/)?
   - Are dependencies properly layered?
   - Is the module reusable or application-specific?

3. **Check for code duplication**
   - Can common functionality be extracted to lib/?
   - Are there repeated patterns that could be abstracted?
   - Could this be useful in other projects?

### When Making Changes

1. **Always add type hints**
   ```python
   # BAD
   def connect(ssid, password):
       return True

   # GOOD
   def connect(ssid: str, password: str) -> bool:
       return True
   ```

2. **Use docstrings**
   ```python
   # GOOD
   def calculate(value: int) -> float:
       """Calculate result based on input value.

       Args:
           value: Input value for calculation

       Returns:
           Calculated result as float
       """
       return float(value * 2.5)
   ```

3. **Design for reusability**
   - Make modules configurable via parameters
   - Avoid hardcoding values
   - Use dependency injection
   - Keep modules focused and single-purpose

4. **Memory awareness**
   - MicroPython has limited memory
   - Avoid creating large temporary objects
   - Use generators for large datasets
   - Call `gc.collect()` after large allocations

5. **MicroPython limitations**
   - Not all Python stdlib is available
   - Use `uasyncio`, not `asyncio`
   - Some typing features may not work on device (but use them anyway for IDE support)
   - File operations are synchronous and blocking

### When Adding Features

1. **Library vs Application code**
   - Reusable functionality → `lib/`
   - Project-specific code → `src/`
   - If in doubt, make it reusable

2. **Module structure**
   ```python
   # lib/my_module/__init__.py
   """Module description."""

   from .core import MainClass, main_function

   __all__ = ['MainClass', 'main_function']
   __version__ = '1.0.0'
   ```

3. **Configuration**
   - Use config files or parameters
   - Never hardcode WiFi credentials, pins, etc.
   - Provide sensible defaults

4. **Error handling**
   ```python
   class ModuleError(Exception):
       """Base exception for this module."""
       pass

   def risky_operation() -> None:
       try:
           # Operation
           pass
       except OSError as e:
           raise ModuleError(f"Operation failed: {e}") from e
   ```

### When Debugging Issues

1. **Use REPL for testing**
   ```bash
   mpremote
   >>> from lib.wifi.station import WiFiStation
   >>> wifi = WiFiStation('test', 'pass')
   >>> wifi.get_status()
   ```

2. **Check memory**
   ```python
   import gc
   gc.collect()
   print(f"Free memory: {gc.mem_free()}")
   ```

3. **Common MicroPython issues**
   - Import errors: Check module is copied to device
   - Memory errors: Reduce allocations, use gc.collect()
   - WiFi issues: Check credentials, signal strength
   - Pin conflicts: Verify pin assignments
   - Timing issues: Add delays or use async

### Best Practices for AI Assistants

1. **Always verify type hints**
   - Every function should have type hints
   - Use `from typing import` for complex types
   - Be explicit about `Optional` types

2. **Promote code reuse**
   - Extract common patterns to lib/
   - Suggest existing modules before creating new ones
   - Design APIs for reusability

3. **Think modular**
   - Small, focused modules
   - Clear public APIs
   - Minimal dependencies
   - Easy to test

4. **Documentation is required**
   - Module docstrings
   - Class docstrings
   - Function docstrings with Args/Returns
   - Usage examples

5. **Test on device**
   - Suggest using `mpremote` to test changes
   - Provide commands to deploy and test
   - Check for memory issues

---

## Quick Reference

### Essential Commands

```bash
# Device interaction
mpremote                          # Connect to REPL
mpremote ls                       # List files on device
mpremote cp file.py :file.py      # Copy file to device
mpremote cp -r lib/ :lib/         # Copy directory to device
mpremote cat :main.py             # Read file from device
mpremote rm :file.py              # Remove file from device
mpremote run script.py            # Run script on device
mpremote soft-reset               # Soft reset device

# Development
mpremote mount .                  # Mount local directory
mpremote exec "import os; os.listdir()"  # Execute command

# Deployment
./tools/deploy.sh /dev/ttyUSB0    # Deploy all files

# Testing
mpremote run tests/test_wifi.py  # Run tests on device
```

### Important Files

| File | Purpose |
|------|---------|
| `boot.py` | Runs first on boot (minimal setup) |
| `main.py` | Application entry point |
| `lib/` | Reusable library modules |
| `src/` | Application-specific code |
| `config.json` | Configuration file |

### Project Structure Template

```python
# Minimal main.py structure
from typing import NoReturn
from lib.utils.logger import Logger, LogLevel
from lib.utils.config import Config

def main() -> NoReturn:
    """Application entry point."""
    # Initialize
    logger = Logger('Main', LogLevel.INFO)
    config = Config('config.json')

    logger.info("Starting application...")

    # Main loop
    while True:
        try:
            # Application logic
            pass
        except Exception as e:
            logger.error(f"Error: {e}")
            import time
            time.sleep(5)

if __name__ == '__main__':
    main()
```

---

## Resources

- **MicroPython Documentation**: https://docs.micropython.org/
- **MicroPython ESP32**: https://docs.micropython.org/en/latest/esp32/quickref.html
- **mpremote Documentation**: https://docs.micropython.org/en/latest/reference/mpremote.html
- **MicroPython Forum**: https://forum.micropython.org/
- **Python Type Hints**: https://docs.python.org/3/library/typing.html

---

## Document Maintenance

**Last Updated**: 2025-11-15
**MicroPython Version**: Latest stable
**Target**: ESP32 family
**Maintainer**: Project Team

This document should be updated when:
- Project structure changes
- New conventions are adopted
- MicroPython version is upgraded
- New development tools are introduced
- Common patterns emerge

---

## Notes for AI Assistants

### Critical Requirements

1. **Type hints are mandatory** - Every function must have type hints
2. **Docstrings are required** - All public APIs must be documented
3. **Code must be modular** - Think reusability first
4. **No duplication** - Extract common code to lib/
5. **Configuration over hardcoding** - Use parameters and config files

### MicroPython Considerations

- Limited memory (~100KB free RAM typical)
- Not all Python stdlib available
- Use `uasyncio`, not `asyncio`
- File operations are synchronous
- WiFi operations can be slow
- Device must be reset to run updated `main.py`

### Development Flow

1. Write code locally with full IDE support
2. Use type hints and docstrings
3. Test logic locally when possible
4. Deploy to device with `mpremote cp`
5. Test on device via REPL or soft-reset
6. Iterate based on results

### Common Patterns

```python
# Configuration
config = Config('config.json')
ssid = config.get('wifi.ssid', 'default')

# Logging
logger = Logger('ModuleName', LogLevel.INFO)
logger.info("Message")

# Async operations
async def task():
    await asyncio.sleep(1)

# Memory management
import gc
gc.collect()
```

When in doubt, prioritize modularity, type safety, and reusability. Write code that could be used in future projects with minimal modifications.
