"""Unit tests for MQTT client module.

Run with: python3 tests/test_mqtt_client.py
"""

import sys
import os
import unittest
from unittest.mock import Mock, MagicMock, patch, call
from typing import Optional, Any

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'lib'))

# Mock umqtt.robust before importing our module
sys.modules['umqtt.robust'] = MagicMock()

from lib.mqtt.client import MQTTBridge, MQTTConfig, MQTT_AVAILABLE


class TestMQTTConfig(unittest.TestCase):
    """Test MQTT configuration constants."""

    def test_qos_values(self) -> None:
        """Test that QoS constants have correct values."""
        self.assertEqual(MQTTConfig.QOS_0, 0)
        self.assertEqual(MQTTConfig.QOS_1, 1)

    def test_qos_unique(self) -> None:
        """Test that QoS values are unique."""
        self.assertNotEqual(MQTTConfig.QOS_0, MQTTConfig.QOS_1)

    def test_default_port(self) -> None:
        """Test default MQTT port."""
        self.assertEqual(MQTTConfig.DEFAULT_PORT, 1883)

    def test_default_keepalive(self) -> None:
        """Test default keep-alive value."""
        self.assertEqual(MQTTConfig.DEFAULT_KEEPALIVE, 60)

    def test_default_qos(self) -> None:
        """Test default QoS value."""
        self.assertEqual(MQTTConfig.DEFAULT_QOS, 0)


