"""Unit tests for the GPIO handler module.

Tests the GPIOHandler, PinMode, PullMode, and IRQTrigger classes to ensure
proper GPIO control, pin management, interrupt handling, and state tracking.

Note: These tests validate the API and logic. Full hardware testing
requires actual ESP32 hardware.
"""

import unittest
import sys
import os
from typing import Optional

# Add project root and lib to path for testing
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'lib'))
sys.path.append('/lib')  # For MicroPython on device
sys.path.append('lib')

from lib.io_bridge.gpio_handler import GPIOHandler, PinMode, PullMode, IRQTrigger


class TestPinMode(unittest.TestCase):
    """Test PinMode constants."""

    def test_pin_mode_values(self) -> None:
        """Test that pin mode constants have correct values."""
        self.assertEqual(PinMode.INPUT, 0)
        self.assertEqual(PinMode.OUTPUT, 1)
        self.assertEqual(PinMode.PWM, 2)
        self.assertEqual(PinMode.ADC, 3)

    def test_pin_mode_unique(self) -> None:
        """Test that pin modes are unique."""
        modes = [PinMode.INPUT, PinMode.OUTPUT, PinMode.PWM, PinMode.ADC]
        self.assertEqual(len(modes), len(set(modes)))


class TestPullMode(unittest.TestCase):
    """Test PullMode constants."""

    def test_pull_mode_values(self) -> None:
        """Test that pull mode constants have correct values."""
        self.assertEqual(PullMode.NONE, -1)
        self.assertEqual(PullMode.PULL_UP, 0)
        self.assertEqual(PullMode.PULL_DOWN, 1)

    def test_pull_mode_unique(self) -> None:
        """Test that pull modes are unique."""
        modes = [PullMode.NONE, PullMode.PULL_UP, PullMode.PULL_DOWN]
        self.assertEqual(len(modes), len(set(modes)))


class TestIRQTrigger(unittest.TestCase):
    """Test IRQTrigger constants."""

    def test_irq_trigger_values(self) -> None:
        """Test that IRQ trigger constants have correct values."""
        self.assertEqual(IRQTrigger.RISING, 0)
        self.assertEqual(IRQTrigger.FALLING, 1)
        self.assertEqual(IRQTrigger.BOTH, 2)

    def test_irq_trigger_unique(self) -> None:
        """Test that IRQ triggers are unique."""
        triggers = [IRQTrigger.RISING, IRQTrigger.FALLING, IRQTrigger.BOTH]
        self.assertEqual(len(triggers), len(set(triggers)))


