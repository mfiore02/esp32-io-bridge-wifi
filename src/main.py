"""ESP32 IO Bridge WiFi - Main Application.

This is the main entry point for the ESP32 IO Bridge WiFi firmware.
It initializes all modules and starts the main application loop.
"""

from typing import NoReturn
import time
import gc
import sys

# Add lib to the module search path
sys.path.append('/lib')

from lib.utils.logger import Logger, LogLevel
from lib.utils.config import Config


def main() -> NoReturn:
    """Application entry point.

    This function initializes the application, loads configuration,
    and runs the main loop.
    """
    # Initialize logger
    logger = Logger('Main', LogLevel.INFO)
    logger.info("Starting ESP32 IO Bridge WiFi...")

    # Load configuration
    try:
        config = Config('config.json')
        logger.info("Configuration loaded successfully")

        # Set logging level from config
        log_level = config.get('logging.level', LogLevel.INFO)
        Logger.set_global_level(log_level)
        logger.info(f"Log level set to {log_level}")

        # Display device info
        device_name = config.get('device.name', 'ESP32-IOBridge')
        device_version = config.get('device.version', '1.0.0')
        logger.info(f"Device: {device_name} v{device_version}")

    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.print_exception(e)
        return

    # Display memory info
    gc.collect()
    logger.info(f"Free memory: {gc.mem_free()} bytes")

    # Main application loop
    logger.info("Entering main loop...")
    loop_count = 0

    while True:
        try:
            # Placeholder for main application logic
            # In future phases, this will:
            # 1. Manage WiFi connection
            # 2. Handle IO bridge operations
            # 3. Process incoming requests

            loop_count += 1
            if loop_count % 10 == 0:
                logger.debug(f"Main loop iteration {loop_count}")
                gc.collect()

            # Sleep to prevent tight loop
            time.sleep(1)

        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received, shutting down...")
            break

        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            sys.print_exception(e)
            # Wait before retrying
            time.sleep(5)

    logger.info("Application stopped")


if __name__ == '__main__':
    main()
