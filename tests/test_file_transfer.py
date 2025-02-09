import os
import tempfile
import unittest
from pathlib import Path

import pytest

from fileservice import file_service_pb2 as pb2
from fileservice.server.service import FileServiceServicer


class TestFileTransfer(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        self.servicer = FileServiceServicer()
        self.temp_dir = tempfile.mkdtemp()

        # Create test files of different sizes
        self.small_file = os.path.join(self.temp_dir, "small.txt")
        self.medium_file = os.path.join(self.temp_dir, "medium.txt")
        self.large_file = os.path.join(self.temp_dir, "large.txt")

        # Create small file (100KB)
        with open(self.small_file, "wb") as f:
            f.write(os.urandom(100 * 1024))

        # Create medium file (5MB)
        with open(self.medium_file, "wb") as f:
            f.write(os.urandom(5 * 1024 * 1024))

        # Create large file (20MB)
        with open(self.large_file, "wb") as f:
            f.write(os.urandom(20 * 1024 * 1024))

    def tearDown(self):
        """Clean up test files."""
        for file in [self.small_file, self.medium_file, self.large_file]:
            try:
                os.remove(file)
            except:
                pass
        try:
            os.rmdir(self.temp_dir)
        except:
            pass

    def test_transfer_small_file(self):
        """Test transferring a small file."""
        request = pb2.FileRequest(
            file_path=self.small_file,
            include_metadata=True
        )

        chunks = list(self.servicer.TransferFile(request, None))

        # Verify transfer
        self.assertGreater(len(chunks), 0)
        self.assertTrue(chunks[-1].is_last)
        self.assertIsNotNone(chunks[0].metadata)
        self.assertEqual(chunks[-1].progress, 100.0)

        # Verify content
        content = b''.join(chunk.content for chunk in chunks)
        with open(self.small_file, 'rb') as f:
            original = f.read()
        self.assertEqual(content, original)

    def test_transfer_large_file_progress(self):
        """Test progress tracking for large file transfer."""
        request = pb2.FileRequest(
            file_path=self.large_file,
            include_metadata=True
        )

        chunks = list(self.servicer.TransferFile(request, None))

        # Verify progress
        progress_values = [chunk.progress for chunk in chunks]
        self.assertTrue(all(0 <= p <= 100 for p in progress_values))
        self.assertTrue(progress_values[-1] == 100.0)
        self.assertEqual(sorted(progress_values), progress_values)  # Progress should increase

    def test_transfer_with_custom_chunk_size(self):
        """Test transfer with custom chunk size."""
        chunk_size = 64 * 1024  # 64KB chunks
        request = pb2.FileRequest(
            file_path=self.medium_file,
            chunk_size=chunk_size
        )

        chunks = list(self.servicer.TransferFile(request, None))

        # Verify chunk sizes
        for chunk in chunks[:-1]:  # All except last chunk
            self.assertLessEqual(len(chunk.content), chunk_size)

    def test_transfer_nonexistent_file(self):
        """Test transfer of non-existent file."""
        request = pb2.FileRequest(
            file_path=os.path.join(self.temp_dir, "nonexistent.txt")
        )

        chunks = list(self.servicer.TransferFile(request, None))

        # Should get single error chunk
        self.assertEqual(len(chunks), 1)
        self.assertTrue(chunks[0].is_last)
        self.assertIn("exist", chunks[0].error.lower())

    def test_chunk_size_optimization(self):
        """Test chunk size optimization logic."""
        file_sizes = [
            (100 * 1024, "small"),  # 100KB
            (50 * 1024 * 1024, "medium"),  # 50MB
            (500 * 1024 * 1024, "large"),  # 500MB
        ]

        for size, category in file_sizes:
            chunk_size = self.servicer._optimize_chunk_size(size)
            if category == "small":
                self.assertLessEqual(chunk_size, 512 * 1024)
            elif category == "medium":
                self.assertLessEqual(chunk_size, 2 * 1024 * 1024)
            else:
                self.assertLessEqual(chunk_size, 8 * 1024 * 1024)

    def test_transfer_metadata_handling(self):
        """Test metadata handling during transfer."""
        request = pb2.FileRequest(
            file_path=self.small_file,
            include_metadata=True
        )

        chunks = list(self.servicer.TransferFile(request, None))

        # Verify metadata
        self.assertIsNotNone(chunks[0].metadata)
        self.assertEqual(chunks[0].metadata.size, os.path.getsize(self.small_file))

        # Verify only first chunk has metadata
        for chunk in chunks[1:]:
            self.assertIsNone(chunk.metadata)