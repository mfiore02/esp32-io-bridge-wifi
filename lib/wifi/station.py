"""WiFi Station mode management module.

This module provides WiFi station functionality with automatic
reconnection and status monitoring for ESP32 devices.
"""

from typing import Optional, Dict, Any, Callable
import time

try:
    import network
except ImportError:
    # For development/testing on non-MicroPython systems
    network = None

__all__ = ['WiFiStation', 'WiFiStatus']


class WiFiStatus:
    """WiFi connection status constants."""
    IDLE = 0
    CONNECTING = 1
    CONNECTED = 2
    FAILED = 3
    DISCONNECTED = 4
    NO_AP_FOUND = 5
    WRONG_PASSWORD = 6


class WiFiStation:
    """Manage WiFi station mode connection.

    Provides WiFi station functionality with automatic reconnection,
    configurable retry logic, and comprehensive status monitoring.

    Example:
        >>> from lib.wifi.station import WiFiStation
        >>> wifi = WiFiStation('MyNetwork', 'password')
        >>> if wifi.connect(timeout=15):
        ...     print(f"Connected! IP: {wifi.get_ip()}")
        ...     print(f"Signal strength: {wifi.get_rssi()} dBm")

        >>> # With auto-reconnect
        >>> wifi = WiFiStation('MyNetwork', 'password', auto_reconnect=True)
        >>> wifi.connect()
        >>> # Connection will be automatically maintained
    """

    def __init__(
        self,
        ssid: str,
        password: str,
        auto_reconnect: bool = True,
        max_retries: int = 3,
        retry_delay: int = 5
    ) -> None:
        """Initialize WiFi station.

        Args:
            ssid: Network SSID to connect to
            password: Network password
            auto_reconnect: Enable automatic reconnection on disconnect
            max_retries: Maximum connection retry attempts
            retry_delay: Delay between retries in seconds
        """
        self.ssid = ssid
        self.password = password
        self.auto_reconnect = auto_reconnect
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Initialize WiFi interface
        if network:
            self._sta: Optional[network.WLAN] = network.WLAN(network.STA_IF)
        else:
            self._sta = None

        self._status: int = WiFiStatus.IDLE
        self._retry_count: int = 0
        self._last_error: Optional[str] = None

    def connect(self, timeout: int = 10) -> bool:
        """Connect to WiFi network.

        Attempts to connect to the configured network with retry logic.
        If auto_reconnect is enabled, connection will be monitored and
        automatically restored if lost.

        Args:
            timeout: Connection timeout in seconds

        Returns:
            True if connected successfully, False otherwise

        Example:
            >>> wifi = WiFiStation('MyNetwork', 'password')
            >>> if wifi.connect(timeout=20):
            ...     print("Connected successfully")
            ... else:
            ...     print(f"Connection failed: {wifi.get_error()}")
        """
        if not self._sta:
            self._last_error = "WiFi hardware not available"
            self._status = WiFiStatus.FAILED
            return False

        self._status = WiFiStatus.CONNECTING
        self._retry_count = 0

        # Activate station interface
        if not self._sta.active():
            self._sta.active(True)
            time.sleep(0.5)  # Give interface time to activate

        # Try connection with retries
        while self._retry_count < self.max_retries:
            if self._attempt_connection(timeout):
                self._status = WiFiStatus.CONNECTED
                self._last_error = None
                return True

            self._retry_count += 1
            if self._retry_count < self.max_retries:
                time.sleep(self.retry_delay)

        self._status = WiFiStatus.FAILED
        return False

    def _attempt_connection(self, timeout: int) -> bool:
        """Attempt a single connection to the network.

        Args:
            timeout: Connection timeout in seconds

        Returns:
            True if connection successful
        """
        if not self._sta:
            return False

        # If already connected, check if it's to the right network
        if self._sta.isconnected():
            config = self._sta.ifconfig()
            if config[0] != '0.0.0.0':  # Valid IP assigned
                return True

        # Disconnect if connected to wrong network
        if self._sta.isconnected():
            self._sta.disconnect()
            time.sleep(1)

        # Attempt connection
        try:
            self._sta.connect(self.ssid, self.password)
        except Exception as e:
            self._last_error = f"Connection error: {e}"
            return False

        # Wait for connection
        start_time = time.time()
        while not self._sta.isconnected():
            if time.time() - start_time > timeout:
                self._last_error = f"Connection timeout after {timeout}s"
                self._status = WiFiStatus.FAILED
                return False

            # Check for specific failure conditions
            status = self._sta.status()
            if status == network.STAT_WRONG_PASSWORD:
                self._last_error = "Wrong password"
                self._status = WiFiStatus.WRONG_PASSWORD
                return False
            elif status == network.STAT_NO_AP_FOUND:
                self._last_error = "Access point not found"
                self._status = WiFiStatus.NO_AP_FOUND
                return False

            time.sleep(0.1)

        return True

    def disconnect(self) -> None:
        """Disconnect from WiFi network.

        Cleanly disconnects from the network and deactivates the
        station interface.

        Example:
            >>> wifi.disconnect()
            >>> print(wifi.is_connected())  # False
        """
        if self._sta:
            if self._sta.isconnected():
                self._sta.disconnect()
            self._sta.active(False)

        self._status = WiFiStatus.DISCONNECTED

    def is_connected(self) -> bool:
        """Check if connected to WiFi network.

        Returns:
            True if connected to WiFi with valid IP

        Example:
            >>> if wifi.is_connected():
            ...     print("Online")
            ... else:
            ...     print("Offline")
        """
        if not self._sta:
            return False

        if not self._sta.isconnected():
            return False

        # Verify we have a valid IP address
        try:
            config = self._sta.ifconfig()
            return config[0] != '0.0.0.0'
        except Exception:
            return False

    def get_ip(self) -> Optional[str]:
        """Get assigned IP address.

        Returns:
            IP address string or None if not connected

        Example:
            >>> ip = wifi.get_ip()
            >>> if ip:
            ...     print(f"Device IP: {ip}")
        """
        if not self._sta or not self._sta.isconnected():
            return None

        try:
            return self._sta.ifconfig()[0]
        except Exception:
            return None

    def get_netmask(self) -> Optional[str]:
        """Get network subnet mask.

        Returns:
            Netmask string or None if not connected
        """
        if not self._sta or not self._sta.isconnected():
            return None

        try:
            return self._sta.ifconfig()[1]
        except Exception:
            return None

    def get_gateway(self) -> Optional[str]:
        """Get network gateway address.

        Returns:
            Gateway IP address or None if not connected
        """
        if not self._sta or not self._sta.isconnected():
            return None

        try:
            return self._sta.ifconfig()[2]
        except Exception:
            return None

    def get_dns(self) -> Optional[str]:
        """Get DNS server address.

        Returns:
            DNS server IP or None if not connected
        """
        if not self._sta or not self._sta.isconnected():
            return None

        try:
            return self._sta.ifconfig()[3]
        except Exception:
            return None

    def get_rssi(self) -> Optional[int]:
        """Get WiFi signal strength (RSSI).

        Returns:
            Signal strength in dBm or None if not connected.
            Typical values: -30 (excellent) to -90 (poor)

        Example:
            >>> rssi = wifi.get_rssi()
            >>> if rssi and rssi > -50:
            ...     print("Excellent signal")
            >>> elif rssi and rssi > -70:
            ...     print("Good signal")
            >>> else:
            ...     print("Weak signal")
        """
        if not self._sta or not self._sta.isconnected():
            return None

        try:
            return self._sta.status('rssi')
        except Exception:
            return None

    def get_mac(self) -> Optional[str]:
        """Get MAC address of WiFi interface.

        Returns:
            MAC address as colon-separated hex string or None

        Example:
            >>> mac = wifi.get_mac()
            >>> print(f"Device MAC: {mac}")
        """
        if not self._sta:
            return None

        try:
            import ubinascii
            mac_bytes = self._sta.config('mac')
            return ubinascii.hexlify(mac_bytes, ':').decode()
        except Exception:
            return None

    def get_status(self) -> Dict[str, Any]:
        """Get detailed connection status.

        Returns:
            Dictionary with comprehensive status information

        Example:
            >>> status = wifi.get_status()
            >>> print(f"Connected: {status['connected']}")
            >>> print(f"IP: {status['ip']}")
            >>> print(f"Signal: {status['rssi']} dBm")
        """
        return {
            'connected': self.is_connected(),
            'status': self._status,
            'status_name': self._get_status_name(self._status),
            'ssid': self.ssid,
            'ip': self.get_ip(),
            'netmask': self.get_netmask(),
            'gateway': self.get_gateway(),
            'dns': self.get_dns(),
            'rssi': self.get_rssi(),
            'mac': self.get_mac(),
            'retry_count': self._retry_count,
            'last_error': self._last_error
        }

    def get_error(self) -> Optional[str]:
        """Get last error message.

        Returns:
            Last error message or None if no error

        Example:
            >>> if not wifi.connect():
            ...     print(f"Error: {wifi.get_error()}")
        """
        return self._last_error

    def check_connection(self) -> bool:
        """Check connection and attempt reconnect if needed.

        This method should be called periodically if auto_reconnect
        is enabled to maintain the connection.

        Returns:
            True if connected, False otherwise

        Example:
            >>> # In main loop
            >>> while True:
            ...     wifi.check_connection()
            ...     # Do other work
            ...     time.sleep(1)
        """
        if self.is_connected():
            self._status = WiFiStatus.CONNECTED
            return True

        if self.auto_reconnect:
            return self.connect()

        return False

    @staticmethod
    def _get_status_name(status: int) -> str:
        """Get human-readable status name.

        Args:
            status: Status code

        Returns:
            Status name string
        """
        status_names = {
            WiFiStatus.IDLE: 'IDLE',
            WiFiStatus.CONNECTING: 'CONNECTING',
            WiFiStatus.CONNECTED: 'CONNECTED',
            WiFiStatus.FAILED: 'FAILED',
            WiFiStatus.DISCONNECTED: 'DISCONNECTED',
            WiFiStatus.NO_AP_FOUND: 'NO_AP_FOUND',
            WiFiStatus.WRONG_PASSWORD: 'WRONG_PASSWORD'
        }
        return status_names.get(status, 'UNKNOWN')

    def scan_networks(self) -> list:
        """Scan for available WiFi networks.

        Returns:
            List of tuples: (ssid, bssid, channel, RSSI, authmode, hidden)

        Example:
            >>> networks = wifi.scan_networks()
            >>> for ssid, bssid, channel, rssi, authmode, hidden in networks:
            ...     print(f"{ssid}: {rssi} dBm on channel {channel}")
        """
        if not self._sta:
            return []

        if not self._sta.active():
            self._sta.active(True)
            time.sleep(0.5)

        try:
            return self._sta.scan()
        except Exception:
            return []
