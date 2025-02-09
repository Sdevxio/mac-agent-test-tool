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

    def __init__(self, max_workers: int = 10, ports: list[int] = None):
        """
        Initialize the FileServer.

        Args:
            max_workers: Maximum number of worker threads
            ports: Optional list of ports to try
        """
        self.max_workers = max_workers
        self.port_manager = PortManager(ports)
        self._server: Optional[grpc.Server] = None
        self._port: Optional[int] = None
        self._service = FileServiceServicer()

    def start(self) -> bool:
        """
        Start the gRPC server on an available port.

        Returns:
            bool: True if server started successfully, False otherwise
        """
        try:
            # Create the gRPC server
            self._server = grpc.server(
                futures.ThreadPoolExecutor(max_workers=self.max_workers)
            )

            # Register our service
            file_service_pb2_grpc.add_FileServiceServicer_to_server(
                self._service, self._server)

            # Get an available port
            port = self.port_manager.get_available_port()
            if not port:
                logger.error("Could not find available port")
                return False

            # Try to start the server
            server_address = f'[::]:{port}'
            try:
                self._server.add_insecure_port(server_address)
                self._server.start()
                self._port = port
                logger.info(f"Server started successfully on port {port}")
                return True
            except Exception as e:
                logger.error(f"Failed to start server: {e}")
                return False

        except Exception as e:
            logger.error(f"Error starting server: {e}")
            return False

    def stop(self, grace: Optional[float] = None) -> None:
        """
        Stop the server gracefully.

        Args:
            grace: Optional grace period in seconds
        """
        if self._server:
            logger.info("Stopping server...")
            self._server.stop(grace)
            self.port_manager.release_port()
            self._server = None
            self._port = None
            logger.info("Server stopped")

    def wait_for_termination(self, timeout: Optional[float] = None) -> None:
        """
        Wait for the server to terminate.

        Args:
            timeout: Optional timeout in seconds
        """
        if self._server:
            self._server.wait_for_termination(timeout)

    @property
    def port(self) -> Optional[int]:
        """Get the current server port."""
        return self._port

    def __enter__(self) -> 'FileServer':
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.stop()