"""Unit tests for the WiFi station module.

Tests the WiFiStation and WiFiStatus classes to ensure proper WiFi
connectivity, status management, and auto-reconnect functionality.

Note: These tests validate the API and logic. Full network testing
requires actual ESP32 hardware.
"""

import unittest
import sys
import os
from typing import Optional
from unittest.mock import Mock, MagicMock, patch

# Add project root and lib to path for testing
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'lib'))
sys.path.append('/lib')  # For MicroPython on device
sys.path.append('lib')

from lib.wifi.station import WiFiStation, WiFiStatus


class TestWiFiStatus(unittest.TestCase):
    """Test WiFiStatus constants."""

    def test_status_values(self) -> None:
        """Test that status constants have correct values."""
        self.assertEqual(WiFiStatus.IDLE, 0)
        self.assertEqual(WiFiStatus.CONNECTING, 1)
        self.assertEqual(WiFiStatus.CONNECTED, 2)
        self.assertEqual(WiFiStatus.FAILED, 3)
        self.assertEqual(WiFiStatus.DISCONNECTED, 4)
        self.assertEqual(WiFiStatus.NO_AP_FOUND, 5)
        self.assertEqual(WiFiStatus.WRONG_PASSWORD, 6)

    def test_status_ordering(self) -> None:
        """Test that status constants are properly ordered."""
        self.assertLess(WiFiStatus.IDLE, WiFiStatus.CONNECTING)
        self.assertLess(WiFiStatus.CONNECTING, WiFiStatus.CONNECTED)


