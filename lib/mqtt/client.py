"""MQTT Client Module for ESP32 IO Bridge.

This module provides MQTT client functionality for remote device control
and monitoring. It uses the umqtt.robust library for reliable connections
with automatic reconnection support.
"""

from typing import Optional, Callable, Dict, Any, Tuple
import time

try:
    from umqtt.robust import MQTTClient
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    MQTTClient = None  # type: ignore

__all__ = ['MQTTBridge', 'MQTTConfig', 'MQTT_AVAILABLE']


class MQTTConfig:
    """MQTT configuration constants."""

    # QoS Levels
    QOS_0 = 0  # At most once delivery
    QOS_1 = 1  # At least once delivery

    # Default values
    DEFAULT_PORT = 1883
    DEFAULT_KEEPALIVE = 60
    DEFAULT_QOS = QOS_0


class MQTTBridge:
    """MQTT client bridge for ESP32 IO Bridge.

    Provides publish/subscribe functionality for remote device control
    via MQTT. Supports GPIO control, status updates, and custom topics.

    Example:
        >>> bridge = MQTTBridge(
        ...     broker="192.168.1.100",
        ...     client_id="esp32-bridge-01"
        ... )
        >>> if bridge.connect():
        ...     bridge.publish_status("online")
        ...     bridge.subscribe_gpio_commands(gpio_command_handler)
    """

    def __init__(
        self,
        broker: str,
        client_id: str,
        port: int = MQTTConfig.DEFAULT_PORT,
        user: Optional[str] = None,
        password: Optional[str] = None,
        keepalive: int = MQTTConfig.DEFAULT_KEEPALIVE,
        topic_prefix: str = "esp32"
    ) -> None:
        """Initialize MQTT bridge.

        Args:
            broker: MQTT broker hostname or IP address
            client_id: Unique client identifier
            port: MQTT broker port (default: 1883)
            user: Username for authentication (optional)
            password: Password for authentication (optional)
            keepalive: Keep-alive interval in seconds (default: 60)
            topic_prefix: Prefix for all MQTT topics (default: "esp32")

        Raises:
            ImportError: If umqtt.robust is not available
        """
        if not MQTT_AVAILABLE:
            raise ImportError("umqtt.robust module not available")

        self.broker = broker
        self.client_id = client_id
        self.port = port
        self.user = user
        self.password = password
        self.keepalive = keepalive
        self.topic_prefix = topic_prefix

        # Initialize client
        self._client: Optional[MQTTClient] = None
        self._connected = False
        self._last_error: Optional[str] = None

        # Callback handlers
        self._message_handlers: Dict[bytes, Callable[[bytes, bytes], None]] = {}
        self._gpio_command_handler: Optional[Callable[[int, int], None]] = None

    def connect(self) -> bool:
        """Connect to MQTT broker.

        Returns:
            True if connected successfully, False otherwise
        """
        try:
            # Create client instance
            if self.user and self.password:
                self._client = MQTTClient(
                    self.client_id,
                    self.broker,
                    port=self.port,
                    user=self.user,
                    password=self.password,
                    keepalive=self.keepalive
                )
            else:
                self._client = MQTTClient(
                    self.client_id,
                    self.broker,
                    port=self.port,
                    keepalive=self.keepalive
                )

            # Set message callback
            self._client.set_callback(self._on_message)

            # Connect to broker
            self._client.connect()
            self._connected = True
            self._last_error = None

            return True

        except Exception as e:
            self._connected = False
            self._last_error = str(e)
            return False

    def disconnect(self) -> None:
        """Disconnect from MQTT broker."""
        if self._client:
            try:
                self._client.disconnect()
            except Exception:
                pass
            finally:
                self._connected = False

    def is_connected(self) -> bool:
        """Check if connected to MQTT broker.

        Returns:
            True if connected, False otherwise
        """
        return self._connected

    def get_error(self) -> Optional[str]:
        """Get last error message.

        Returns:
            Error message string or None if no error
        """
        return self._last_error

    def publish(
        self,
        topic: str,
        message: str,
        qos: int = MQTTConfig.QOS_0,
        retain: bool = False
    ) -> bool:
        """Publish message to MQTT topic.

        Args:
            topic: Topic to publish to (will be prefixed)
            message: Message payload
            qos: Quality of Service level (0 or 1)
            retain: Whether to retain message on broker

        Returns:
            True if published successfully, False otherwise
        """
        if not self._connected or not self._client:
            self._last_error = "Not connected to broker"
            return False

        try:
            full_topic = f"{self.topic_prefix}/{topic}".encode()
            self._client.publish(
                full_topic,
                message.encode(),
                qos=qos,
                retain=retain
            )
            return True

        except Exception as e:
            self._last_error = str(e)
            self._connected = False
            return False

    def subscribe(self, topic: str, qos: int = MQTTConfig.QOS_0) -> bool:
        """Subscribe to MQTT topic.

        Args:
            topic: Topic to subscribe to (will be prefixed)
            qos: Quality of Service level (0 or 1)

        Returns:
            True if subscribed successfully, False otherwise
        """
        if not self._connected or not self._client:
            self._last_error = "Not connected to broker"
            return False

        try:
            full_topic = f"{self.topic_prefix}/{topic}".encode()
            self._client.subscribe(full_topic, qos=qos)
            return True

        except Exception as e:
            self._last_error = str(e)
            return False

    def check_messages(self) -> bool:
        """Check for incoming MQTT messages.

        This should be called periodically to process incoming messages.

        Returns:
            True if check succeeded, False on error
        """
        if not self._connected or not self._client:
            return False

        try:
            self._client.check_msg()
            return True
        except Exception as e:
            self._last_error = str(e)
            self._connected = False
            return False

    def wait_message(self, timeout: int = 1) -> bool:
        """Wait for incoming MQTT message.

        Args:
            timeout: Timeout in seconds (not supported by umqtt, blocks indefinitely)

        Returns:
            True if message received, False on error
        """
        if not self._connected or not self._client:
            return False

        try:
            self._client.wait_msg()
            return True
        except Exception as e:
            self._last_error = str(e)
            self._connected = False
            return False

    def publish_gpio_state(
        self,
        pin: int,
        value: int,
        retain: bool = True
    ) -> bool:
        """Publish GPIO pin state.

        Args:
            pin: GPIO pin number
            value: Pin value (0 or 1 for digital, 0-1023 for PWM)
            retain: Whether to retain state on broker

        Returns:
            True if published successfully
        """
        topic = f"{self.client_id}/gpio/{pin}/state"
        return self.publish(topic, str(value), retain=retain)

    def publish_status(self, status: str, retain: bool = True) -> bool:
        """Publish device status.

        Args:
            status: Status message (e.g., "online", "offline")
            retain: Whether to retain status on broker

        Returns:
            True if published successfully
        """
        topic = f"{self.client_id}/status"
        return self.publish(topic, status, retain=retain)

    def publish_data(
        self,
        sensor: str,
        value: str,
        retain: bool = False
    ) -> bool:
        """Publish sensor data.

        Args:
            sensor: Sensor identifier
            value: Sensor value
            retain: Whether to retain data on broker

        Returns:
            True if published successfully
        """
        topic = f"{self.client_id}/sensor/{sensor}"
        return self.publish(topic, value, retain=retain)

    def subscribe_gpio_commands(
        self,
        handler: Callable[[int, int], None]
    ) -> bool:
        """Subscribe to GPIO command topic.

        Commands should be published to: {prefix}/{client_id}/gpio/{pin}/set
        with payload: "0" or "1" for digital, "0-1023" for PWM

        Args:
            handler: Callback function(pin: int, value: int)

        Returns:
            True if subscribed successfully
        """
        self._gpio_command_handler = handler
        topic = f"{self.client_id}/gpio/+/set"
        return self.subscribe(topic)

    def _on_message(self, topic: bytes, message: bytes) -> None:
        """Internal message callback handler.

        Args:
            topic: MQTT topic
            message: MQTT message payload
        """
        try:
            # Decode topic and message
            topic_str = topic.decode()
            message_str = message.decode()

            # Check for GPIO command
            if "/gpio/" in topic_str and topic_str.endswith("/set"):
                self._handle_gpio_command(topic_str, message_str)

            # Call custom handlers
            if topic in self._message_handlers:
                self._message_handlers[topic](topic, message)

        except Exception as e:
            self._last_error = f"Message handler error: {e}"

    def _handle_gpio_command(self, topic: str, message: str) -> None:
        """Handle GPIO command message.

        Args:
            topic: Topic string (e.g., "esp32/device1/gpio/2/set")
            message: Command value ("0", "1", or "0-1023")
        """
        if not self._gpio_command_handler:
            return

        try:
            # Extract pin number from topic
            # Format: {prefix}/{client_id}/gpio/{pin}/set
            parts = topic.split('/')
            pin = int(parts[-2])

            # Parse value
            value = int(message)

            # Call handler
            self._gpio_command_handler(pin, value)

        except (ValueError, IndexError) as e:
            self._last_error = f"Invalid GPIO command: {e}"

    def add_message_handler(
        self,
        topic: str,
        handler: Callable[[bytes, bytes], None]
    ) -> None:
        """Add custom message handler for a topic.

        Args:
            topic: Topic to handle (without prefix)
            handler: Callback function(topic: bytes, message: bytes)
        """
        full_topic = f"{self.topic_prefix}/{topic}".encode()
        self._message_handlers[full_topic] = handler

    def get_status(self) -> Dict[str, Any]:
        """Get MQTT client status.

        Returns:
            Dictionary with status information
        """
        return {
            'connected': self._connected,
            'broker': self.broker,
            'port': self.port,
            'client_id': self.client_id,
            'topic_prefix': self.topic_prefix,
            'error': self._last_error
        }