class TestMQTTBridge(unittest.TestCase):
    """Test MQTT bridge functionality."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        # Force MQTT to be available for testing
        import lib.mqtt.client as mqtt_module
        mqtt_module.MQTT_AVAILABLE = True

        self.broker = "192.168.1.100"
        self.client_id = "test-device"
        self.port = 1883
        self.topic_prefix = "esp32"

    def test_initialization_basic(self) -> None:
        """Test basic MQTT bridge initialization."""
        bridge = MQTTBridge(
            broker=self.broker,
            client_id=self.client_id
        )

        self.assertEqual(bridge.broker, self.broker)
        self.assertEqual(bridge.client_id, self.client_id)
        self.assertEqual(bridge.port, MQTTConfig.DEFAULT_PORT)
        self.assertIsNone(bridge.user)
        self.assertIsNone(bridge.password)
        self.assertEqual(bridge.keepalive, MQTTConfig.DEFAULT_KEEPALIVE)
        self.assertEqual(bridge.topic_prefix, "esp32")

    def test_initialization_with_auth(self) -> None:
        """Test initialization with authentication."""
        bridge = MQTTBridge(
            broker=self.broker,
            client_id=self.client_id,
            user="testuser",
            password="testpass"
        )

        self.assertEqual(bridge.user, "testuser")
        self.assertEqual(bridge.password, "testpass")

    def test_initialization_with_custom_params(self) -> None:
        """Test initialization with custom parameters."""
        bridge = MQTTBridge(
            broker=self.broker,
            client_id=self.client_id,
            port=8883,
            keepalive=120,
            topic_prefix="custom"
        )

        self.assertEqual(bridge.port, 8883)
        self.assertEqual(bridge.keepalive, 120)
        self.assertEqual(bridge.topic_prefix, "custom")

    def test_initial_connected_state(self) -> None:
        """Test that initial state is not connected."""
        bridge = MQTTBridge(self.broker, self.client_id)
        self.assertFalse(bridge.is_connected())

    def test_initial_error_is_none(self) -> None:
        """Test that initial error is None."""
        bridge = MQTTBridge(self.broker, self.client_id)
        self.assertIsNone(bridge.get_error())

    @patch('lib.mqtt.client.MQTTClient')
    def test_connect_without_auth(self, mock_mqtt_class: Mock) -> None:
        """Test connecting without authentication."""
        mock_client = Mock()
        mock_mqtt_class.return_value = mock_client

        bridge = MQTTBridge(self.broker, self.client_id)
        result = bridge.connect()

        self.assertTrue(result)
        self.assertTrue(bridge.is_connected())
        mock_mqtt_class.assert_called_once()
        mock_client.set_callback.assert_called_once()
        mock_client.connect.assert_called_once()

    @patch('lib.mqtt.client.MQTTClient')
    def test_connect_with_auth(self, mock_mqtt_class: Mock) -> None:
        """Test connecting with authentication."""
        mock_client = Mock()
        mock_mqtt_class.return_value = mock_client

        bridge = MQTTBridge(
            self.broker,
            self.client_id,
            user="user",
            password="pass"
        )
        result = bridge.connect()

        self.assertTrue(result)
        mock_client.connect.assert_called_once()

    @patch('lib.mqtt.client.MQTTClient')
    def test_connect_failure(self, mock_mqtt_class: Mock) -> None:
        """Test connection failure handling."""
        mock_client = Mock()
        mock_client.connect.side_effect = Exception("Connection failed")
        mock_mqtt_class.return_value = mock_client

        bridge = MQTTBridge(self.broker, self.client_id)
        result = bridge.connect()

        self.assertFalse(result)
        self.assertFalse(bridge.is_connected())
        self.assertIsNotNone(bridge.get_error())

    @patch('lib.mqtt.client.MQTTClient')
    def test_disconnect(self, mock_mqtt_class: Mock) -> None:
        """Test disconnecting from broker."""
        mock_client = Mock()
        mock_mqtt_class.return_value = mock_client

        bridge = MQTTBridge(self.broker, self.client_id)
        bridge.connect()
        bridge.disconnect()

        self.assertFalse(bridge.is_connected())
        mock_client.disconnect.assert_called_once()

    @patch('lib.mqtt.client.MQTTClient')
    def test_disconnect_when_not_connected(self, mock_mqtt_class: Mock) -> None:
        """Test disconnect when not connected doesn't crash."""
        bridge = MQTTBridge(self.broker, self.client_id)
        bridge.disconnect()  # Should not raise exception

        self.assertFalse(bridge.is_connected())

    @patch('lib.mqtt.client.MQTTClient')
    def test_publish_basic(self, mock_mqtt_class: Mock) -> None:
        """Test basic message publishing."""
        mock_client = Mock()
        mock_mqtt_class.return_value = mock_client

        bridge = MQTTBridge(self.broker, self.client_id)
        bridge.connect()
        result = bridge.publish("test/topic", "test message")

        self.assertTrue(result)
        mock_client.publish.assert_called_once()

    @patch('lib.mqtt.client.MQTTClient')
    def test_publish_with_qos_and_retain(self, mock_mqtt_class: Mock) -> None:
        """Test publishing with QoS and retain flags."""
        mock_client = Mock()
        mock_mqtt_class.return_value = mock_client

        bridge = MQTTBridge(self.broker, self.client_id)
        bridge.connect()
        result = bridge.publish(
            "test/topic",
            "message",
            qos=MQTTConfig.QOS_1,
            retain=True
        )

        self.assertTrue(result)
        mock_client.publish.assert_called_once()
        args, kwargs = mock_client.publish.call_args
        self.assertEqual(kwargs.get('qos'), 1)
        self.assertEqual(kwargs.get('retain'), True)

    @patch('lib.mqtt.client.MQTTClient')
    def test_publish_when_not_connected(self, mock_mqtt_class: Mock) -> None:
        """Test publish fails when not connected."""
        bridge = MQTTBridge(self.broker, self.client_id)
        result = bridge.publish("test/topic", "message")

        self.assertFalse(result)
        self.assertIsNotNone(bridge.get_error())

    @patch('lib.mqtt.client.MQTTClient')
    def test_subscribe_basic(self, mock_mqtt_class: Mock) -> None:
        """Test basic topic subscription."""
        mock_client = Mock()
        mock_mqtt_class.return_value = mock_client

        bridge = MQTTBridge(self.broker, self.client_id)
        bridge.connect()
        result = bridge.subscribe("test/topic")

        self.assertTrue(result)
        mock_client.subscribe.assert_called_once()

    @patch('lib.mqtt.client.MQTTClient')
    def test_subscribe_with_qos(self, mock_mqtt_class: Mock) -> None:
        """Test subscription with custom QoS."""
        mock_client = Mock()
        mock_mqtt_class.return_value = mock_client

        bridge = MQTTBridge(self.broker, self.client_id)
        bridge.connect()
        result = bridge.subscribe("test/topic", qos=MQTTConfig.QOS_1)

        self.assertTrue(result)
        mock_client.subscribe.assert_called_once()

    @patch('lib.mqtt.client.MQTTClient')
    def test_subscribe_when_not_connected(self, mock_mqtt_class: Mock) -> None:
        """Test subscribe fails when not connected."""
        bridge = MQTTBridge(self.broker, self.client_id)
        result = bridge.subscribe("test/topic")

        self.assertFalse(result)
        self.assertIsNotNone(bridge.get_error())

    @patch('lib.mqtt.client.MQTTClient')
    def test_check_messages(self, mock_mqtt_class: Mock) -> None:
        """Test checking for messages."""
        mock_client = Mock()
        mock_mqtt_class.return_value = mock_client

        bridge = MQTTBridge(self.broker, self.client_id)
        bridge.connect()
        result = bridge.check_messages()

        self.assertTrue(result)
        mock_client.check_msg.assert_called_once()

    @patch('lib.mqtt.client.MQTTClient')
    def test_check_messages_when_not_connected(self, mock_mqtt_class: Mock) -> None:
        """Test check_messages returns False when not connected."""
        bridge = MQTTBridge(self.broker, self.client_id)
        result = bridge.check_messages()

        self.assertFalse(result)

    @patch('lib.mqtt.client.MQTTClient')
    def test_publish_gpio_state(self, mock_mqtt_class: Mock) -> None:
        """Test publishing GPIO state."""
        mock_client = Mock()
        mock_mqtt_class.return_value = mock_client

        bridge = MQTTBridge(self.broker, self.client_id)
        bridge.connect()
        result = bridge.publish_gpio_state(2, 1)

        self.assertTrue(result)
        mock_client.publish.assert_called_once()
        args = mock_client.publish.call_args[0]
        self.assertIn(b'gpio/2/state', args[0])
        self.assertEqual(args[1], b'1')

    @patch('lib.mqtt.client.MQTTClient')
    def test_publish_gpio_state_with_pwm_value(self, mock_mqtt_class: Mock) -> None:
        """Test publishing GPIO PWM value."""
        mock_client = Mock()
        mock_mqtt_class.return_value = mock_client

        bridge = MQTTBridge(self.broker, self.client_id)
        bridge.connect()
        result = bridge.publish_gpio_state(5, 512)

        self.assertTrue(result)
        args = mock_client.publish.call_args[0]
        self.assertEqual(args[1], b'512')

    @patch('lib.mqtt.client.MQTTClient')
    def test_publish_status(self, mock_mqtt_class: Mock) -> None:
        """Test publishing device status."""
        mock_client = Mock()
        mock_mqtt_class.return_value = mock_client

        bridge = MQTTBridge(self.broker, self.client_id)
        bridge.connect()
        result = bridge.publish_status("online")

        self.assertTrue(result)
        args = mock_client.publish.call_args[0]
        self.assertIn(b'status', args[0])
        self.assertEqual(args[1], b'online')

    @patch('lib.mqtt.client.MQTTClient')
    def test_publish_data(self, mock_mqtt_class: Mock) -> None:
        """Test publishing sensor data."""
        mock_client = Mock()
        mock_mqtt_class.return_value = mock_client

        bridge = MQTTBridge(self.broker, self.client_id)
        bridge.connect()
        result = bridge.publish_data("temperature", "25.5")

        self.assertTrue(result)
        args = mock_client.publish.call_args[0]
        self.assertIn(b'sensor/temperature', args[0])
        self.assertEqual(args[1], b'25.5')

    @patch('lib.mqtt.client.MQTTClient')
    def test_subscribe_gpio_commands(self, mock_mqtt_class: Mock) -> None:
        """Test subscribing to GPIO commands."""
        mock_client = Mock()
        mock_mqtt_class.return_value = mock_client

        handler = Mock()
        bridge = MQTTBridge(self.broker, self.client_id)
        bridge.connect()
        result = bridge.subscribe_gpio_commands(handler)

        self.assertTrue(result)
        mock_client.subscribe.assert_called_once()
        args = mock_client.subscribe.call_args[0]
        self.assertIn(b'gpio/+/set', args[0])

    @patch('lib.mqtt.client.MQTTClient')
    def test_gpio_command_handler_called(self, mock_mqtt_class: Mock) -> None:
        """Test that GPIO command handler is called on message."""
        mock_client = Mock()
        mock_mqtt_class.return_value = mock_client

        handler = Mock()
        bridge = MQTTBridge(self.broker, self.client_id)
        bridge.connect()
        bridge.subscribe_gpio_commands(handler)

        # Simulate incoming message
        topic = b'esp32/test-device/gpio/2/set'
        message = b'1'
        bridge._on_message(topic, message)

        handler.assert_called_once_with(2, 1)

    @patch('lib.mqtt.client.MQTTClient')
    def test_gpio_command_invalid_format(self, mock_mqtt_class: Mock) -> None:
        """Test handling of invalid GPIO command format."""
        mock_client = Mock()
        mock_mqtt_class.return_value = mock_client

        handler = Mock()
        bridge = MQTTBridge(self.broker, self.client_id)
        bridge.connect()
        bridge.subscribe_gpio_commands(handler)

        # Invalid topic format
        topic = b'esp32/test-device/invalid'
        message = b'1'
        bridge._on_message(topic, message)

        # Handler should not be called
        handler.assert_not_called()

    @patch('lib.mqtt.client.MQTTClient')
    def test_gpio_command_invalid_value(self, mock_mqtt_class: Mock) -> None:
        """Test handling of invalid GPIO command value."""
        mock_client = Mock()
        mock_mqtt_class.return_value = mock_client

        handler = Mock()
        bridge = MQTTBridge(self.broker, self.client_id)
        bridge.connect()
        bridge.subscribe_gpio_commands(handler)

        # Invalid value
        topic = b'esp32/test-device/gpio/2/set'
        message = b'invalid'
        bridge._on_message(topic, message)

        # Handler should not be called
        handler.assert_not_called()
        self.assertIsNotNone(bridge.get_error())

    @patch('lib.mqtt.client.MQTTClient')
    def test_add_custom_message_handler(self, mock_mqtt_class: Mock) -> None:
        """Test adding custom message handler."""
        mock_client = Mock()
        mock_mqtt_class.return_value = mock_client

        handler = Mock()
        bridge = MQTTBridge(self.broker, self.client_id)
        bridge.connect()
        bridge.add_message_handler("custom/topic", handler)

        # Simulate message
        topic = b'esp32/custom/topic'
        message = b'test'
        bridge._on_message(topic, message)

        handler.assert_called_once_with(topic, message)

    @patch('lib.mqtt.client.MQTTClient')
    def test_get_status(self, mock_mqtt_class: Mock) -> None:
        """Test getting MQTT client status."""
        mock_client = Mock()
        mock_mqtt_class.return_value = mock_client

        bridge = MQTTBridge(self.broker, self.client_id)
        bridge.connect()
        status = bridge.get_status()

        self.assertIsInstance(status, dict)
        self.assertTrue(status['connected'])
        self.assertEqual(status['broker'], self.broker)
        self.assertEqual(status['port'], self.port)
        self.assertEqual(status['client_id'], self.client_id)
        self.assertEqual(status['topic_prefix'], self.topic_prefix)

    @patch('lib.mqtt.client.MQTTClient')
    def test_get_status_when_not_connected(self, mock_mqtt_class: Mock) -> None:
        """Test status when not connected."""
        bridge = MQTTBridge(self.broker, self.client_id)
        status = bridge.get_status()

        self.assertFalse(status['connected'])
        self.assertEqual(status['broker'], self.broker)

    def test_mqtt_available_flag(self) -> None:
        """Test that MQTT_AVAILABLE flag is set."""
        # We mocked umqtt.robust, so it should be available
        import lib.mqtt.client as mqtt_module
        self.assertTrue(mqtt_module.MQTT_AVAILABLE)


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
