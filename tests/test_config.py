"""Unit tests for the config module.

Tests the Config class to ensure proper JSON configuration management,
dot-notation access, file I/O, and edge case handling.
"""

import unittest
import sys
import os
import json
from typing import Dict, Any

# Add project root and lib to path for testing
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'lib'))
sys.path.append('/lib')  # For MicroPython on device
sys.path.append('lib')

from lib.utils.config import Config


class TestConfig(unittest.TestCase):
    """Test Config class functionality."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.test_file = 'test_config.json'
        self.test_data: Dict[str, Any] = {
            'string_value': 'test',
            'int_value': 42,
            'bool_value': True,
            'nested': {
                'level1': {
                    'level2': 'deep_value'
                },
                'array': [1, 2, 3]
            }
        }

    def tearDown(self) -> None:
        """Clean up test files."""
        try:
            os.remove(self.test_file)
        except OSError:
            pass

    def _create_test_file(self, data: Dict[str, Any]) -> None:
        """Helper to create a test config file."""
        with open(self.test_file, 'w') as f:
            json.dump(data, f)

    def test_initialization_with_nonexistent_file(self) -> None:
        """Test initialization when config file doesn't exist."""
        config = Config('nonexistent_file.json')
        self.assertEqual(config.filename, 'nonexistent_file.json')
        self.assertEqual(config._data, {})

    def test_initialization_with_existing_file(self) -> None:
        """Test initialization with existing config file."""
        self._create_test_file(self.test_data)
        config = Config(self.test_file)
        self.assertEqual(config._data, self.test_data)

    def test_load_valid_json(self) -> None:
        """Test loading valid JSON configuration."""
        self._create_test_file(self.test_data)
        config = Config(self.test_file)
        config.load()
        self.assertEqual(config._data['string_value'], 'test')
        self.assertEqual(config._data['int_value'], 42)

    def test_load_invalid_json(self) -> None:
        """Test loading invalid JSON file."""
        # Create invalid JSON file
        with open(self.test_file, 'w') as f:
            f.write('{ invalid json content }')

        config = Config(self.test_file)
        # Should initialize with empty dict on error
        self.assertEqual(config._data, {})

    def test_save_configuration(self) -> None:
        """Test saving configuration to file."""
        config = Config(self.test_file)
        config._data = self.test_data
        config.save()

        # Read the file and verify
        with open(self.test_file, 'r') as f:
            loaded_data = json.load(f)
        self.assertEqual(loaded_data, self.test_data)

    def test_get_simple_key(self) -> None:
        """Test getting simple key value."""
        config = Config(self.test_file)
        config._data = self.test_data
        self.assertEqual(config.get('string_value'), 'test')
        self.assertEqual(config.get('int_value'), 42)
        self.assertEqual(config.get('bool_value'), True)

    def test_get_nested_key_with_dot_notation(self) -> None:
        """Test getting nested values with dot notation."""
        config = Config(self.test_file)
        config._data = self.test_data
        self.assertEqual(config.get('nested.level1.level2'), 'deep_value')

    def test_get_array_value(self) -> None:
        """Test getting array value."""
        config = Config(self.test_file)
        config._data = self.test_data
        array = config.get('nested.array')
        self.assertEqual(array, [1, 2, 3])

    def test_get_nonexistent_key_returns_default(self) -> None:
        """Test that nonexistent key returns default value."""
        config = Config(self.test_file)
        config._data = self.test_data
        self.assertEqual(config.get('nonexistent', 'default'), 'default')
        self.assertIsNone(config.get('nonexistent'))

    def test_get_nonexistent_nested_key_returns_default(self) -> None:
        """Test that nonexistent nested key returns default."""
        config = Config(self.test_file)
        config._data = self.test_data
        self.assertEqual(
            config.get('nested.nonexistent.key', 'default'),
            'default'
        )

    def test_get_with_none_default(self) -> None:
        """Test get with None as default value."""
        config = Config(self.test_file)
        config._data = {}
        result = config.get('key', None)
        self.assertIsNone(result)

    def test_set_simple_key(self) -> None:
        """Test setting simple key value."""
        config = Config(self.test_file)
        config.set('new_key', 'new_value')
        self.assertEqual(config._data['new_key'], 'new_value')

    def test_set_nested_key_with_dot_notation(self) -> None:
        """Test setting nested values with dot notation."""
        config = Config(self.test_file)
        config.set('level1.level2.level3', 'nested_value')
        self.assertEqual(
            config._data['level1']['level2']['level3'],
            'nested_value'
        )

    def test_set_creates_intermediate_dicts(self) -> None:
        """Test that set creates intermediate dictionaries."""
        config = Config(self.test_file)
        config.set('a.b.c.d', 'value')
        self.assertIsInstance(config._data['a'], dict)
        self.assertIsInstance(config._data['a']['b'], dict)
        self.assertIsInstance(config._data['a']['b']['c'], dict)
        self.assertEqual(config._data['a']['b']['c']['d'], 'value')

    def test_set_overwrites_existing_value(self) -> None:
        """Test that set overwrites existing values."""
        config = Config(self.test_file)
        config._data = self.test_data
        config.set('string_value', 'new_value')
        self.assertEqual(config._data['string_value'], 'new_value')

    def test_set_different_types(self) -> None:
        """Test setting different data types."""
        config = Config(self.test_file)
        config.set('string', 'text')
        config.set('integer', 123)
        config.set('float', 3.14)
        config.set('boolean', True)
        config.set('null', None)
        config.set('list', [1, 2, 3])
        config.set('dict', {'key': 'value'})

        self.assertEqual(config._data['string'], 'text')
        self.assertEqual(config._data['integer'], 123)
        self.assertEqual(config._data['float'], 3.14)
        self.assertEqual(config._data['boolean'], True)
        self.assertIsNone(config._data['null'])
        self.assertEqual(config._data['list'], [1, 2, 3])
        self.assertEqual(config._data['dict'], {'key': 'value'})

    def test_get_all(self) -> None:
        """Test getting entire configuration dictionary."""
        config = Config(self.test_file)
        config._data = self.test_data
        all_data = config.get_all()
        self.assertEqual(all_data, self.test_data)

    def test_get_all_returns_copy(self) -> None:
        """Test that get_all returns a copy, not reference."""
        config = Config(self.test_file)
        config._data = {'key': 'value'}
        all_data = config.get_all()
        all_data['key'] = 'modified'
        # Original should be unchanged
        self.assertEqual(config._data['key'], 'value')

    def test_has_existing_key(self) -> None:
        """Test has() with existing keys."""
        config = Config(self.test_file)
        config._data = self.test_data
        self.assertTrue(config.has('string_value'))
        self.assertTrue(config.has('nested.level1.level2'))

    def test_has_nonexistent_key(self) -> None:
        """Test has() with nonexistent keys."""
        config = Config(self.test_file)
        config._data = self.test_data
        self.assertFalse(config.has('nonexistent'))
        self.assertFalse(config.has('nested.nonexistent'))

    def test_has_with_empty_config(self) -> None:
        """Test has() with empty configuration."""
        config = Config(self.test_file)
        self.assertFalse(config.has('any_key'))

    def test_delete_existing_key(self) -> None:
        """Test deleting existing key."""
        config = Config(self.test_file)
        config._data = self.test_data.copy()
        result = config.delete('string_value')
        self.assertTrue(result)
        self.assertNotIn('string_value', config._data)

    def test_delete_nested_key(self) -> None:
        """Test deleting nested key."""
        config = Config(self.test_file)
        config._data = self.test_data.copy()
        result = config.delete('nested.level1.level2')
        self.assertTrue(result)
        self.assertNotIn('level2', config._data['nested']['level1'])

    def test_delete_nonexistent_key(self) -> None:
        """Test deleting nonexistent key."""
        config = Config(self.test_file)
        config._data = self.test_data.copy()
        result = config.delete('nonexistent')
        self.assertFalse(result)

    def test_delete_from_empty_config(self) -> None:
        """Test deleting from empty configuration."""
        config = Config(self.test_file)
        result = config.delete('any_key')
        self.assertFalse(result)

    def test_clear(self) -> None:
        """Test clearing all configuration."""
        config = Config(self.test_file)
        config._data = self.test_data.copy()
        config.clear()
        self.assertEqual(config._data, {})

    def test_clear_empty_config(self) -> None:
        """Test clearing already empty configuration."""
        config = Config(self.test_file)
        config.clear()
        self.assertEqual(config._data, {})

    def test_round_trip_save_and_load(self) -> None:
        """Test saving and loading configuration."""
        # Create and save config
        config1 = Config(self.test_file)
        config1._data = self.test_data
        config1.save()

        # Load in new instance
        config2 = Config(self.test_file)
        self.assertEqual(config2._data, self.test_data)

    def test_modify_and_save(self) -> None:
        """Test modifying configuration and saving."""
        config = Config(self.test_file)
        config.set('key1', 'value1')
        config.set('key2.nested', 'value2')
        config.save()

        # Load and verify
        config2 = Config(self.test_file)
        self.assertEqual(config2.get('key1'), 'value1')
        self.assertEqual(config2.get('key2.nested'), 'value2')

    def test_special_characters_in_keys(self) -> None:
        """Test keys with special characters."""
        config = Config(self.test_file)
        config.set('key-with-dash', 'value')
        config.set('key_with_underscore', 'value')
        self.assertEqual(config.get('key-with-dash'), 'value')
        self.assertEqual(config.get('key_with_underscore'), 'value')

    def test_empty_string_value(self) -> None:
        """Test setting empty string value."""
        config = Config(self.test_file)
        config.set('empty', '')
        self.assertEqual(config.get('empty'), '')

    def test_zero_and_false_values(self) -> None:
        """Test that zero and False are handled correctly."""
        config = Config(self.test_file)
        config.set('zero', 0)
        config.set('false', False)
        self.assertEqual(config.get('zero'), 0)
        self.assertEqual(config.get('false'), False)
        # These should not be confused with "not set"
        self.assertTrue(config.has('zero'))
        self.assertTrue(config.has('false'))

    def test_unicode_values(self) -> None:
        """Test Unicode string values."""
        config = Config(self.test_file)
        config.set('unicode', 'Hello 世界 🌍')
        config.save()

        config2 = Config(self.test_file)
        self.assertEqual(config2.get('unicode'), 'Hello 世界 🌍')

    def test_large_nested_structure(self) -> None:
        """Test with large nested structure."""
        config = Config(self.test_file)
        config.set('a.b.c.d.e.f.g.h.i.j', 'deep')
        self.assertEqual(config.get('a.b.c.d.e.f.g.h.i.j'), 'deep')

    def test_dot_notation_with_single_level(self) -> None:
        """Test dot notation access with single level keys."""
        config = Config(self.test_file)
        config._data = {'simple': 'value'}
        self.assertEqual(config.get('simple'), 'value')


def run_tests() -> None:
    """Run all config tests."""
    print("=" * 60)
    print("Running Config Module Tests")
    print("=" * 60)

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestConfig))

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
