"""Configuration management module.

This module provides JSON-based configuration management with support for
nested keys using dot notation and automatic file saving.
"""

import json
from typing import Dict, Any, Optional

__all__ = ['Config']


class Config:
    """Manage JSON configuration files.

    Supports reading and writing JSON configuration files with convenient
    dot-notation access to nested values.

    Example:
        >>> config = Config('config.json')
        >>> ssid = config.get('wifi.ssid', 'default_network')
        >>> config.set('wifi.password', 'secret123')
        >>> config.save()
    """

    def __init__(self, filename: str = 'config.json') -> None:
        """Initialize config manager.

        Args:
            filename: Configuration file path (relative or absolute)
        """
        self.filename = filename
        self._data: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """Load configuration from file.

        If the file doesn't exist, initializes with empty configuration.
        Prints a message if file is not found but doesn't raise an error.
        """
        try:
            with open(self.filename, 'r') as f:
                self._data = json.load(f)
        except OSError:
            print(f"Config file {self.filename} not found, using defaults")
            self._data = {}
        except ValueError as e:
            print(f"Error parsing config file {self.filename}: {e}")
            self._data = {}

    def save(self) -> None:
        """Save configuration to file.

        Writes the current configuration to the JSON file.

        Raises:
            OSError: If file cannot be written
        """
        with open(self.filename, 'w') as f:
            json.dump(self._data, f)

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value.

        Supports dot notation for nested values, e.g., 'wifi.ssid' will
        access data['wifi']['ssid'].

        Args:
            key: Configuration key (supports dot notation: 'wifi.ssid')
            default: Default value if key not found

        Returns:
            Configuration value or default if not found

        Example:
            >>> config.get('wifi.ssid', 'default')
            'my_network'
            >>> config.get('nonexistent.key', 'fallback')
            'fallback'
        """
        keys = key.split('.')
        value = self._data

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """Set configuration value.

        Supports dot notation for nested values. Creates intermediate
        dictionaries as needed.

        Args:
            key: Configuration key (supports dot notation)
            value: Value to set

        Example:
            >>> config.set('wifi.ssid', 'my_network')
            >>> config.set('wifi.password', 'secret')
            >>> config.set('server.port', 80)
        """
        keys = key.split('.')

        # Navigate to the parent dictionary, creating as needed
        current = self._data
        for k in keys[:-1]:
            if k not in current or not isinstance(current[k], dict):
                current[k] = {}
            current = current[k]

        # Set the final value
        current[keys[-1]] = value

    def get_all(self) -> Dict[str, Any]:
        """Get entire configuration dictionary.

        Returns:
            Complete configuration dictionary
        """
        return self._data.copy()

    def has(self, key: str) -> bool:
        """Check if configuration key exists.

        Args:
            key: Configuration key (supports dot notation)

        Returns:
            True if key exists, False otherwise
        """
        keys = key.split('.')
        value = self._data

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return False

        return True

    def delete(self, key: str) -> bool:
        """Delete configuration key.

        Args:
            key: Configuration key (supports dot notation)

        Returns:
            True if key was deleted, False if key didn't exist
        """
        keys = key.split('.')

        # Navigate to parent
        current = self._data
        for k in keys[:-1]:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return False

        # Delete the final key
        if isinstance(current, dict) and keys[-1] in current:
            del current[keys[-1]]
            return True

        return False

    def clear(self) -> None:
        """Clear all configuration data."""
        self._data = {}
