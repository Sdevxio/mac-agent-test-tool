import socket
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)


class PortManager:
    """Manages port allocation for the file service."""

    DEFAULT_PORTS = [50051, 50052, 50053]
    _used_ports = set()  # Class-level tracking of used ports

    def __init__(self, ports: Optional[List[int]] = None):
        self.ports = ports if ports is not None else self.DEFAULT_PORTS
        self.current_port = None

    def is_port_available(self, port: Optional[int]) -> bool:
        """Check if a port is available."""
        if port is None:
            return False

        if port in self._used_ports:
            return False

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(('localhost', port))
            sock.close()
            return True
        except (socket.error, OSError):
            return False

    def get_available_port(self) -> Optional[int]:
        """Get first available port from the list."""
        for port in self.ports:
            if port not in self._used_ports and self.is_port_available(port):
                self._used_ports.add(port)
                self.current_port = port
                return port
        return None

    def release_port(self, port: Optional[int]) -> None:
        """Release a specific port."""
        if port is not None:
            self._used_ports.discard(port)
        if port == self.current_port:
            self.current_port = None