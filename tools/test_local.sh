#!/bin/bash
# ESP32 IO Bridge WiFi - Local Test Runner
#
# This script runs tests locally (not on device) for faster development.
# Note: Some tests may behave differently than on the actual ESP32 device.
#
# Usage: ./tools/test_local.sh [test_file]
# Example: ./tools/test_local.sh
# Example: ./tools/test_local.sh test_logger.py

TEST_FILE=${1:-run_all_tests.py}

echo "======================================================"
echo "ESP32 IO Bridge WiFi - Local Test Runner"
echo "======================================================"
echo "Test file: $TEST_FILE"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed"
    exit 1
fi

# Navigate to project root
cd "$(dirname "$0")/.." || exit 1

echo "Running tests locally..."
echo "======================================================"
echo ""

# Run the tests
if [ -f "tests/$TEST_FILE" ]; then
    python3 "tests/$TEST_FILE"
    EXIT_CODE=$?
else
    echo "Error: Test file 'tests/$TEST_FILE' not found"
    exit 1
fi

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo "======================================================"
    echo "✓ Tests completed successfully!"
    echo "======================================================"
else
    echo "======================================================"
    echo "✗ Tests failed with exit code $EXIT_CODE"
    echo "======================================================"
fi

exit $EXIT_CODE
