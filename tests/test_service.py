import os
import tempfile
import unittest
from pathlib import Path

import grpc_testing
import pytest

from fileservice import file_service_pb2 as pb2
from fileservice.server.service import FileServiceServicer


class TestFileService(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test."""
        self.servicer = FileServiceServicer()

        # Create temporary test files
        self.temp_dir = tempfile.mkdtemp()

        # Create a test file with content
        self.test_file_path = os.path.join(self.temp_dir, "test_file.txt")
        with open(self.test_file_path, "w") as f:
            f.write("Test content\n" * 1000)  # Create some content

        # Create a test file for read permission testing
        self.no_read_file = os.path.join(self.temp_dir, "no_read.txt")
        with open(self.no_read_file, "w") as f:
            f.write("Restricted content")
        os.chmod(self.no_read_file, 0o200)  # Write-only permission

    def tearDown(self):
        """Clean up test environment after each test."""
        # Reset file permissions for cleanup
        try:
            os.chmod(self.no_read_file, 0o600)
        except:
            pass

        # Remove test files
        for file in [self.test_file_path, self.no_read_file]:
            try:
                os.remove(file)
            except:
                pass

        # Remove temp directory
        try:
            os.rmdir(self.temp_dir)
        except:
            pass

    def test_is_file_exists_success(self):
        """Test IsFileExists with existing file."""
        request = pb2.FileRequest(
            file_path=self.test_file_path,
            include_metadata=True
        )

        response = self.servicer.IsFileExists(request, None)

        self.assertTrue(response.exists)
        self.assertIsNotNone(response.metadata)
        self.assertEqual(response.metadata.mime_type, 'text/plain')
        self.assertGreater(response.metadata.size, 0)

    def test_is_file_exists_nonexistent(self):
        """Test IsFileExists with non-existent file."""
        request = pb2.FileRequest(
            file_path=os.path.join(self.temp_dir, "nonexistent.txt")
        )

        response = self.servicer.IsFileExists(request, None)

        self.assertFalse(response.exists)
        self.assertIsNone(response.metadata)

    def test_get_file_contents_success(self):
        """Test GetFileContents with valid file."""
        request = pb2.FileRequest(
            file_path=self.test_file_path,
            chunk_size=1024,
            include_metadata=True
        )

        chunks = list(self.servicer.GetFileContents(request, None))

        # Verify we got chunks
        self.assertTrue(len(chunks) > 0)

        # First chunk should have metadata
        self.assertIsNotNone(chunks[0].metadata)

        # Last chunk should be marked
        self.assertTrue(chunks[-1].is_last)

        # Verify content
        content = b''.join(chunk.content for chunk in chunks)
        with open(self.test_file_path, 'rb') as f:
            original = f.read()
        self.assertEqual(content, original)

    def test_get_file_contents_no_permission(self):
        """Test GetFileContents with no read permission."""
        request = pb2.FileRequest(
            file_path=self.no_read_file
        )

        chunks = list(self.servicer.GetFileContents(request, None))

        # Should get error in first and only chunk
        self.assertEqual(len(chunks), 1)
        self.assertTrue(chunks[0].is_last)
        self.assertIn("permission", chunks[0].error.lower())

    def test_get_file_contents_nonexistent(self):
        """Test GetFileContents with non-existent file."""
        request = pb2.FileRequest(
            file_path=os.path.join(self.temp_dir, "nonexistent.txt")
        )

        chunks = list(self.servicer.GetFileContents(request, None))

        # Should get error in first and only chunk
        self.assertEqual(len(chunks), 1)
        self.assertTrue(chunks[0].is_last)
        self.assertIn("exist", chunks[0].error.lower())