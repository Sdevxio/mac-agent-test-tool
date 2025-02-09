import logging
from concurrent import futures
from typing import Optional

import grpc

from .port_manager import PortManager
from .service import FileServiceServicer
from .. import file_service_pb2_grpc

logger = logging.getLogger(__name__)


class FileServer:
    """Base server class that handles port management and server lifecycle."""

    def __init__(self, max_workers: int = 10, ports: Optional[list[int]] = None):
        self.max_workers = max_workers
        self._port_manager = PortManager(ports)
        self._server: Optional[grpc.Server] = None
        self._port: Optional[int] = None
        self._service = FileServiceServicer()

    def start(self) -> bool:
        """Start the gRPC server."""
        try:
            if self._server:
                logger.warning("Server already running")
                return False

            # Get available port first
            port = self._port_manager.get_available_port()
            if not port:
                logger.error("No available ports")
                return False

            # Create and start server
            self._server = grpc.server(futures.ThreadPoolExecutor(max_workers=self.max_workers))
            file_service_pb2_grpc.add_FileServiceServicer_to_server(self._service, self._server)

            server_address = f'[::]:{port}'
            self._server.add_insecure_port(server_address)
            self._server.start()

            self._port = port
            logger.info(f"Server started on port {port}")
            return True

        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            self.stop()  # Cleanup on failure
            return False

    def stop(self, grace: Optional[float] = None) -> None:
        """Stop the server and release resources."""
        if self._server:
            try:
                self._server.stop(grace)
                self._port_manager.release_port(self._port)
            finally:
                self._server = None
                self._port = None

    @property
    def port(self) -> Optional[int]:
        """Get current server port."""
        return self._port

    def wait_for_termination(self, timeout: Optional[float] = None) -> None:
        """Wait for server termination."""
        if self._server:
            self._server.wait_for_termination(timeout)

    def __enter__(self) -> 'FileServer':
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.stop()