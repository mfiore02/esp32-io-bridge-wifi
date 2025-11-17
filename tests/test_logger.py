"""Unit tests for the logger module.

Tests the Logger and LogLevel classes to ensure proper logging functionality,
level filtering, and message formatting.
"""

import unittest
import sys
import io
import os
from typing import List

# Add project root and lib to path for testing
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'lib'))
sys.path.append('/lib')  # For MicroPython on device
sys.path.append('lib')

from lib.utils.logger import Logger, LogLevel


class TestLogLevel(unittest.TestCase):
    """Test LogLevel constants."""

    def test_log_level_values(self) -> None:
        """Test that log levels have correct numeric values."""
        self.assertEqual(LogLevel.DEBUG, 0)
        self.assertEqual(LogLevel.INFO, 1)
        self.assertEqual(LogLevel.WARNING, 2)
        self.assertEqual(LogLevel.ERROR, 3)
        self.assertEqual(LogLevel.CRITICAL, 4)

    def test_log_level_ordering(self) -> None:
        """Test that log levels are properly ordered."""
        self.assertLess(LogLevel.DEBUG, LogLevel.INFO)
        self.assertLess(LogLevel.INFO, LogLevel.WARNING)
        self.assertLess(LogLevel.WARNING, LogLevel.ERROR)
        self.assertLess(LogLevel.ERROR, LogLevel.CRITICAL)


