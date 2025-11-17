#!/bin/bash
# ESP32 IO Bridge WiFi Deployment Script
#
# This script deploys the application to an ESP32 device using mpremote.
# Usage: ./tools/deploy.sh [port]
# Example: ./tools/deploy.sh /dev/ttyUSB0

set -e  # Exit on error

PORT=${1:-/dev/ttyUSB0}

echo "======================================================"
echo "ESP32 IO Bridge WiFi - Deployment Script"
echo "======================================================"
echo "Target device: $PORT"
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

echo "Step 1/4: Copying library modules..."
mpremote connect $PORT cp -r lib/ :lib/
echo "✓ Libraries copied"

echo ""
echo "Step 2/4: Copying application files..."
mpremote connect $PORT cp src/boot.py :boot.py
mpremote connect $PORT cp src/main.py :main.py
echo "✓ Application files copied"

echo ""
echo "Step 3/4: Copying configuration..."
mpremote connect $PORT cp src/config.json :config.json
echo "✓ Configuration copied"

echo ""
echo "Step 4/4: Soft resetting device..."
mpremote connect $PORT soft-reset
echo "✓ Device reset"

echo ""
echo "======================================================"
echo "Deployment complete!"
echo "======================================================"
echo ""
echo "To monitor the device:"
echo "  mpremote connect $PORT"
echo ""
echo "To view files on device:"
echo "  mpremote connect $PORT ls"
echo ""
