"""WiFi Access Point mode management module.

This module provides WiFi access point (AP) functionality, allowing
the ESP32 to act as a WiFi hotspot for other devices to connect to.
"""

from typing import Optional, Dict, Any, List, Tuple
import time

try:
    import network
except ImportError:
    # For development/testing on non-MicroPython systems
    network = None

__all__ = ['WiFiAccessPoint', 'APStatus']


class APStatus:
    """Access Point status constants."""
    IDLE = 0
    STARTING = 1
    ACTIVE = 2
    FAILED = 3
    STOPPED = 4


class WiFiAccessPoint:
    """Manage WiFi Access Point mode.

    Provides WiFi AP functionality, allowing the ESP32 to act as a
    wireless access point for other devices.

    Example:
        >>> from lib.wifi.access_point import WiFiAccessPoint
        >>> ap = WiFiAccessPoint('ESP32-Bridge', 'password123')
        >>> if ap.start():
        ...     print(f"AP started! Connect to: {ap.get_ssid()}")
        ...     print(f"AP IP: {ap.get_ip()}")

        >>> # Get connected clients
        >>> clients = ap.get_clients()
        >>> print(f"Connected clients: {len(clients)}")
    """

    def __init__(
        self,
        ssid: str,
        password: str = '',
        channel: int = 11,
        hidden: bool = False,
        max_clients: int = 4,
        authmode: int = 3  # WPA2 by default
    ) -> None:
        """Initialize WiFi Access Point.

        Args:
            ssid: Network SSID for the access point
            password: Network password (empty for open network)
            channel: WiFi channel (1-13)
            hidden: Hide SSID from broadcast
            max_clients: Maximum number of connected clients
            authmode: Authentication mode (0=open, 3=WPA2, 4=WPA/WPA2)
        """
        self.ssid = ssid
        self.password = password
        self.channel = channel
        self.hidden = hidden
        self.max_clients = max_clients
        self.authmode = authmode

        # Initialize AP interface
        if network:
            self._ap: Optional[network.WLAN] = network.WLAN(network.AP_IF)
        else:
            self._ap = None

        self._status: int = APStatus.IDLE
        self._last_error: Optional[str] = None

    def start(self) -> bool:
        """Start the access point.

        Activates the AP interface and configures it with the
        specified parameters.

        Returns:
            True if AP started successfully, False otherwise

        Example:
            >>> ap = WiFiAccessPoint('MyESP32', 'secure123')
            >>> if ap.start():
            ...     print("Access point is running")
            ... else:
            ...     print(f"Failed to start: {ap.get_error()}")
        """
        if not self._ap:
            self._last_error = "WiFi hardware not available"
            self._status = APStatus.FAILED
            return False

        self._status = APStatus.STARTING

        try:
            # Activate AP interface
            self._ap.active(True)
            time.sleep(0.5)  # Give interface time to activate

            # Configure AP
            config_params = {
                'essid': self.ssid,
                'channel': self.channel,
                'hidden': self.hidden,
                'max_clients': self.max_clients
            }

            # Only set authmode and password for secured networks
            if self.password:
                config_params['authmode'] = self.authmode
                config_params['password'] = self.password
            else:
                config_params['authmode'] = 0  # Open network

            self._ap.config(**config_params)

            # Verify AP is active
            if self._ap.active():
                self._status = APStatus.ACTIVE
                self._last_error = None
                return True
            else:
                self._last_error = "Failed to activate AP interface"
                self._status = APStatus.FAILED
                return False

        except Exception as e:
            self._last_error = f"AP start error: {e}"
            self._status = APStatus.FAILED
            return False

    def stop(self) -> None:
        """Stop the access point.

        Deactivates the AP interface and disconnects all clients.

        Example:
            >>> ap.stop()
            >>> print(ap.is_active())  # False
        """
        if self._ap:
            self._ap.active(False)

        self._status = APStatus.STOPPED

    def is_active(self) -> bool:
        """Check if access point is active.

        Returns:
            True if AP is running

        Example:
            >>> if ap.is_active():
            ...     print(f"AP is running with {len(ap.get_clients())} clients")
        """
        if not self._ap:
            return False

        return self._ap.active()

    def get_ssid(self) -> str:
        """Get AP SSID.

        Returns:
            SSID of the access point
        """
        return self.ssid

    def get_ip(self) -> Optional[str]:
        """Get AP IP address.

        Returns:
            IP address of the AP or None if not active

        Example:
            >>> ip = ap.get_ip()
            >>> print(f"Connect and navigate to: http://{ip}")
        """
        if not self._ap or not self._ap.active():
            return None

        try:
            return self._ap.ifconfig()[0]
        except Exception:
            return None

    def get_netmask(self) -> Optional[str]:
        """Get AP network subnet mask.

        Returns:
            Netmask string or None if not active
        """
        if not self._ap or not self._ap.active():
            return None

        try:
            return self._ap.ifconfig()[1]
        except Exception:
            return None

    def get_gateway(self) -> Optional[str]:
        """Get AP gateway address.

        Returns:
            Gateway IP address or None if not active
        """
        if not self._ap or not self._ap.active():
            return None

        try:
            return self._ap.ifconfig()[2]
        except Exception:
            return None

    def get_dns(self) -> Optional[str]:
        """Get AP DNS server address.

        Returns:
            DNS server IP or None if not active
        """
        if not self._ap or not self._ap.active():
            return None

        try:
            return self._ap.ifconfig()[3]
        except Exception:
            return None

    def get_mac(self) -> Optional[str]:
        """Get MAC address of AP interface.

        Returns:
            MAC address as colon-separated hex string or None

        Example:
            >>> mac = ap.get_mac()
            >>> print(f"AP MAC address: {mac}")
        """
        if not self._ap:
            return None

        try:
            import ubinascii
            mac_bytes = self._ap.config('mac')
            return ubinascii.hexlify(mac_bytes, ':').decode()
        except Exception:
            return None

    def get_clients(self) -> List[Tuple[str, int]]:
        """Get list of connected clients.

        Returns:
            List of tuples containing (MAC address, RSSI) for each client

        Example:
            >>> clients = ap.get_clients()
            >>> for mac, rssi in clients:
            ...     print(f"Client {mac}: {rssi} dBm")
        """
        if not self._ap or not self._ap.active():
            return []

        try:
            # Get station list (clients connected to AP)
            stations = self._ap.status('stations')
            result = []

            try:
                import ubinascii
                for station in stations:
                    mac = ubinascii.hexlify(station, ':').decode()
                    # RSSI not directly available for AP mode clients
                    # Return 0 as placeholder
                    result.append((mac, 0))
            except Exception:
                pass

            return result

        except Exception:
            return []

    def get_client_count(self) -> int:
        """Get number of connected clients.

        Returns:
            Number of clients connected to the AP

        Example:
            >>> count = ap.get_client_count()
            >>> print(f"{count} devices connected")
        """
        return len(self.get_clients())

    def get_status(self) -> Dict[str, Any]:
        """Get detailed AP status.

        Returns:
            Dictionary with comprehensive status information

        Example:
            >>> status = ap.get_status()
            >>> print(f"Active: {status['active']}")
            >>> print(f"SSID: {status['ssid']}")
            >>> print(f"Clients: {status['client_count']}")
        """
        return {
            'active': self.is_active(),
            'status': self._status,
            'status_name': self._get_status_name(self._status),
            'ssid': self.ssid,
            'channel': self.channel,
            'hidden': self.hidden,
            'authmode': self.authmode,
            'ip': self.get_ip(),
            'netmask': self.get_netmask(),
            'gateway': self.get_gateway(),
            'dns': self.get_dns(),
            'mac': self.get_mac(),
            'client_count': self.get_client_count(),
            'clients': self.get_clients(),
            'last_error': self._last_error
        }

    def get_error(self) -> Optional[str]:
        """Get last error message.

        Returns:
            Last error message or None if no error

        Example:
            >>> if not ap.start():
            ...     print(f"Error: {ap.get_error()}")
        """
        return self._last_error

    def set_ip_config(
        self,
        ip: str = '192.168.4.1',
        netmask: str = '255.255.255.0',
        gateway: str = '192.168.4.1',
        dns: str = '192.168.4.1'
    ) -> bool:
        """Configure AP network settings.

        Args:
            ip: IP address for the AP
            netmask: Network subnet mask
            gateway: Gateway address
            dns: DNS server address

        Returns:
            True if configuration successful

        Example:
            >>> ap.set_ip_config(
            ...     ip='10.0.0.1',
            ...     netmask='255.255.255.0',
            ...     gateway='10.0.0.1',
            ...     dns='10.0.0.1'
            ... )
        """
        if not self._ap:
            self._last_error = "WiFi hardware not available"
            return False

        try:
            self._ap.ifconfig((ip, netmask, gateway, dns))
            return True
        except Exception as e:
            self._last_error = f"IP config error: {e}"
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
            APStatus.IDLE: 'IDLE',
            APStatus.STARTING: 'STARTING',
            APStatus.ACTIVE: 'ACTIVE',
            APStatus.FAILED: 'FAILED',
            APStatus.STOPPED: 'STOPPED'
        }
        return status_names.get(status, 'UNKNOWN')
