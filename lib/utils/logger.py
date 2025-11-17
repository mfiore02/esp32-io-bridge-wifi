"""Logging utility for MicroPython.

This module provides a simple but effective logging system for MicroPython
applications running on ESP32. It supports multiple log levels and timestamps.
"""

from typing import Optional
import time

__all__ = ['Logger', 'LogLevel']


class LogLevel:
    """Log level constants."""
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4


class Logger:
    """Simple logger for MicroPython.

    Provides formatted logging with timestamps and log levels. Useful for
    debugging and monitoring application behavior on the device.

    Example:
        >>> logger = Logger('WiFi', LogLevel.INFO)
        >>> logger.info("Connected to network")
        [1234567890] INFO - WiFi: Connected to network
        >>> logger.error("Connection failed")
        [1234567890] ERROR - WiFi: Connection failed
    """

    # Class-level minimum log level (can be set globally)
    global_level: int = LogLevel.INFO

    def __init__(self, name: str, level: Optional[int] = None) -> None:
        """Initialize logger.

        Args:
            name: Logger name (typically module name or component name)
            level: Minimum log level to display. If None, uses global_level
        """
        self.name = name
        self.level = level if level is not None else Logger.global_level

    def _log(self, level: int, level_name: str, message: str) -> None:
        """Internal logging method.

        Args:
            level: Numeric log level
            level_name: String representation of log level
            message: Log message
        """
        if level >= self.level:
            timestamp = time.time()
            print(f"[{timestamp:.0f}] {level_name} - {self.name}: {message}")

    def debug(self, message: str) -> None:
        """Log debug message.

        Args:
            message: Debug message to log
        """
        self._log(LogLevel.DEBUG, "DEBUG", message)

    def info(self, message: str) -> None:
        """Log info message.

        Args:
            message: Info message to log
        """
        self._log(LogLevel.INFO, "INFO", message)

    def warning(self, message: str) -> None:
        """Log warning message.

        Args:
            message: Warning message to log
        """
        self._log(LogLevel.WARNING, "WARNING", message)

    def error(self, message: str) -> None:
        """Log error message.

        Args:
            message: Error message to log
        """
        self._log(LogLevel.ERROR, "ERROR", message)

    def critical(self, message: str) -> None:
        """Log critical message.

        Args:
            message: Critical message to log
        """
        self._log(LogLevel.CRITICAL, "CRITICAL", message)

    def set_level(self, level: int) -> None:
        """Set minimum log level for this logger.

        Args:
            level: New minimum log level
        """
        self.level = level

    @classmethod
    def set_global_level(cls, level: int) -> None:
        """Set global minimum log level for all loggers.

        Args:
            level: New global minimum log level
        """
        cls.global_level = level
