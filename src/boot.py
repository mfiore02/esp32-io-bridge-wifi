"""Boot configuration for ESP32 IO Bridge WiFi.

This file runs on every boot before main.py. It performs minimal
initialization and system setup.
"""

import gc
import esp

# Disable OS debug output for cleaner logs
esp.osdebug(None)

# Run garbage collection to free up memory
gc.collect()

# Print boot message
print("=" * 50)
print("ESP32 IO Bridge WiFi - Boot")
print("=" * 50)

# Display memory info
print(f"Free memory: {gc.mem_free()} bytes")
print(f"Allocated memory: {gc.mem_alloc()} bytes")

# Set garbage collection threshold (optional, tuning parameter)
# Collect when allocation reaches 4KB
gc.threshold(4096)

print("Boot complete, starting main.py...")
print("=" * 50)
