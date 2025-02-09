import unittest
from concurrent import futures
import threading
import time

from fileservice.server.server import FileServer
from fileservice.server.port_manager import PortManager


class TestFileServer(unittest.TestCase):
    def test_server_start_stop(self):
        """Test server startup and shutdown."""
        server = FileServer()

        # Start server
        self.assertTrue(server.start())
        self.assertIsNotNone(server.port)

        # Verify port is in use
        self.assertFalse(PortManager().is_port_available(server.port))

        # Stop server
        server.stop()

        # Verify port is released
        self.assertTrue(PortManager().is_port_available(server.port))

    def test_server_port_conflict(self):
        """Test server handles port conflicts correctly."""
        # Start first server
        server1 = FileServer()
        self.assertTrue(server1.start())
        port1 = server1.port

        # Try to start second server
        server2 = FileServer()
        self.assertTrue(server2.start())  # Should get different port
        port2 = server2.port

        # Verify different ports
        self.assertNotEqual(port1, port2)

        # Cleanup
        server1.stop()
        server2.stop()

    def test_server_context_manager(self):
        """Test server context manager functionality."""
        with FileServer() as server:
            self.assertIsNotNone(server.port)
            self.assertFalse(PortManager().is_port_available(server.port))

        # Verify cleanup after context
        self.assertTrue(PortManager().is_port_available(server.port))

    def test_server_graceful_shutdown(self):
        """Test server shuts down gracefully."""

        def run_server(server):
            server.start()
            server.wait_for_termination()

        server = FileServer()

        # Start server in thread
        thread = threading.Thread(target=run_server, args=(server,))
        thread.start()

        # Give it time to start
        time.sleep(1)

        # Request shutdown
        server.stop(grace=2.0)

        # Wait for thread to finish
        thread.join(timeout=5)

        self.assertFalse(thread.is_alive())