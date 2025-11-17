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
from lib.io_bridge import GPIOHandler
from lib.mqtt import MQTTBridge, MQTT_AVAILABLE


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

    # Initialize GPIO Handler
    gpio_handler: Optional[GPIOHandler] = None
    gpio_logger = Logger('GPIO', log_level)

    try:
        # Get GPIO configuration
        gpio_enabled = config.get('gpio.enabled', True)

        if gpio_enabled:
            enabled_pins = config.get('gpio.enabled_pins', None)

            if enabled_pins:
                gpio_logger.info(f"Initializing GPIO handler with {len(enabled_pins)} enabled pins")
                gpio_handler = GPIOHandler(allowed_pins=enabled_pins)
                gpio_logger.info(f"GPIO handler initialized: {enabled_pins}")
                gpio_logger.info("GPIO ready for configuration")
            else:
                gpio_logger.info("Initializing GPIO handler with default pins")
                gpio_handler = GPIOHandler()
                gpio_logger.info(f"GPIO handler initialized with {len(gpio_handler.allowed_pins)} pins")
        else:
            gpio_logger.info("GPIO disabled in configuration")

    except Exception as e:
        gpio_logger.error(f"GPIO initialization error: {e}")
        sys.print_exception(e)

    # Initialize MQTT Bridge
    mqtt_bridge: Optional[MQTTBridge] = None
    mqtt_logger = Logger('MQTT', log_level)

    # GPIO command handler for MQTT
    def handle_gpio_command(pin: int, value: int) -> None:
        """Handle GPIO command from MQTT.

        Args:
            pin: GPIO pin number
            value: Pin value (0/1 for digital, 0-1023 for PWM)
        """
        if not gpio_handler:
            mqtt_logger.warning(f"GPIO command received but GPIO handler not initialized")
            return

        try:
            # Check if pin is valid
            if not gpio_handler.is_pin_valid(pin):
                mqtt_logger.error(f"Invalid pin number in MQTT command: {pin}")
                return

            # Setup pin as output if not configured
            if not gpio_handler.is_pin_available(pin):
                # Pin already in use, check if we can write to it
                status = gpio_handler.get_pin_status(pin)
                if status and status.get('mode') not in ['output', 'pwm']:
                    mqtt_logger.warning(f"Pin {pin} not configured for output, reconfiguring")
                    gpio_handler.release_pin(pin)

            # Handle PWM values (512-1023 range indicates PWM intent)
            if value > 1:
                # PWM mode
                if gpio_handler.is_pin_available(pin):
                    gpio_handler.setup_pwm(pin, freq=1000, duty=value)
                    mqtt_logger.info(f"PWM command: pin {pin} = {value}")
                else:
                    # Already configured, just update duty
                    gpio_handler.set_pwm_duty(pin, value)
                    mqtt_logger.debug(f"PWM update: pin {pin} = {value}")
            else:
                # Digital output mode (0 or 1)
                if gpio_handler.is_pin_available(pin):
                    from lib.io_bridge import PinMode
                    gpio_handler.setup_pin(pin, PinMode.OUTPUT)

                gpio_handler.digital_write(pin, value)
                mqtt_logger.info(f"Digital command: pin {pin} = {value}")

            # Publish state back if configured
            if mqtt_bridge and config.get('mqtt.publish_gpio_state', True):
                mqtt_bridge.publish_gpio_state(pin, value)

        except Exception as e:
            mqtt_logger.error(f"Error handling GPIO command: {e}")
            sys.print_exception(e)

    try:
        # Get MQTT configuration
        mqtt_enabled = config.get('mqtt.enabled', False)

        if mqtt_enabled and MQTT_AVAILABLE:
            broker = config.get('mqtt.broker', '')
            port = config.get('mqtt.port', 1883)
            client_id = config.get('mqtt.client_id', 'esp32-bridge')
            username = config.get('mqtt.username', '')
            password = config.get('mqtt.password', '')
            keepalive = config.get('mqtt.keepalive', 60)
            topic_prefix = config.get('mqtt.topic_prefix', 'esp32')

            if broker:
                mqtt_logger.info(f"Initializing MQTT client (broker: {broker}:{port})")
                mqtt_bridge = MQTTBridge(
                    broker=broker,
                    client_id=client_id,
                    port=port,
                    user=username if username else None,
                    password=password if password else None,
                    keepalive=keepalive,
                    topic_prefix=topic_prefix
                )

                # Wait for WiFi connection before connecting to MQTT
                if wifi_station and wifi_station.is_connected():
                    mqtt_logger.info("Connecting to MQTT broker...")
                    if mqtt_bridge.connect():
                        mqtt_logger.info("MQTT connected successfully")

                        # Publish online status
                        mqtt_bridge.publish_status("online", retain=True)

                        # Subscribe to GPIO commands if enabled
                        if config.get('mqtt.subscribe_gpio_commands', True) and gpio_handler:
                            mqtt_logger.info("Subscribing to GPIO command topic")
                            mqtt_bridge.subscribe_gpio_commands(handle_gpio_command)
                            mqtt_logger.info(f"MQTT ready for GPIO commands on topic: {topic_prefix}/{client_id}/gpio/+/set")
                    else:
                        mqtt_logger.error(f"MQTT connection failed: {mqtt_bridge.get_error()}")
                else:
                    mqtt_logger.warning("WiFi not connected, MQTT connection deferred")
            else:
                mqtt_logger.warning("No MQTT broker configured")

        elif mqtt_enabled and not MQTT_AVAILABLE:
            mqtt_logger.error("MQTT enabled but umqtt.robust library not available")
        else:
            mqtt_logger.info("MQTT disabled in configuration")

    except Exception as e:
        mqtt_logger.error(f"MQTT initialization error: {e}")
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

                    # Reconnect MQTT if WiFi reconnected
                    if mqtt_bridge and not mqtt_bridge.is_connected():
                        mqtt_logger.info("Reconnecting MQTT after WiFi restoration...")
                        if mqtt_bridge.connect():
                            mqtt_logger.info("MQTT reconnected")
                            mqtt_bridge.publish_status("online", retain=True)
                            if config.get('mqtt.subscribe_gpio_commands', True) and gpio_handler:
                                mqtt_bridge.subscribe_gpio_commands(handle_gpio_command)

                elif was_connected and not is_connected:
                    wifi_logger.warning("WiFi connection lost")
                    if mqtt_bridge and mqtt_bridge.is_connected():
                        mqtt_logger.warning("MQTT connection likely lost with WiFi")

            # Check for MQTT messages
            if mqtt_bridge and mqtt_bridge.is_connected():
                mqtt_bridge.check_messages()

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

                if gpio_handler:
                    pin_status = gpio_handler.get_all_pins_status()
                    if pin_status:
                        logger.debug(f"GPIO: {len(pin_status)} pins configured")

                if mqtt_bridge:
                    mqtt_status = mqtt_bridge.get_status()
                    if mqtt_status['connected']:
                        logger.debug(f"MQTT: Connected to {mqtt_status['broker']}")
                    else:
                        logger.debug(f"MQTT: Not connected")

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

    if mqtt_bridge:
        mqtt_logger.info("Publishing offline status")
        mqtt_bridge.publish_status("offline", retain=True)
        mqtt_logger.info("Disconnecting MQTT")
        mqtt_bridge.disconnect()
        mqtt_logger.info("MQTT cleanup complete")

    if gpio_handler:
        gpio_logger.info("Releasing GPIO pins")
        pin_status = gpio_handler.get_all_pins_status()
        for pin in pin_status.keys():
            gpio_handler.release_pin(pin)
        gpio_logger.info("GPIO cleanup complete")

    if wifi_station:
        wifi_logger.info("Disconnecting WiFi Station")
        wifi_station.disconnect()

    if wifi_ap:
        wifi_logger.info("Stopping Access Point")
        wifi_ap.stop()

    logger.info("Application stopped")


if __name__ == '__main__':
    main()
