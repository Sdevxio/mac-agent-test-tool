import socket
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)


class PortManager:
    """Manages port allocation for the file service."""

    DEFAULT_PORTS = [50051, 50052, 50053]

    def __init__(self, ports: Optional[List[int]] = None):
        self.ports = ports if ports is not None else self.DEFAULT_PORTS
        self.current_port = None

    def is_port_available(self, port: Optional[int]) -> bool:
        """Check if a port is available."""
        if port is None:
            return False

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            # Setting SO_REUSEADDR before bind to ensure port is released
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('localhost', port))
            return True
        except (socket.error, OSError):
            return False
        finally:
            sock.close()

    def get_available_port(self) -> Optional[int]:
        """Get first available port from the list."""
        for port in self.ports:
            if self.is_port_available(port):
                self.current_port = port
                return port
        return None

    def release_port(self, port: Optional[int]) -> None:
        """Release a specific port."""
        if port is None:
            return

        # Force close any existing connections
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('localhost', port))
        except:
            pass
        finally:
            sock.close()

        if port == self.current_port:
            self.current_port = None