import socket
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class PortManager:
    """Manages port selection and availability for the file service."""

    # Default ports to try in order
    DEFAULT_PORTS = [50051, 50052, 50053]

    def __init__(self, ports: list[int] = None):
        """
        Initialize the PortManager.

        Args:
            ports: Optional list of ports to try. If not provided, uses DEFAULT_PORTS.
        """
        self.ports = ports if ports is not None else self.DEFAULT_PORTS
        self._current_port: Optional[int] = None

    @property
    def current_port(self) -> Optional[int]:
        """Get the currently assigned port."""
        return self._current_port

    def is_port_available(self, port: Optional[int]) -> bool:
        """
        Check if a specific port is available.

        Args:
            port: Port number to check

        Returns:
            bool: True if port is available, False otherwise
        """
        if port is None:
            return False

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return True
        except (socket.error, OSError):
            return False

    def get_available_port(self) -> Optional[int]:
        """
        Find the first available port from the configured list.

        Returns:
            int or None: First available port number, or None if no ports are available
        """
        for port in self.ports:
            logger.debug(f"Trying port {port}")
            if self.is_port_available(port):
                self._current_port = port
                logger.info(f"Found available port: {port}")
                return port

        logger.error("No available ports found")
        return None

    def release_port(self) -> None:
        """Release the currently assigned port."""
        self._current_port = None

    def __enter__(self) -> 'PortManager':
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit, ensures port is released."""
        self.release_port()