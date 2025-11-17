"""MQTT Client Package for ESP32 IO Bridge.

This package provides MQTT client functionality for remote device
control and monitoring over MQTT protocol.
"""

from .client import MQTTBridge, MQTTConfig, MQTT_AVAILABLE

__all__ = ['MQTTBridge', 'MQTTConfig', 'MQTT_AVAILABLE']
__version__ = '1.0.0'
