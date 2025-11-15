# CLAUDE.md - ESP32 IO Bridge WiFi Project Guide

This document provides comprehensive guidance for AI assistants working with the ESP32 IO Bridge WiFi codebase. It covers project structure, development workflows, conventions, and best practices.

## Table of Contents
1. [Project Overview](#project-overview)
2. [Repository Structure](#repository-structure)
3. [Development Environment](#development-environment)
4. [Build System](#build-system)
5. [Development Workflow](#development-workflow)
6. [Code Conventions](#code-conventions)
7. [Testing and Debugging](#testing-and-debugging)
8. [Common Tasks](#common-tasks)
9. [Git Workflow](#git-workflow)
10. [AI Assistant Guidelines](#ai-assistant-guidelines)

---

## Project Overview

**ESP32 IO Bridge WiFi** is an ESP32-based firmware project that provides WiFi connectivity and IO bridging functionality. This project uses the ESP-IDF (Espressif IoT Development Framework) as its foundation.

### Key Technologies
- **Framework**: ESP-IDF (Espressif IoT Development Framework)
- **Build System**: CMake
- **Target Hardware**: ESP32 family microcontrollers
- **Language**: C/C++
- **Communication**: WiFi, potentially UART/SPI/I2C bridging

### Purpose
The firmware enables the ESP32 to act as an IO bridge, allowing remote devices to interact with GPIO pins, sensors, and peripherals over WiFi connections.

---

## Repository Structure

A typical ESP-IDF project follows this structure:

```
esp32-io-bridge-wifi/
├── CMakeLists.txt              # Root CMake configuration
├── sdkconfig                   # ESP-IDF configuration (auto-generated)
├── sdkconfig.defaults          # Default configuration values
├── main/                       # Main application component
│   ├── CMakeLists.txt         # Main component CMake config
│   ├── main.c / main.cpp      # Application entry point
│   ├── Kconfig.projbuild      # Project configuration menu
│   └── include/               # Private headers
├── components/                 # Custom/third-party components
│   └── <component_name>/
│       ├── CMakeLists.txt
│       ├── include/           # Public headers
│       └── src/               # Implementation files
├── build/                      # Build artifacts (git-ignored)
├── docs/                       # Documentation
├── test/                       # Unit tests
├── tools/                      # Build/flash/debug scripts
├── README.md                   # Project documentation
└── LICENSE                     # License file
```

### Key Directories

- **main/**: Contains the primary application code. This is a special ESP-IDF component.
- **components/**: Reusable components specific to this project. Each component should be self-contained with its own CMakeLists.txt.
- **build/**: Generated during compilation. Contains binaries, intermediate files, and flashable .bin files. Safe to delete and regenerate.
- **sdkconfig**: Auto-generated configuration file. Managed via `idf.py menuconfig`.
- **sdkconfig.defaults**: Version-controlled defaults for project configuration.

---

## Development Environment

### Prerequisites

1. **ESP-IDF Installation**
   - Install ESP-IDF v5.0 or later (check project requirements)
   - Set up `IDF_PATH` environment variable
   - Install ESP-IDF tools: `install.sh` or `install.bat`
   - Source the environment: `. $HOME/esp/esp-idf/export.sh`

2. **Required Tools**
   - CMake (v3.16 or higher)
   - Python 3.8+
   - Ninja or GNU Make
   - USB-to-UART drivers for flashing

3. **Optional Tools**
   - OpenOCD for debugging
   - Serial monitor (minicom, screen, or `idf.py monitor`)

### Environment Setup Verification

```bash
# Verify ESP-IDF installation
idf.py --version

# Check Python and CMake
python --version
cmake --version
```

---

## Build System

The project uses ESP-IDF's CMake-based build system.

### Root CMakeLists.txt Structure

```cmake
cmake_minimum_required(VERSION 3.16)

include($ENV{IDF_PATH}/tools/cmake/project.cmake)
project(esp32-io-bridge-wifi)
```

### Component CMakeLists.txt Structure

```cmake
idf_component_register(
    SRCS "src/file1.c" "src/file2.c"
    INCLUDE_DIRS "include"
    REQUIRES driver nvs_flash esp_wifi
)
```

### Configuration Management

- **menuconfig**: Interactive configuration tool
  ```bash
  idf.py menuconfig
  ```
- Configuration is saved to `sdkconfig`
- Defaults should be committed in `sdkconfig.defaults`

---

## Development Workflow

### Standard Development Cycle

1. **Configure the Project**
   ```bash
   idf.py set-target esp32       # or esp32s2, esp32s3, esp32c3, etc.
   idf.py menuconfig             # Optional: customize configuration
   ```

2. **Build the Firmware**
   ```bash
   idf.py build
   ```

3. **Flash to Device**
   ```bash
   idf.py -p /dev/ttyUSB0 flash  # Replace with correct port
   ```

4. **Monitor Output**
   ```bash
   idf.py -p /dev/ttyUSB0 monitor
   ```

5. **Combined Flash and Monitor**
   ```bash
   idf.py -p /dev/ttyUSB0 flash monitor
   ```

### Build System Commands

| Command | Description |
|---------|-------------|
| `idf.py build` | Compile the project |
| `idf.py clean` | Remove build artifacts |
| `idf.py fullclean` | Remove build directory and sdkconfig |
| `idf.py flash` | Flash firmware to device |
| `idf.py monitor` | Open serial monitor |
| `idf.py size` | Show binary size breakdown |
| `idf.py menuconfig` | Configure project settings |
| `idf.py app-flash` | Flash only the app (faster) |

---

## Code Conventions

### C/C++ Style Guidelines

1. **Naming Conventions**
   - Functions: `snake_case` (e.g., `wifi_init_sta()`)
   - Variables: `snake_case` (e.g., `wifi_config`)
   - Constants/Macros: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRY_COUNT`)
   - Types/Structs: `snake_case_t` (e.g., `wifi_config_t`)
   - Global variables: Prefix with `g_` (e.g., `g_wifi_handle`)

2. **File Organization**
   - Header files: Use include guards or `#pragma once`
   - One component per logical feature
   - Public headers in `include/`, private headers in component root or `src/`

3. **ESP-IDF Specific**
   - Use ESP-IDF logging macros: `ESP_LOGI()`, `ESP_LOGW()`, `ESP_LOGE()`, `ESP_LOGD()`
   - Use FreeRTOS primitives for threading/synchronization
   - Leverage ESP-IDF components (esp_wifi, nvs_flash, etc.)
   - Follow ESP-IDF error handling patterns (esp_err_t return values)

4. **Error Handling**
   ```c
   esp_err_t ret = some_function();
   if (ret != ESP_OK) {
       ESP_LOGE(TAG, "Function failed: %s", esp_err_to_name(ret));
       return ret;
   }
   ```

5. **Memory Management**
   - Prefer stack allocation for small, short-lived data
   - Use `heap_caps_malloc()` for specific memory regions
   - Always free allocated memory
   - Use `ESP_ERROR_CHECK()` for critical operations

### Documentation

- Use Doxygen-style comments for public APIs
- Document function parameters, return values, and side effects
- Include examples in header comments where appropriate

```c
/**
 * @brief Initialize WiFi in station mode
 *
 * @param ssid WiFi network SSID
 * @param password WiFi password
 * @return esp_err_t ESP_OK on success, error code otherwise
 */
esp_err_t wifi_init_sta(const char *ssid, const char *password);
```

---

## Testing and Debugging

### Logging

ESP-IDF provides a powerful logging system:

```c
static const char *TAG = "MY_MODULE";

ESP_LOGI(TAG, "Informational message");
ESP_LOGW(TAG, "Warning message");
ESP_LOGE(TAG, "Error message");
ESP_LOGD(TAG, "Debug message (disabled by default)");
ESP_LOGV(TAG, "Verbose message (disabled by default)");
```

Configure log levels via menuconfig or at runtime:
```c
esp_log_level_set("MY_MODULE", ESP_LOG_DEBUG);
```

### Debugging

1. **Serial Monitor Debugging**
   - Use ESP_LOG macros liberally
   - Monitor for stack overflow warnings
   - Check for heap corruption

2. **JTAG Debugging**
   - Use OpenOCD with compatible JTAG adapter
   - GDB integration available via ESP-IDF

3. **Core Dumps**
   - Enable in menuconfig: Component config → ESP System Settings → Core dump
   - Analyze with `espcoredump.py`

### Unit Testing

- ESP-IDF supports Unity test framework
- Place tests in `test/` directory or component test subdirectories
- Run tests on target: `idf.py build flash monitor`

---

## Common Tasks

### Adding a New Component

1. Create component directory:
   ```bash
   mkdir -p components/my_component/{src,include}
   ```

2. Create `components/my_component/CMakeLists.txt`:
   ```cmake
   idf_component_register(
       SRCS "src/my_component.c"
       INCLUDE_DIRS "include"
       REQUIRES driver
   )
   ```

3. Add public header to `include/my_component.h`

4. Implement in `src/my_component.c`

### Modifying WiFi Configuration

1. Update credentials in code or use NVS storage
2. Modify WiFi mode (STA/AP/APSTA) in initialization
3. Adjust connection retry logic as needed
4. Configure static IP if required (vs DHCP)

### Adding Dependencies

- Modify `REQUIRES` in component CMakeLists.txt:
  ```cmake
  idf_component_register(
      SRCS "src/file.c"
      INCLUDE_DIRS "include"
      REQUIRES driver nvs_flash esp_http_server  # Add dependencies here
  )
  ```

### Partition Table Customization

1. Create custom partition CSV in root directory
2. Reference in CMakeLists.txt or menuconfig
3. Common partitions: nvs, phy_init, factory, ota_0, ota_1, spiffs

---

## Git Workflow

### Branch Strategy

- **main/master**: Stable, production-ready code
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
   - `feat`: New feature
   - `fix`: Bug fix
   - `docs`: Documentation changes
   - `style`: Code style changes (formatting)
   - `refactor`: Code refactoring
   - `test`: Test additions/changes
   - `chore`: Build process, tooling changes

3. **Examples**
   ```
   feat: add WiFi reconnection logic

   Implement automatic reconnection with exponential backoff
   when WiFi connection is lost.

   Closes #123
   ```

### Pre-commit Checks

Before committing:
- [ ] Code builds successfully (`idf.py build`)
- [ ] No compiler warnings
- [ ] Code follows style guidelines
- [ ] Tests pass (if applicable)
- [ ] Documentation updated

---

## AI Assistant Guidelines

### When Analyzing Code

1. **Always check ESP-IDF version compatibility**
   - API changes between versions are common
   - Check documentation for target ESP-IDF version

2. **Understand component dependencies**
   - Review CMakeLists.txt for REQUIRES/PRIV_REQUIRES
   - Check for circular dependencies

3. **Review sdkconfig for context**
   - Configuration affects code behavior
   - Check enabled features and memory allocations

### When Making Changes

1. **Build before committing**
   - Always run `idf.py build` to verify compilation
   - Check for warnings, not just errors

2. **Respect ESP-IDF patterns**
   - Use esp_err_t for error returns
   - Use ESP_ERROR_CHECK for critical operations
   - Follow FreeRTOS task creation patterns

3. **Memory considerations**
   - ESP32 has limited RAM (typical: 320KB internal)
   - Be mindful of stack sizes for tasks
   - Avoid large static allocations
   - Use PROGMEM/DRAM attributes appropriately

4. **Thread safety**
   - ESP-IDF is multithreaded (FreeRTOS)
   - Use mutexes, semaphores for shared resources
   - Be aware of ISR context restrictions

### When Adding Features

1. **Component-based design**
   - Create new components for distinct functionality
   - Keep components loosely coupled
   - Use clear public APIs

2. **Configuration management**
   - Add Kconfig options for user-configurable features
   - Provide sensible defaults in sdkconfig.defaults

3. **Error handling**
   - Always handle esp_err_t returns
   - Log errors with appropriate severity
   - Provide recovery mechanisms where possible

4. **Documentation**
   - Update README.md for major features
   - Document public APIs with Doxygen comments
   - Include usage examples

### When Debugging Issues

1. **Check logs first**
   - Enable verbose logging for relevant modules
   - Look for stack traces, panic handlers
   - Check for heap/stack overflow messages

2. **Verify hardware**
   - Confirm correct GPIO pins
   - Check voltage levels and power supply
   - Verify UART/SPI/I2C bus configuration

3. **Common pitfalls**
   - Watchdog timer resets (blocking operations)
   - Stack overflow in tasks
   - Race conditions in multi-threaded code
   - Incorrect GPIO configuration
   - Missing NVS initialization

### Best Practices for AI Assistants

1. **Always verify before suggesting**
   - Check ESP-IDF documentation for API usage
   - Verify component availability in target ESP-IDF version
   - Test build configurations when possible

2. **Provide context**
   - Explain why changes are needed
   - Reference ESP-IDF documentation
   - Highlight potential side effects

3. **Security considerations**
   - Never hardcode WiFi credentials
   - Use secure boot when appropriate
   - Validate input data
   - Implement proper authentication for network services

4. **Performance awareness**
   - Profile code when adding compute-intensive features
   - Monitor task stack usage
   - Check heap fragmentation
   - Optimize WiFi power consumption

---

## Quick Reference

### Essential Commands

```bash
# Setup
idf.py set-target esp32
idf.py menuconfig

# Development
idf.py build
idf.py -p PORT flash monitor
idf.py clean

# Utilities
idf.py size
idf.py size-components
idf.py size-files
idf.py monitor
idf.py erase-flash

# Application only (faster iteration)
idf.py app-flash
```

### Important Files

| File | Purpose |
|------|---------|
| `CMakeLists.txt` | Root build configuration |
| `sdkconfig.defaults` | Default configuration values (committed) |
| `sdkconfig` | Active configuration (auto-generated) |
| `main/main.c` | Application entry point |
| `partitions.csv` | Partition table (if custom) |

### Environment Variables

| Variable | Purpose |
|----------|---------|
| `IDF_PATH` | ESP-IDF framework location |
| `IDF_TARGET` | Target chip (esp32, esp32s3, etc.) |

### Useful Macros

```c
ESP_ERROR_CHECK(function_call);  // Assert on error
ESP_LOGI(TAG, "message");        // Log info
configASSERT(condition);         // FreeRTOS assert
portMAX_DELAY                    // Infinite wait
pdMS_TO_TICKS(ms)               // Convert ms to ticks
```

---

## Resources

- **ESP-IDF Documentation**: https://docs.espressif.com/projects/esp-idf/
- **ESP-IDF GitHub**: https://github.com/espressif/esp-idf
- **ESP32 Forum**: https://www.esp32.com/
- **ESP-IDF API Reference**: https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/
- **FreeRTOS Documentation**: https://www.freertos.org/

---

## Document Maintenance

**Last Updated**: 2025-11-15
**ESP-IDF Version**: 5.x
**Maintainer**: Project Team

This document should be updated when:
- Project structure changes significantly
- New conventions are adopted
- ESP-IDF version is upgraded
- New development tools are introduced

---

## Notes for AI Assistants

- This project is embedded firmware with real-time constraints
- Always consider power consumption implications
- WiFi operations are asynchronous - handle callbacks properly
- Flash writes have limited cycles - minimize unnecessary writes
- Debugging options affect binary size and performance
- OTA updates require careful partition management
- Network security is critical for IoT devices

When in doubt, consult the official ESP-IDF documentation and prefer ESP-IDF's built-in components over custom implementations.
