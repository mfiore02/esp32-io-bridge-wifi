"""GPIO handler module for ESP32.

This module provides GPIO control functionality including digital I/O,
PWM (pulse width modulation), ADC (analog to digital conversion), and
interrupt handling.
"""

from typing import Optional, Dict, Any, List, Callable
import time

try:
    from machine import Pin, PWM, ADC
except ImportError:
    # For development/testing on non-MicroPython systems
    Pin = None
    PWM = None
    ADC = None

__all__ = ['GPIOHandler', 'PinMode', 'PullMode', 'IRQTrigger']


class PinMode:
    """Pin mode constants."""
    INPUT = 0
    OUTPUT = 1
    PWM = 2
    ADC = 3


class PullMode:
    """Pull resistor mode constants."""
    NONE = -1
    PULL_UP = 0
    PULL_DOWN = 1


class IRQTrigger:
    """Interrupt trigger mode constants."""
    RISING = 0   # Trigger on rising edge (LOW to HIGH)
    FALLING = 1  # Trigger on falling edge (HIGH to LOW)
    BOTH = 2     # Trigger on both edges


class GPIOHandler:
    """Manage GPIO operations for ESP32.

    Provides safe access to GPIO pins with support for digital I/O,
    PWM, and ADC operations. Includes pin validation and state tracking.

    Example:
        >>> gpio = GPIOHandler()
        >>>
        >>> # Digital output
        >>> gpio.setup_pin(2, PinMode.OUTPUT)
        >>> gpio.digital_write(2, True)
        >>>
        >>> # Digital input with pull-up
        >>> gpio.setup_pin(4, PinMode.INPUT, pull=PullMode.PULL_UP)
        >>> value = gpio.digital_read(4)
        >>>
        >>> # PWM output (LED dimming)
        >>> gpio.setup_pwm(5, freq=1000)
        >>> gpio.set_pwm_duty(5, 512)  # 50% duty cycle
        >>>
        >>> # ADC input (analog sensor)
        >>> gpio.setup_adc(34)
        >>> voltage = gpio.read_adc_voltage(34)
    """

    # ESP32 pin capabilities
    # GPIO pins that can be used for general I/O
    VALID_GPIO_PINS = [0, 2, 4, 5, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23, 25, 26, 27, 32, 33]

    # ADC-capable pins (ADC1 only to avoid WiFi conflicts)
    ADC_PINS = [32, 33, 34, 35, 36, 39]

    # Input-only pins (no pull-up/pull-down)
    INPUT_ONLY_PINS = [34, 35, 36, 39]

    # Strapping pins (use with caution)
    STRAPPING_PINS = [0, 2, 5, 12, 15]

    def __init__(self, allowed_pins: Optional[List[int]] = None) -> None:
        """Initialize GPIO handler.

        Args:
            allowed_pins: List of pins allowed for use. If None, uses VALID_GPIO_PINS
        """
        self.allowed_pins = allowed_pins if allowed_pins is not None else self.VALID_GPIO_PINS.copy()
        self._pins: Dict[int, Any] = {}  # Pin number -> Pin/PWM/ADC object
        self._pin_modes: Dict[int, int] = {}  # Pin number -> mode
        self._pwm_configs: Dict[int, Dict[str, int]] = {}  # Pin -> {freq, duty}
        self._irq_handlers: Dict[int, Callable] = {}  # Pin -> interrupt handler
        self._irq_enabled: Dict[int, bool] = {}  # Pin -> interrupt enabled state

    def is_pin_valid(self, pin: int) -> bool:
        """Check if pin number is valid and allowed.

        Args:
            pin: Pin number to check

        Returns:
            True if pin is valid and allowed
        """
        return pin in self.allowed_pins

    def is_pin_available(self, pin: int) -> bool:
        """Check if pin is available (not already configured).

        Args:
            pin: Pin number to check

        Returns:
            True if pin is available
        """
        return pin not in self._pins

    def setup_pin(
        self,
        pin: int,
        mode: int,
        pull: int = PullMode.NONE,
        value: Optional[bool] = None
    ) -> bool:
        """Setup a GPIO pin for digital I/O.

        Args:
            pin: Pin number
            mode: Pin mode (PinMode.INPUT or PinMode.OUTPUT)
            pull: Pull resistor mode (PullMode.NONE, PULL_UP, or PULL_DOWN)
            value: Initial value for output pins

        Returns:
            True if setup successful

        Example:
            >>> gpio.setup_pin(2, PinMode.OUTPUT, value=False)
            >>> gpio.setup_pin(4, PinMode.INPUT, pull=PullMode.PULL_UP)
        """
        if not Pin:
            return False

        if not self.is_pin_valid(pin):
            return False

        # Release pin if already configured
        if pin in self._pins:
            self.release_pin(pin)

        try:
            # Input-only pins cannot have pull resistors
            if pin in self.INPUT_ONLY_PINS and pull != PullMode.NONE:
                return False

            # Create Pin object
            if mode == PinMode.INPUT:
                if pull == PullMode.PULL_UP:
                    self._pins[pin] = Pin(pin, Pin.IN, Pin.PULL_UP)
                elif pull == PullMode.PULL_DOWN:
                    self._pins[pin] = Pin(pin, Pin.IN, Pin.PULL_DOWN)
                else:
                    self._pins[pin] = Pin(pin, Pin.IN)
            elif mode == PinMode.OUTPUT:
                if value is not None:
                    self._pins[pin] = Pin(pin, Pin.OUT, value=value)
                else:
                    self._pins[pin] = Pin(pin, Pin.OUT)
            else:
                return False

            self._pin_modes[pin] = mode
            return True

        except Exception:
            return False

    def setup_pwm(self, pin: int, freq: int = 1000, duty: int = 0) -> bool:
        """Setup a pin for PWM output.

        Args:
            pin: Pin number
            freq: PWM frequency in Hz (default 1000)
            duty: Initial duty cycle 0-1023 (default 0)

        Returns:
            True if setup successful

        Example:
            >>> gpio.setup_pwm(5, freq=1000, duty=512)  # 50% duty
        """
        if not PWM or not Pin:
            return False

        if not self.is_pin_valid(pin):
            return False

        # Input-only pins cannot do PWM
        if pin in self.INPUT_ONLY_PINS:
            return False

        # Release pin if already configured
        if pin in self._pins:
            self.release_pin(pin)

        try:
            # Create PWM object
            pwm_pin = PWM(Pin(pin))
            pwm_pin.freq(freq)
            pwm_pin.duty(duty)

            self._pins[pin] = pwm_pin
            self._pin_modes[pin] = PinMode.PWM
            self._pwm_configs[pin] = {'freq': freq, 'duty': duty}
            return True

        except Exception:
            return False

    def setup_adc(self, pin: int, atten: int = 3) -> bool:
        """Setup a pin for ADC (analog input).

        Args:
            pin: Pin number (must be ADC-capable)
            atten: Attenuation (0=0-1V, 1=0-1.34V, 2=0-2V, 3=0-3.6V)

        Returns:
            True if setup successful

        Example:
            >>> gpio.setup_adc(34)  # Full 0-3.6V range
        """
        if not ADC:
            return False

        if pin not in self.ADC_PINS:
            return False

        # Release pin if already configured
        if pin in self._pins:
            self.release_pin(pin)

        try:
            adc = ADC(Pin(pin))
            adc.atten(atten)

            self._pins[pin] = adc
            self._pin_modes[pin] = PinMode.ADC
            return True

        except Exception:
            return False

    def digital_write(self, pin: int, value: bool) -> bool:
        """Write digital value to output pin.

        Args:
            pin: Pin number
            value: True for HIGH, False for LOW

        Returns:
            True if write successful

        Example:
            >>> gpio.digital_write(2, True)   # Set HIGH
            >>> gpio.digital_write(2, False)  # Set LOW
        """
        if pin not in self._pins:
            return False

        if self._pin_modes.get(pin) != PinMode.OUTPUT:
            return False

        try:
            self._pins[pin].value(1 if value else 0)
            return True
        except Exception:
            return False

    def digital_read(self, pin: int) -> Optional[bool]:
        """Read digital value from input pin.

        Args:
            pin: Pin number

        Returns:
            True for HIGH, False for LOW, None on error

        Example:
            >>> value = gpio.digital_read(4)
            >>> if value:
            ...     print("Button pressed")
        """
        if pin not in self._pins:
            return None

        if self._pin_modes.get(pin) not in [PinMode.INPUT, PinMode.OUTPUT]:
            return None

        try:
            return bool(self._pins[pin].value())
        except Exception:
            return None

    def set_pwm_duty(self, pin: int, duty: int) -> bool:
        """Set PWM duty cycle.

        Args:
            pin: Pin number
            duty: Duty cycle 0-1023 (0=0%, 1023=100%)

        Returns:
            True if successful

        Example:
            >>> gpio.set_pwm_duty(5, 256)   # 25%
            >>> gpio.set_pwm_duty(5, 512)   # 50%
            >>> gpio.set_pwm_duty(5, 1023)  # 100%
        """
        if pin not in self._pins:
            return False

        if self._pin_modes.get(pin) != PinMode.PWM:
            return False

        try:
            duty = max(0, min(1023, duty))  # Clamp to valid range
            self._pins[pin].duty(duty)
            self._pwm_configs[pin]['duty'] = duty
            return True
        except Exception:
            return False

    def set_pwm_freq(self, pin: int, freq: int) -> bool:
        """Set PWM frequency.

        Args:
            pin: Pin number
            freq: Frequency in Hz (1-40000000)

        Returns:
            True if successful

        Example:
            >>> gpio.set_pwm_freq(5, 2000)  # 2kHz
        """
        if pin not in self._pins:
            return False

        if self._pin_modes.get(pin) != PinMode.PWM:
            return False

        try:
            self._pins[pin].freq(freq)
            self._pwm_configs[pin]['freq'] = freq
            return True
        except Exception:
            return False

    def read_adc(self, pin: int) -> Optional[int]:
        """Read raw ADC value.

        Args:
            pin: Pin number

        Returns:
            ADC value 0-4095, or None on error

        Example:
            >>> raw = gpio.read_adc(34)
            >>> print(f"Raw ADC: {raw}")
        """
        if pin not in self._pins:
            return None

        if self._pin_modes.get(pin) != PinMode.ADC:
            return None

        try:
            return self._pins[pin].read()
        except Exception:
            return None

    def read_adc_voltage(self, pin: int) -> Optional[float]:
        """Read ADC value as voltage.

        Args:
            pin: Pin number

        Returns:
            Voltage in volts (0.0-3.6V), or None on error

        Example:
            >>> voltage = gpio.read_adc_voltage(34)
            >>> print(f"Voltage: {voltage:.2f}V")
        """
        raw = self.read_adc(pin)
        if raw is None:
            return None

        # Convert 12-bit ADC value to voltage (assuming 3.6V attenuation)
        return (raw / 4095.0) * 3.6

    def release_pin(self, pin: int) -> bool:
        """Release a configured pin.

        Args:
            pin: Pin number

        Returns:
            True if released successfully
        """
        if pin not in self._pins:
            return False

        try:
            # Disable interrupts if enabled
            if pin in self._irq_enabled and self._irq_enabled[pin]:
                self.disable_interrupt(pin)

            # Deinitialize PWM if applicable
            if self._pin_modes.get(pin) == PinMode.PWM:
                self._pins[pin].deinit()

            del self._pins[pin]
            del self._pin_modes[pin]

            if pin in self._pwm_configs:
                del self._pwm_configs[pin]

            if pin in self._irq_handlers:
                del self._irq_handlers[pin]

            if pin in self._irq_enabled:
                del self._irq_enabled[pin]

            return True
        except Exception:
            return False

    def setup_interrupt(
        self,
        pin: int,
        trigger: int,
        handler: Callable[[Any], None],
        pull: int = PullMode.NONE
    ) -> bool:
        """Setup interrupt on a pin.

        Args:
            pin: Pin number
            trigger: Interrupt trigger mode (IRQTrigger.RISING, FALLING, or BOTH)
            handler: Callback function to call when interrupt fires
            pull: Pull resistor mode

        Returns:
            True if setup successful

        Example:
            >>> def button_pressed(pin):
            ...     print(f"Button on pin {pin} pressed!")
            >>>
            >>> gpio.setup_interrupt(4, IRQTrigger.FALLING, button_pressed, pull=PullMode.PULL_UP)
            >>> gpio.enable_interrupt(4)
        """
        if not Pin:
            return False

        if not self.is_pin_valid(pin):
            return False

        # Input-only pins cannot have pull resistors
        if pin in self.INPUT_ONLY_PINS and pull != PullMode.NONE:
            return False

        # Release pin if already configured
        if pin in self._pins:
            self.release_pin(pin)

        try:
            # Create Pin object with appropriate pull mode
            if pull == PullMode.PULL_UP:
                pin_obj = Pin(pin, Pin.IN, Pin.PULL_UP)
            elif pull == PullMode.PULL_DOWN:
                pin_obj = Pin(pin, Pin.IN, Pin.PULL_DOWN)
            else:
                pin_obj = Pin(pin, Pin.IN)

            # Map trigger mode to Pin IRQ constants
            if trigger == IRQTrigger.RISING:
                irq_trigger = Pin.IRQ_RISING
            elif trigger == IRQTrigger.FALLING:
                irq_trigger = Pin.IRQ_FALLING
            elif trigger == IRQTrigger.BOTH:
                irq_trigger = Pin.IRQ_RISING | Pin.IRQ_FALLING
            else:
                return False

            # Setup interrupt (but don't enable yet)
            pin_obj.irq(handler=handler, trigger=irq_trigger)

            self._pins[pin] = pin_obj
            self._pin_modes[pin] = PinMode.INPUT
            self._irq_handlers[pin] = handler
            self._irq_enabled[pin] = True  # IRQ is enabled by default after setup

            return True

        except Exception:
            return False

    def enable_interrupt(self, pin: int) -> bool:
        """Enable interrupt on a pin.

        Args:
            pin: Pin number

        Returns:
            True if enabled successfully

        Example:
            >>> gpio.enable_interrupt(4)
        """
        if pin not in self._pins:
            return False

        if pin not in self._irq_handlers:
            return False

        try:
            # Re-attach the interrupt handler
            handler = self._irq_handlers[pin]

            # Determine the trigger mode (we'll use BOTH as we don't track it)
            # In practice, this re-enables with the same trigger as before
            self._pins[pin].irq(handler=handler)

            self._irq_enabled[pin] = True
            return True

        except Exception:
            return False

    def disable_interrupt(self, pin: int) -> bool:
        """Disable interrupt on a pin.

        Args:
            pin: Pin number

        Returns:
            True if disabled successfully

        Example:
            >>> gpio.disable_interrupt(4)
        """
        if pin not in self._pins:
            return False

        if pin not in self._irq_handlers:
            return False

        try:
            # Disable by setting handler to None
            self._pins[pin].irq(handler=None)
            self._irq_enabled[pin] = False
            return True

        except Exception:
            return False

    def is_interrupt_enabled(self, pin: int) -> bool:
        """Check if interrupt is enabled on a pin.

        Args:
            pin: Pin number

        Returns:
            True if interrupt is enabled

        Example:
            >>> if gpio.is_interrupt_enabled(4):
            ...     print("Interrupt active")
        """
        return self._irq_enabled.get(pin, False)

    def get_pin_status(self, pin: int) -> Optional[Dict[str, Any]]:
        """Get status of a configured pin.

        Args:
            pin: Pin number

        Returns:
            Dictionary with pin status or None if not configured

        Example:
            >>> status = gpio.get_pin_status(5)
            >>> print(status)
            {'pin': 5, 'mode': 'PWM', 'freq': 1000, 'duty': 512}
        """
        if pin not in self._pins:
            return None

        mode = self._pin_modes.get(pin)
        mode_name = self._get_mode_name(mode)

        status: Dict[str, Any] = {
            'pin': pin,
            'mode': mode_name,
            'configured': True
        }

        if mode == PinMode.INPUT or mode == PinMode.OUTPUT:
            value = self.digital_read(pin)
            status['value'] = value

        if mode == PinMode.PWM:
            status.update(self._pwm_configs.get(pin, {}))

        if mode == PinMode.ADC:
            raw = self.read_adc(pin)
            voltage = self.read_adc_voltage(pin)
            status['raw'] = raw
            status['voltage'] = voltage

        # Add interrupt information if applicable
        if pin in self._irq_handlers:
            status['interrupt_enabled'] = self._irq_enabled.get(pin, False)
            status['has_interrupt'] = True
        else:
            status['has_interrupt'] = False

        return status

    def get_all_pins_status(self) -> Dict[int, Dict[str, Any]]:
        """Get status of all configured pins.

        Returns:
            Dictionary mapping pin numbers to their status
        """
        return {pin: self.get_pin_status(pin) for pin in self._pins}

    @staticmethod
    def _get_mode_name(mode: Optional[int]) -> str:
        """Get human-readable mode name.

        Args:
            mode: Pin mode constant

        Returns:
            Mode name string
        """
        mode_names = {
            PinMode.INPUT: 'INPUT',
            PinMode.OUTPUT: 'OUTPUT',
            PinMode.PWM: 'PWM',
            PinMode.ADC: 'ADC'
        }
        return mode_names.get(mode, 'UNKNOWN') if mode is not None else 'UNKNOWN'
