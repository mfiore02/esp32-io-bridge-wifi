"""IO Bridge modules for GPIO and peripheral communication.

This package provides IO bridging functionality including GPIO control,
UART bridging, and communication protocols.
"""

from .gpio_handler import GPIOHandler, PinMode, PullMode, IRQTrigger

__all__ = ['GPIOHandler', 'PinMode', 'PullMode', 'IRQTrigger']
__version__ = '1.0.0'