class TestWiFiStation(unittest.TestCase):
    """Test WiFiStation class functionality."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        # WiFiStation will initialize with None _sta when network module unavailable
        self.ssid = 'TestNetwork'
        self.password = 'TestPassword123'

    def test_initialization_basic(self) -> None:
        """Test basic WiFi station initialization."""
        wifi = WiFiStation(self.ssid, self.password)
        self.assertEqual(wifi.ssid, self.ssid)
        self.assertEqual(wifi.password, self.password)
        self.assertTrue(wifi.auto_reconnect)
        self.assertEqual(wifi.max_retries, 3)

    def test_initialization_with_custom_params(self) -> None:
        """Test initialization with custom parameters."""
        wifi = WiFiStation(
            self.ssid,
            self.password,
            auto_reconnect=False,
            max_retries=5,
            retry_delay=10
        )
        self.assertEqual(wifi.ssid, self.ssid)
        self.assertEqual(wifi.password, self.password)
        self.assertFalse(wifi.auto_reconnect)
        self.assertEqual(wifi.max_retries, 5)
        self.assertEqual(wifi.retry_delay, 10)

    def test_initial_status_is_idle(self) -> None:
        """Test that initial status is IDLE."""
        wifi = WiFiStation(self.ssid, self.password)
        self.assertEqual(wifi._status, WiFiStatus.IDLE)

    def test_get_status_structure(self) -> None:
        """Test get_status returns proper structure."""
        wifi = WiFiStation(self.ssid, self.password)
        status = wifi.get_status()

        # Check all expected keys are present
        expected_keys = [
            'connected', 'status', 'status_name', 'ssid',
            'ip', 'netmask', 'gateway', 'dns', 'rssi', 'mac',
            'retry_count', 'last_error'
        ]

        for key in expected_keys:
            self.assertIn(key, status)

    def test_get_status_values_when_not_connected(self) -> None:
        """Test status values when not connected."""
        wifi = WiFiStation(self.ssid, self.password)
        status = wifi.get_status()

        self.assertFalse(status['connected'])
        self.assertEqual(status['status'], WiFiStatus.IDLE)
        self.assertEqual(status['ssid'], self.ssid)
        self.assertIsNone(status['ip'])
        self.assertIsNone(status['rssi'])
        self.assertEqual(status['retry_count'], 0)

    def test_status_name_mapping(self) -> None:
        """Test status name mapping."""
        wifi = WiFiStation(self.ssid, self.password)

        # Test all status names
        self.assertEqual(wifi._get_status_name(WiFiStatus.IDLE), 'IDLE')
        self.assertEqual(wifi._get_status_name(WiFiStatus.CONNECTING), 'CONNECTING')
        self.assertEqual(wifi._get_status_name(WiFiStatus.CONNECTED), 'CONNECTED')
        self.assertEqual(wifi._get_status_name(WiFiStatus.FAILED), 'FAILED')
        self.assertEqual(wifi._get_status_name(WiFiStatus.DISCONNECTED), 'DISCONNECTED')
        self.assertEqual(wifi._get_status_name(WiFiStatus.NO_AP_FOUND), 'NO_AP_FOUND')
        self.assertEqual(wifi._get_status_name(WiFiStatus.WRONG_PASSWORD), 'WRONG_PASSWORD')
        self.assertEqual(wifi._get_status_name(999), 'UNKNOWN')

    def test_get_error_initial(self) -> None:
        """Test that get_error returns None initially."""
        wifi = WiFiStation(self.ssid, self.password)
        self.assertIsNone(wifi.get_error())

    def test_is_connected_when_sta_none(self) -> None:
        """Test is_connected returns False when no hardware available."""
        wifi = WiFiStation(self.ssid, self.password)
        # When network module is unavailable, _sta is None
        self.assertFalse(wifi.is_connected())

    def test_get_ip_when_sta_none(self) -> None:
        """Test get_ip returns None when no hardware available."""
        wifi = WiFiStation(self.ssid, self.password)
        self.assertIsNone(wifi.get_ip())

    def test_get_netmask_when_sta_none(self) -> None:
        """Test get_netmask returns None when no hardware available."""
        wifi = WiFiStation(self.ssid, self.password)
        self.assertIsNone(wifi.get_netmask())

    def test_get_gateway_when_sta_none(self) -> None:
        """Test get_gateway returns None when no hardware available."""
        wifi = WiFiStation(self.ssid, self.password)
        self.assertIsNone(wifi.get_gateway())

    def test_get_dns_when_sta_none(self) -> None:
        """Test get_dns returns None when no hardware available."""
        wifi = WiFiStation(self.ssid, self.password)
        self.assertIsNone(wifi.get_dns())

    def test_get_rssi_when_sta_none(self) -> None:
        """Test get_rssi returns None when no hardware available."""
        wifi = WiFiStation(self.ssid, self.password)
        self.assertIsNone(wifi.get_rssi())

    def test_get_mac_when_sta_none(self) -> None:
        """Test get_mac returns None when no hardware available."""
        wifi = WiFiStation(self.ssid, self.password)
        self.assertIsNone(wifi.get_mac())

    def test_scan_networks_when_sta_none(self) -> None:
        """Test scan_networks returns empty list when no hardware."""
        wifi = WiFiStation(self.ssid, self.password)
        networks = wifi.scan_networks()
        self.assertEqual(networks, [])

    def test_disconnect_when_sta_none(self) -> None:
        """Test disconnect doesn't crash when no hardware."""
        wifi = WiFiStation(self.ssid, self.password)
        wifi.disconnect()  # Should not raise exception
        self.assertEqual(wifi._status, WiFiStatus.DISCONNECTED)

    def test_connect_fails_when_no_hardware(self) -> None:
        """Test connect returns False when hardware unavailable."""
        wifi = WiFiStation(self.ssid, self.password)
        result = wifi.connect()
        self.assertFalse(result)
        self.assertEqual(wifi._status, WiFiStatus.FAILED)
        self.assertIsNotNone(wifi.get_error())
        self.assertIn('not available', wifi.get_error())

    def test_check_connection_when_not_connected(self) -> None:
        """Test check_connection behavior when not connected."""
        wifi = WiFiStation(self.ssid, self.password, auto_reconnect=False)
        result = wifi.check_connection()
        self.assertFalse(result)

    def test_ssid_stored_correctly(self) -> None:
        """Test that SSID is stored correctly."""
        test_ssid = "MyCustomNetwork"
        wifi = WiFiStation(test_ssid, self.password)
        self.assertEqual(wifi.ssid, test_ssid)

    def test_password_stored_correctly(self) -> None:
        """Test that password is stored correctly."""
        test_password = "SecurePassword456!"
        wifi = WiFiStation(self.ssid, test_password)
        self.assertEqual(wifi.password, test_password)

    def test_empty_ssid(self) -> None:
        """Test initialization with empty SSID."""
        wifi = WiFiStation('', self.password)
        self.assertEqual(wifi.ssid, '')

    def test_empty_password(self) -> None:
        """Test initialization with empty password (open network)."""
        wifi = WiFiStation(self.ssid, '')
        self.assertEqual(wifi.password, '')

    def test_retry_count_initial(self) -> None:
        """Test that retry count is initially zero."""
        wifi = WiFiStation(self.ssid, self.password)
        status = wifi.get_status()
        self.assertEqual(status['retry_count'], 0)

    def test_auto_reconnect_default_true(self) -> None:
        """Test that auto_reconnect defaults to True."""
        wifi = WiFiStation(self.ssid, self.password)
        self.assertTrue(wifi.auto_reconnect)

    def test_max_retries_default(self) -> None:
        """Test that max_retries defaults to 3."""
        wifi = WiFiStation(self.ssid, self.password)
        self.assertEqual(wifi.max_retries, 3)

    def test_retry_delay_default(self) -> None:
        """Test that retry_delay defaults to 5."""
        wifi = WiFiStation(self.ssid, self.password)
        self.assertEqual(wifi.retry_delay, 5)

    def test_special_characters_in_ssid(self) -> None:
        """Test SSID with special characters."""
        special_ssid = "WiFi-Network_2.4GHz (5G)"
        wifi = WiFiStation(special_ssid, self.password)
        self.assertEqual(wifi.ssid, special_ssid)

    def test_unicode_in_ssid(self) -> None:
        """Test SSID with Unicode characters."""
        unicode_ssid = "WiFi 世界"
        wifi = WiFiStation(unicode_ssid, self.password)
        self.assertEqual(wifi.ssid, unicode_ssid)

    def test_very_long_ssid(self) -> None:
        """Test with very long SSID."""
        long_ssid = "A" * 100
        wifi = WiFiStation(long_ssid, self.password)
        self.assertEqual(wifi.ssid, long_ssid)

    def test_very_long_password(self) -> None:
        """Test with very long password."""
        long_password = "SecurePassword" * 20
        wifi = WiFiStation(self.ssid, long_password)
        self.assertEqual(wifi.password, long_password)


def run_tests() -> None:
    """Run all WiFi station tests."""
    print("=" * 60)
    print("Running WiFi Station Module Tests")
    print("=" * 60)

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestWiFiStatus))
    suite.addTests(loader.loadTestsFromTestCase(TestWiFiStation))

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
