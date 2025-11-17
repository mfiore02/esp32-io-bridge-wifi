#!/bin/bash
# ESP32 IO Bridge WiFi - Test on Device Script
#
# This script deploys tests to an ESP32 device and runs them using mpremote.
# Usage: ./tools/test_on_device.sh [port] [test_file]
# Example: ./tools/test_on_device.sh /dev/ttyUSB0
# Example: ./tools/test_on_device.sh /dev/ttyUSB0 test_logger.py

set -e  # Exit on error

PORT=${1:-/dev/ttyUSB0}
TEST_FILE=${2:-run_all_tests.py}

echo "======================================================"
echo "ESP32 IO Bridge WiFi - Test on Device"
echo "======================================================"
echo "Target device: $PORT"
echo "Test file: $TEST_FILE"
echo ""

# Check if mpremote is available
if ! command -v mpremote &> /dev/null; then
    echo "Error: mpremote is not installed"
    echo "Install with: pip install mpremote"
    exit 1
fi

# Check if device is connected
if [ ! -e "$PORT" ]; then
    echo "Error: Device not found at $PORT"
    echo "Available devices:"
    ls /dev/ttyUSB* /dev/ttyACM* 2>/dev/null || echo "No devices found"
    exit 1
fi

echo "Step 1/3: Deploying library modules..."
mpremote connect $PORT cp -r lib/ :lib/
echo "✓ Libraries deployed"

echo ""
echo "Step 2/3: Deploying test files..."
mpremote connect $PORT mkdir :tests 2>/dev/null || true
mpremote connect $PORT cp tests/__init__.py :tests/__init__.py
mpremote connect $PORT cp tests/test_logger.py :tests/test_logger.py
mpremote connect $PORT cp tests/test_config.py :tests/test_config.py
mpremote connect $PORT cp tests/run_all_tests.py :tests/run_all_tests.py
echo "✓ Test files deployed"

echo ""
echo "Step 3/3: Running tests on device..."
echo "======================================================"
echo ""

# Run the specified test file
if [ "$TEST_FILE" = "run_all_tests.py" ]; then
    mpremote connect $PORT exec "import sys; sys.path.append('/tests'); sys.path.append('tests'); import run_all_tests; run_all_tests.main()"
else
    mpremote connect $PORT exec "import sys; sys.path.append('/tests'); sys.path.append('tests'); import ${TEST_FILE%.py}; ${TEST_FILE%.py}.run_tests()"
fi

echo ""
echo "======================================================"
echo "Test execution complete!"
echo "======================================================"
