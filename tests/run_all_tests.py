"""Master test runner for ESP32 IO Bridge WiFi.

This script runs all unit tests for the project and provides a comprehensive
test report. Can be run on both development machine and on the ESP32 device.
"""

import unittest
import sys
import time
import os
from typing import List, Tuple

# Add project root and lib to path for testing
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'lib'))
sys.path.append('/lib')  # For MicroPython on device
sys.path.append('lib')

# Import test modules
from test_logger import TestLogLevel, TestLogger
from test_config import TestConfig
from test_wifi_station import TestWiFiStatus, TestWiFiStation
from test_gpio_handler import TestPinMode, TestPullMode, TestIRQTrigger, TestGPIOHandler


def print_banner(message: str) -> None:
    """Print a formatted banner message.

    Args:
        message: Message to display in banner
    """
    width = 70
    print("\n" + "=" * width)
    print(message.center(width))
    print("=" * width + "\n")


def run_all_tests() -> Tuple[int, int, int]:
    """Run all test suites.

    Returns:
        Tuple of (total_tests, failures, errors)
    """
    print_banner("ESP32 IO Bridge WiFi - Comprehensive Test Suite")

    # Create master test suite
    loader = unittest.TestLoader()
    master_suite = unittest.TestSuite()

    # Test suites to run
    test_classes = [
        ('Logger Module - LogLevel', TestLogLevel),
        ('Logger Module - Logger', TestLogger),
        ('Config Module', TestConfig),
        ('WiFi Module - WiFiStatus', TestWiFiStatus),
        ('WiFi Module - WiFiStation', TestWiFiStation),
        ('GPIO Module - PinMode', TestPinMode),
        ('GPIO Module - PullMode', TestPullMode),
        ('GPIO Module - IRQTrigger', TestIRQTrigger),
        ('GPIO Module - GPIOHandler', TestGPIOHandler),
    ]

    print("Test Modules:")
    for name, test_class in test_classes:
        suite = loader.loadTestsFromTestCase(test_class)
        master_suite.addTests(suite)
        print(f"  ✓ {name} ({suite.countTestCases()} tests)")

    print("\n" + "-" * 70)

    # Run all tests
    start_time = time.time()
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(master_suite)
    end_time = time.time()

    # Print detailed summary
    print_banner("Test Results Summary")

    print(f"Total Tests Run:  {result.testsRun}")
    print(f"Successes:        {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures:         {len(result.failures)}")
    print(f"Errors:           {len(result.errors)}")
    print(f"Execution Time:   {end_time - start_time:.2f} seconds")

    # Print failure details if any
    if result.failures:
        print("\n" + "!" * 70)
        print("FAILURES:")
        print("!" * 70)
        for test, traceback in result.failures:
            print(f"\n{test}:")
            print(traceback)

    # Print error details if any
    if result.errors:
        print("\n" + "!" * 70)
        print("ERRORS:")
        print("!" * 70)
        for test, traceback in result.errors:
            print(f"\n{test}:")
            print(traceback)

    # Final result
    if result.wasSuccessful():
        print_banner("✓ ALL TESTS PASSED!")
        return (result.testsRun, 0, 0)
    else:
        print_banner("✗ SOME TESTS FAILED")
        return (result.testsRun, len(result.failures), len(result.errors))


def main() -> int:
    """Main entry point for test runner.

    Returns:
        Exit code (0 for success, 1 for failures)
    """
    try:
        tests_run, failures, errors = run_all_tests()

        # Return appropriate exit code
        if failures == 0 and errors == 0:
            return 0
        else:
            return 1

    except Exception as e:
        print("\n" + "!" * 70)
        print("FATAL ERROR RUNNING TESTS:")
        print("!" * 70)
        print(f"{type(e).__name__}: {e}")
        sys.print_exception(e) if hasattr(sys, 'print_exception') else None
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