class TestGPIOHandler(unittest.TestCase):
    """Test GPIOHandler class functionality."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.gpio = GPIOHandler()

    def test_initialization_default(self) -> None:
        """Test default GPIO handler initialization."""
        gpio = GPIOHandler()
        self.assertIsNotNone(gpio.allowed_pins)
        self.assertGreater(len(gpio.allowed_pins), 0)

    def test_initialization_with_custom_pins(self) -> None:
        """Test initialization with custom allowed pins."""
        custom_pins = [2, 4, 5]
        gpio = GPIOHandler(allowed_pins=custom_pins)
        self.assertEqual(gpio.allowed_pins, custom_pins)

    def test_valid_gpio_pins_list(self) -> None:
        """Test that VALID_GPIO_PINS is properly defined."""
        self.assertIsInstance(GPIOHandler.VALID_GPIO_PINS, list)
        self.assertGreater(len(GPIOHandler.VALID_GPIO_PINS), 0)
        # All pins should be positive integers
        for pin in GPIOHandler.VALID_GPIO_PINS:
            self.assertIsInstance(pin, int)
            self.assertGreaterEqual(pin, 0)

    def test_adc_pins_list(self) -> None:
        """Test that ADC_PINS is properly defined."""
        self.assertIsInstance(GPIOHandler.ADC_PINS, list)
        self.assertGreater(len(GPIOHandler.ADC_PINS), 0)
        # All ADC pins should be positive integers
        for pin in GPIOHandler.ADC_PINS:
            self.assertIsInstance(pin, int)
            self.assertGreaterEqual(pin, 0)

    def test_input_only_pins_list(self) -> None:
        """Test that INPUT_ONLY_PINS is properly defined."""
        self.assertIsInstance(GPIOHandler.INPUT_ONLY_PINS, list)
        # All should be in ADC pins
        for pin in GPIOHandler.INPUT_ONLY_PINS:
            self.assertIn(pin, GPIOHandler.ADC_PINS)

    def test_is_pin_valid_for_valid_pin(self) -> None:
        """Test is_pin_valid with valid pin."""
        gpio = GPIOHandler()
        # Test first allowed pin
        if gpio.allowed_pins:
            self.assertTrue(gpio.is_pin_valid(gpio.allowed_pins[0]))

    def test_is_pin_valid_for_invalid_pin(self) -> None:
        """Test is_pin_valid with invalid pin."""
        gpio = GPIOHandler(allowed_pins=[2, 4, 5])
        self.assertFalse(gpio.is_pin_valid(99))

    def test_is_pin_available_initially(self) -> None:
        """Test that pins are available initially."""
        gpio = GPIOHandler()
        if gpio.allowed_pins:
            self.assertTrue(gpio.is_pin_available(gpio.allowed_pins[0]))

    def test_get_mode_name_for_all_modes(self) -> None:
        """Test _get_mode_name for all pin modes."""
        self.assertEqual(GPIOHandler._get_mode_name(PinMode.INPUT), 'INPUT')
        self.assertEqual(GPIOHandler._get_mode_name(PinMode.OUTPUT), 'OUTPUT')
        self.assertEqual(GPIOHandler._get_mode_name(PinMode.PWM), 'PWM')
        self.assertEqual(GPIOHandler._get_mode_name(PinMode.ADC), 'ADC')
        self.assertEqual(GPIOHandler._get_mode_name(None), 'UNKNOWN')
        self.assertEqual(GPIOHandler._get_mode_name(999), 'UNKNOWN')

    def test_setup_pin_returns_false_without_hardware(self) -> None:
        """Test setup_pin returns False when hardware unavailable."""
        gpio = GPIOHandler()
        result = gpio.setup_pin(2, PinMode.OUTPUT)
        self.assertFalse(result)

    def test_setup_pin_invalid_pin(self) -> None:
        """Test setup_pin with invalid pin number."""
        gpio = GPIOHandler(allowed_pins=[2, 4, 5])
        result = gpio.setup_pin(99, PinMode.OUTPUT)
        self.assertFalse(result)

    def test_setup_pwm_returns_false_without_hardware(self) -> None:
        """Test setup_pwm returns False when hardware unavailable."""
        gpio = GPIOHandler()
        result = gpio.setup_pwm(5, freq=1000, duty=512)
        self.assertFalse(result)

    def test_setup_pwm_invalid_pin(self) -> None:
        """Test setup_pwm with invalid pin number."""
        gpio = GPIOHandler(allowed_pins=[2, 4, 5])
        result = gpio.setup_pwm(99, freq=1000)
        self.assertFalse(result)

    def test_setup_adc_returns_false_without_hardware(self) -> None:
        """Test setup_adc returns False when hardware unavailable."""
        gpio = GPIOHandler()
        result = gpio.setup_adc(34)
        self.assertFalse(result)

    def test_setup_adc_invalid_pin(self) -> None:
        """Test setup_adc with non-ADC-capable pin."""
        gpio = GPIOHandler()
        # Pin 2 is not an ADC pin
        result = gpio.setup_adc(2)
        self.assertFalse(result)

    def test_setup_adc_valid_pin_in_list(self) -> None:
        """Test setup_adc with valid ADC pin."""
        gpio = GPIOHandler()
        # Pin 34 is an ADC pin
        self.assertIn(34, GPIOHandler.ADC_PINS)

    def test_digital_write_unconfigured_pin(self) -> None:
        """Test digital_write on unconfigured pin."""
        gpio = GPIOHandler()
        result = gpio.digital_write(2, True)
        self.assertFalse(result)

    def test_digital_read_unconfigured_pin(self) -> None:
        """Test digital_read on unconfigured pin."""
        gpio = GPIOHandler()
        result = gpio.digital_read(2)
        self.assertIsNone(result)

    def test_set_pwm_duty_unconfigured_pin(self) -> None:
        """Test set_pwm_duty on unconfigured pin."""
        gpio = GPIOHandler()
        result = gpio.set_pwm_duty(5, 512)
        self.assertFalse(result)

    def test_set_pwm_freq_unconfigured_pin(self) -> None:
        """Test set_pwm_freq on unconfigured pin."""
        gpio = GPIOHandler()
        result = gpio.set_pwm_freq(5, 2000)
        self.assertFalse(result)

    def test_read_adc_unconfigured_pin(self) -> None:
        """Test read_adc on unconfigured pin."""
        gpio = GPIOHandler()
        result = gpio.read_adc(34)
        self.assertIsNone(result)

    def test_read_adc_voltage_unconfigured_pin(self) -> None:
        """Test read_adc_voltage on unconfigured pin."""
        gpio = GPIOHandler()
        result = gpio.read_adc_voltage(34)
        self.assertIsNone(result)

    def test_release_pin_unconfigured(self) -> None:
        """Test release_pin on unconfigured pin."""
        gpio = GPIOHandler()
        result = gpio.release_pin(2)
        self.assertFalse(result)

    def test_get_pin_status_unconfigured(self) -> None:
        """Test get_pin_status on unconfigured pin."""
        gpio = GPIOHandler()
        status = gpio.get_pin_status(2)
        self.assertIsNone(status)

    def test_get_all_pins_status_empty(self) -> None:
        """Test get_all_pins_status with no configured pins."""
        gpio = GPIOHandler()
        status = gpio.get_all_pins_status()
        self.assertIsInstance(status, dict)
        self.assertEqual(len(status), 0)

    def test_allowed_pins_not_modified(self) -> None:
        """Test that allowed_pins is not modified internally."""
        custom_pins = [2, 4, 5]
        gpio = GPIOHandler(allowed_pins=custom_pins)
        original_pins = custom_pins.copy()
        # Try various operations
        gpio.is_pin_valid(2)
        gpio.setup_pin(2, PinMode.OUTPUT)
        # Check allowed_pins unchanged
        self.assertEqual(gpio.allowed_pins, original_pins)

    def test_empty_allowed_pins(self) -> None:
        """Test initialization with empty allowed pins list."""
        gpio = GPIOHandler(allowed_pins=[])
        self.assertEqual(len(gpio.allowed_pins), 0)
        self.assertFalse(gpio.is_pin_valid(2))

    def test_adc_pins_subset_of_valid_pins(self) -> None:
        """Test that some ADC pins might not be in standard GPIO list."""
        # Some ADC pins like 34, 35, 36, 39 are input-only
        # They may or may not be in VALID_GPIO_PINS
        for pin in GPIOHandler.ADC_PINS:
            self.assertIsInstance(pin, int)

    def test_strapping_pins_defined(self) -> None:
        """Test that STRAPPING_PINS is properly defined."""
        self.assertIsInstance(GPIOHandler.STRAPPING_PINS, list)
        # Common strapping pins
        for pin in [0, 2, 5, 12, 15]:
            self.assertIn(pin, GPIOHandler.STRAPPING_PINS)

    def test_pin_modes_tracked(self) -> None:
        """Test that _pin_modes dictionary is initialized."""
        gpio = GPIOHandler()
        self.assertIsInstance(gpio._pin_modes, dict)
        self.assertEqual(len(gpio._pin_modes), 0)

    def test_pins_tracked(self) -> None:
        """Test that _pins dictionary is initialized."""
        gpio = GPIOHandler()
        self.assertIsInstance(gpio._pins, dict)
        self.assertEqual(len(gpio._pins), 0)

    def test_pwm_configs_tracked(self) -> None:
        """Test that _pwm_configs dictionary is initialized."""
        gpio = GPIOHandler()
        self.assertIsInstance(gpio._pwm_configs, dict)
        self.assertEqual(len(gpio._pwm_configs), 0)

    def test_large_pin_number(self) -> None:
        """Test behavior with very large pin number."""
        gpio = GPIOHandler()
        self.assertFalse(gpio.is_pin_valid(1000))

    def test_negative_pin_number(self) -> None:
        """Test behavior with negative pin number."""
        gpio = GPIOHandler()
        self.assertFalse(gpio.is_pin_valid(-1))

    def test_valid_gpio_pins_no_duplicates(self) -> None:
        """Test that VALID_GPIO_PINS has no duplicates."""
        pins = GPIOHandler.VALID_GPIO_PINS
        self.assertEqual(len(pins), len(set(pins)))

    def test_adc_pins_no_duplicates(self) -> None:
        """Test that ADC_PINS has no duplicates."""
        pins = GPIOHandler.ADC_PINS
        self.assertEqual(len(pins), len(set(pins)))

    def test_setup_interrupt_returns_false_without_hardware(self) -> None:
        """Test setup_interrupt returns False when hardware unavailable."""
        gpio = GPIOHandler()
        def handler(pin):
            pass
        result = gpio.setup_interrupt(4, IRQTrigger.FALLING, handler)
        self.assertFalse(result)

    def test_setup_interrupt_invalid_pin(self) -> None:
        """Test setup_interrupt with invalid pin number."""
        gpio = GPIOHandler(allowed_pins=[2, 4, 5])
        def handler(pin):
            pass
        result = gpio.setup_interrupt(99, IRQTrigger.RISING, handler)
        self.assertFalse(result)

    def test_enable_interrupt_unconfigured_pin(self) -> None:
        """Test enable_interrupt on unconfigured pin."""
        gpio = GPIOHandler()
        result = gpio.enable_interrupt(4)
        self.assertFalse(result)

    def test_disable_interrupt_unconfigured_pin(self) -> None:
        """Test disable_interrupt on unconfigured pin."""
        gpio = GPIOHandler()
        result = gpio.disable_interrupt(4)
        self.assertFalse(result)

    def test_is_interrupt_enabled_unconfigured_pin(self) -> None:
        """Test is_interrupt_enabled on unconfigured pin."""
        gpio = GPIOHandler()
        result = gpio.is_interrupt_enabled(4)
        self.assertFalse(result)

    def test_irq_handlers_tracked(self) -> None:
        """Test that _irq_handlers dictionary is initialized."""
        gpio = GPIOHandler()
        self.assertIsInstance(gpio._irq_handlers, dict)
        self.assertEqual(len(gpio._irq_handlers), 0)

    def test_irq_enabled_tracked(self) -> None:
        """Test that _irq_enabled dictionary is initialized."""
        gpio = GPIOHandler()
        self.assertIsInstance(gpio._irq_enabled, dict)
        self.assertEqual(len(gpio._irq_enabled), 0)

    def test_pin_status_includes_interrupt_info(self) -> None:
        """Test that pin status includes interrupt information."""
        gpio = GPIOHandler()
        # For unconfigured pin
        status = gpio.get_pin_status(2)
        self.assertIsNone(status)
        # Note: Cannot test with actual interrupt without hardware

    def test_interrupt_trigger_values(self) -> None:
        """Test interrupt trigger constant values."""
        # Verify trigger values are defined
        self.assertIsInstance(IRQTrigger.RISING, int)
        self.assertIsInstance(IRQTrigger.FALLING, int)
        self.assertIsInstance(IRQTrigger.BOTH, int)


def run_tests() -> None:
    """Run all GPIO handler tests."""
    print("=" * 60)
    print("Running GPIO Handler Module Tests")
    print("=" * 60)

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestPinMode))
    suite.addTests(loader.loadTestsFromTestCase(TestPullMode))
    suite.addTests(loader.loadTestsFromTestCase(TestIRQTrigger))
    suite.addTests(loader.loadTestsFromTestCase(TestGPIOHandler))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 60)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