class TestLogger(unittest.TestCase):
    """Test Logger class functionality."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        # Reset global level to default
        Logger.set_global_level(LogLevel.INFO)
        # Create a logger for testing
        self.logger = Logger('TestLogger', LogLevel.DEBUG)

    def tearDown(self) -> None:
        """Clean up after tests."""
        # Reset to default
        Logger.set_global_level(LogLevel.INFO)

    def test_logger_initialization(self) -> None:
        """Test logger initialization with name and level."""
        logger = Logger('TestName', LogLevel.WARNING)
        self.assertEqual(logger.name, 'TestName')
        self.assertEqual(logger.level, LogLevel.WARNING)

    def test_logger_default_level(self) -> None:
        """Test logger uses global level when no level specified."""
        Logger.set_global_level(LogLevel.ERROR)
        logger = Logger('Test')
        self.assertEqual(logger.level, LogLevel.ERROR)

    def test_set_level(self) -> None:
        """Test setting logger level."""
        logger = Logger('Test', LogLevel.INFO)
        logger.set_level(LogLevel.ERROR)
        self.assertEqual(logger.level, LogLevel.ERROR)

    def test_set_global_level(self) -> None:
        """Test setting global log level."""
        Logger.set_global_level(LogLevel.WARNING)
        self.assertEqual(Logger.global_level, LogLevel.WARNING)

        # New loggers should use global level
        logger = Logger('Test')
        self.assertEqual(logger.level, LogLevel.WARNING)

    def test_debug_message(self) -> None:
        """Test debug logging."""
        # Capture output
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()

        try:
            logger = Logger('DebugTest', LogLevel.DEBUG)
            logger.debug("Debug message")
            output = sys.stdout.getvalue()

            self.assertIn('DEBUG', output)
            self.assertIn('DebugTest', output)
            self.assertIn('Debug message', output)
        finally:
            sys.stdout = old_stdout

    def test_info_message(self) -> None:
        """Test info logging."""
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()

        try:
            logger = Logger('InfoTest', LogLevel.INFO)
            logger.info("Info message")
            output = sys.stdout.getvalue()

            self.assertIn('INFO', output)
            self.assertIn('InfoTest', output)
            self.assertIn('Info message', output)
        finally:
            sys.stdout = old_stdout

    def test_warning_message(self) -> None:
        """Test warning logging."""
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()

        try:
            logger = Logger('WarnTest', LogLevel.WARNING)
            logger.warning("Warning message")
            output = sys.stdout.getvalue()

            self.assertIn('WARNING', output)
            self.assertIn('WarnTest', output)
            self.assertIn('Warning message', output)
        finally:
            sys.stdout = old_stdout

    def test_error_message(self) -> None:
        """Test error logging."""
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()

        try:
            logger = Logger('ErrorTest', LogLevel.ERROR)
            logger.error("Error message")
            output = sys.stdout.getvalue()

            self.assertIn('ERROR', output)
            self.assertIn('ErrorTest', output)
            self.assertIn('Error message', output)
        finally:
            sys.stdout = old_stdout

    def test_critical_message(self) -> None:
        """Test critical logging."""
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()

        try:
            logger = Logger('CriticalTest', LogLevel.CRITICAL)
            logger.critical("Critical message")
            output = sys.stdout.getvalue()

            self.assertIn('CRITICAL', output)
            self.assertIn('CriticalTest', output)
            self.assertIn('Critical message', output)
        finally:
            sys.stdout = old_stdout

    def test_level_filtering_blocks_lower_levels(self) -> None:
        """Test that messages below log level are not printed."""
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()

        try:
            # Set level to WARNING
            logger = Logger('FilterTest', LogLevel.WARNING)

            # These should NOT appear
            logger.debug("Debug message")
            logger.info("Info message")

            # This SHOULD appear
            logger.warning("Warning message")

            output = sys.stdout.getvalue()

            # Debug and Info should not be in output
            self.assertNotIn('Debug message', output)
            self.assertNotIn('Info message', output)
            self.assertNotIn('DEBUG', output)
            self.assertNotIn('INFO', output)

            # Warning should be in output
            self.assertIn('Warning message', output)
            self.assertIn('WARNING', output)
        finally:
            sys.stdout = old_stdout

    def test_level_filtering_allows_higher_levels(self) -> None:
        """Test that messages at or above log level are printed."""
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()

        try:
            # Set level to INFO
            logger = Logger('FilterTest', LogLevel.INFO)

            # These should all appear
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")
            logger.critical("Critical message")

            output = sys.stdout.getvalue()

            # All should be in output
            self.assertIn('Info message', output)
            self.assertIn('Warning message', output)
            self.assertIn('Error message', output)
            self.assertIn('Critical message', output)
        finally:
            sys.stdout = old_stdout

    def test_message_format_includes_timestamp(self) -> None:
        """Test that log messages include a timestamp."""
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()

        try:
            logger = Logger('TimeTest', LogLevel.INFO)
            logger.info("Test message")
            output = sys.stdout.getvalue()

            # Should start with [timestamp]
            self.assertTrue(output.startswith('['))
            self.assertIn(']', output)
        finally:
            sys.stdout = old_stdout

    def test_multiple_loggers_independent(self) -> None:
        """Test that multiple loggers operate independently."""
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()

        try:
            logger1 = Logger('Logger1', LogLevel.DEBUG)
            logger2 = Logger('Logger2', LogLevel.ERROR)

            logger1.debug("Debug from logger1")
            logger2.debug("Debug from logger2")  # Should not appear
            logger2.error("Error from logger2")

            output = sys.stdout.getvalue()

            # Logger1 debug should appear
            self.assertIn('Logger1', output)
            self.assertIn('Debug from logger1', output)

            # Logger2 debug should NOT appear
            self.assertNotIn('Debug from logger2', output)

            # Logger2 error should appear
            self.assertIn('Error from logger2', output)
        finally:
            sys.stdout = old_stdout

    def test_special_characters_in_message(self) -> None:
        """Test logging messages with special characters."""
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()

        try:
            logger = Logger('SpecialTest', LogLevel.INFO)
            logger.info("Message with: colons, commas, and 'quotes'")
            output = sys.stdout.getvalue()

            self.assertIn("Message with: colons, commas, and 'quotes'", output)
        finally:
            sys.stdout = old_stdout

    def test_empty_message(self) -> None:
        """Test logging empty message."""
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()

        try:
            logger = Logger('EmptyTest', LogLevel.INFO)
            logger.info("")
            output = sys.stdout.getvalue()

            # Should still have the log format, just empty message
            self.assertIn('INFO', output)
            self.assertIn('EmptyTest', output)
        finally:
            sys.stdout = old_stdout

    def test_long_message(self) -> None:
        """Test logging very long message."""
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()

        try:
            logger = Logger('LongTest', LogLevel.INFO)
            long_msg = "A" * 500
            logger.info(long_msg)
            output = sys.stdout.getvalue()

            self.assertIn(long_msg, output)
        finally:
            sys.stdout = old_stdout


def run_tests() -> None:
    """Run all logger tests."""
    print("=" * 60)
    print("Running Logger Module Tests")
    print("=" * 60)

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestLogLevel))
    suite.addTests(loader.loadTestsFromTestCase(TestLogger))

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
