"""Basic server initialization test."""
import unittest
from fileservice.server.server import FileServer

class TestFileServer(unittest.TestCase):
    def test_server_initialization(self):
        """Test basic server initialization."""
        server = FileServer()
        self.assertIsNotNone(server)