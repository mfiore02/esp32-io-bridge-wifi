"""ESP32 IO Bridge WiFi - Main Application.

This is the main entry point for the ESP32 IO Bridge WiFi firmware.
It initializes all modules and starts the main application loop.
"""

from typing import NoReturn, Optional
import time
import gc
import sys

# Add lib to the module search path
sys.path.append('/lib')

from lib.utils.logger import Logger, LogLevel
from lib.utils.config import Config
from lib.wifi import WiFiStation, WiFiAccessPoint


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

    # Initialize WiFi
    wifi_station: Optional[WiFiStation] = None
    wifi_ap: Optional[WiFiAccessPoint] = None
    wifi_logger = Logger('WiFi', log_level)

    try:
        # Get WiFi mode from config
        wifi_mode = config.get('wifi.mode', 'station')

        if wifi_mode == 'station' or wifi_mode == 'both':
            # Initialize WiFi Station
            ssid = config.get('wifi.ssid', '')
            password = config.get('wifi.password', '')
            auto_reconnect = config.get('wifi.auto_reconnect', True)
            max_retries = config.get('wifi.max_retries', 5)
            timeout = config.get('wifi.timeout', 15)

            if ssid:
                wifi_logger.info(f"Initializing WiFi Station (SSID: {ssid})")
                wifi_station = WiFiStation(
                    ssid=ssid,
                    password=password,
                    auto_reconnect=auto_reconnect,
                    max_retries=max_retries
                )

                wifi_logger.info(f"Connecting to WiFi (timeout: {timeout}s)...")
                if wifi_station.connect(timeout=timeout):
                    status = wifi_station.get_status()
                    wifi_logger.info(f"WiFi connected successfully!")
                    wifi_logger.info(f"  IP: {status['ip']}")
                    wifi_logger.info(f"  Netmask: {status['netmask']}")
                    wifi_logger.info(f"  Gateway: {status['gateway']}")
                    wifi_logger.info(f"  Signal: {status['rssi']} dBm")
                else:
                    wifi_logger.error(f"WiFi connection failed: {wifi_station.get_error()}")
                    if wifi_mode == 'station':
                        wifi_logger.warning("Running without network connectivity")
            else:
                wifi_logger.warning("No WiFi SSID configured")

        if wifi_mode == 'ap' or wifi_mode == 'both':
            # Initialize WiFi Access Point
            ap_ssid = config.get('ap.ssid', 'ESP32-IOBridge')
            ap_password = config.get('ap.password', '')
            ap_channel = config.get('ap.channel', 11)
            ap_hidden = config.get('ap.hidden', False)

            wifi_logger.info(f"Starting WiFi Access Point (SSID: {ap_ssid})")
            wifi_ap = WiFiAccessPoint(
                ssid=ap_ssid,
                password=ap_password,
                channel=ap_channel,
                hidden=ap_hidden
            )

            if wifi_ap.start():
                ap_status = wifi_ap.get_status()
                wifi_logger.info(f"Access Point started successfully!")
                wifi_logger.info(f"  SSID: {ap_status['ssid']}")
                wifi_logger.info(f"  IP: {ap_status['ip']}")
                wifi_logger.info(f"  Channel: {ap_status['channel']}")
            else:
                wifi_logger.error(f"Failed to start AP: {wifi_ap.get_error()}")

    except Exception as e:
        wifi_logger.error(f"WiFi initialization error: {e}")
        sys.print_exception(e)

    # Main application loop
    logger.info("Entering main loop...")
    loop_count = 0
    wifi_check_interval = 30  # Check WiFi every 30 seconds

    while True:
        try:
            # Check WiFi connection periodically
            if wifi_station and loop_count % wifi_check_interval == 0:
                was_connected = wifi_station.is_connected()
                wifi_station.check_connection()
                is_connected = wifi_station.is_connected()

                # Log connection state changes
                if not was_connected and is_connected:
                    wifi_logger.info("WiFi reconnected")
                    status = wifi_station.get_status()
                    wifi_logger.info(f"  IP: {status['ip']}")
                elif was_connected and not is_connected:
                    wifi_logger.warning("WiFi connection lost")

            # Periodic maintenance
            loop_count += 1
            if loop_count % 300 == 0:  # Every 5 minutes
                gc.collect()
                logger.debug(f"Loop {loop_count}, Free memory: {gc.mem_free()} bytes")

                # Log WiFi status
                if wifi_station:
                    status = wifi_station.get_status()
                    if status['connected']:
                        logger.debug(f"WiFi: {status['ssid']}, IP: {status['ip']}, RSSI: {status['rssi']} dBm")

                if wifi_ap and wifi_ap.is_active():
                    ap_status = wifi_ap.get_status()
                    logger.debug(f"AP: {ap_status['client_count']} clients connected")

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

    # Cleanup
    logger.info("Shutting down...")
    if wifi_station:
        wifi_logger.info("Disconnecting WiFi Station")
        wifi_station.disconnect()

    if wifi_ap:
        wifi_logger.info("Stopping Access Point")
        wifi_ap.stop()

    logger.info("Application stopped")


if __name__ == '__main__':
    main()
