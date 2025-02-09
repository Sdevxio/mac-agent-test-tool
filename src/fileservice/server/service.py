import logging
import mimetypes
import os
from pathlib import Path
from typing import Optional, Iterator, BinaryIO

import grpc

# Import generated proto files (relative imports)
from fileservice import file_service_pb2 as pb2
from fileservice import file_service_pb2_grpc as pb2_grpc

logger = logging.getLogger(__name__)

# Default chunk size (1MB)
DEFAULT_CHUNK_SIZE = 1024 * 1024


class FileServiceServicer(pb2_grpc.FileServiceServicer):
    """Implementation of File Service functionality."""

    def __init__(self):
        # Initialize mimetypes database
        mimetypes.init()

    def _validate_path(self, file_path: str) -> tuple[bool, Optional[str]]:
        """
        Validate file path for security and accessibility.

        Args:
            file_path: Path to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            path = Path(file_path).resolve()

            # Check if file exists
            if not path.exists():
                return False, "File does not exist"

            # Check if it's a file (not a directory)
            if not path.is_file():
                return False, "Path is not a file"

            # Check if we have read permission
            if not os.access(path, os.R_OK):
                return False, "No read permission"

            return True, None

        except Exception as e:
            return False, f"Path validation error: {str(e)}"

    def _stream_file(self, file: BinaryIO, chunk_size: int) -> Iterator[pb2.FileChunkResponse]:
        """
        Stream file contents in chunks.

        Args:
            file: Open file object
            chunk_size: Size of each chunk in bytes

        Yields:
            FileChunkResponse for each chunk
        """
        offset = 0
        while True:
            chunk = file.read(chunk_size)
            if not chunk:
                break

            yield pb2.FileChunkResponse(
                content=chunk,
                offset=offset,
                is_last=False
            )

            offset += len(chunk)

        # Send final chunk to indicate completion
        yield pb2.FileChunkResponse(
            content=b"",
            offset=offset,
            is_last=True
        )

    def _get_file_metadata(self, file_path: str) -> Optional[pb2.FileMetadata]:
        """
        Get metadata for a file.

        Args:
            file_path: Path to the file

        Returns:
            FileMetadata message or None if file doesn't exist
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return None

            stat = path.stat()
            mime_type, _ = mimetypes.guess_type(file_path)

            return pb2.FileMetadata(
                size=stat.st_size,
                mime_type=mime_type or 'application/octet-stream',
                modified_time=int(stat.st_mtime),
                permissions=oct(stat.st_mode)[-3:]  # Last 3 digits of octal permissions
            )
        except Exception as e:
            logger.error(f"Error getting metadata for {file_path}: {e}")
            return None

    def GetFileContents(
            self,
            request: pb2.FileRequest,
            context: grpc.ServicerContext
    ) -> Iterator[pb2.FileChunkResponse]:
        """
        Stream file contents to the client.

        Args:
            request: FileRequest containing file path and options
            context: gRPC servicer context

        Yields:
            FileChunkResponse containing file chunks and metadata
        """
        try:
            # Validate file path
            is_valid, error_msg = self._validate_path(request.file_path)
            if not is_valid:
                yield pb2.FileChunkResponse(
                    error=error_msg,
                    is_last=True
                )
                return

            # Get chunk size from request or use default
            chunk_size = request.chunk_size or DEFAULT_CHUNK_SIZE

            # Get file metadata if requested
            metadata = None
            if request.include_metadata:
                metadata = self._get_file_metadata(request.file_path)

            # Open and stream the file
            with open(request.file_path, 'rb') as file:
                # Send first chunk with metadata
                first_chunk = file.read(chunk_size)
                yield pb2.FileChunkResponse(
                    content=first_chunk,
                    offset=0,
                    is_last=False,
                    metadata=metadata
                )

                # Stream remaining chunks
                for chunk in self._stream_file(file, chunk_size):
                    yield chunk

        except Exception as e:
            error_msg = f"Error streaming file contents: {str(e)}"
            logger.error(error_msg)
            yield pb2.FileChunkResponse(
                error=error_msg,
                is_last=True
            )

    def TransferFile(
            self,
            request: pb2.FileRequest,
            context: grpc.ServicerContext
    ) -> Iterator[pb2.FileChunkResponse]:
        """
        Transfer large files with optimized streaming and progress tracking.

        Args:
            request: FileRequest containing file path and options
            context: gRPC servicer context

        Yields:
            FileChunkResponse containing file chunks, progress, and metadata
        """
        try:
            # Validate file path
            is_valid, error_msg = self._validate_path(request.file_path)
            if not is_valid:
                yield pb2.FileChunkResponse(
                    error=error_msg,
                    is_last=True,
                    metadata=None
                )
                return

            # Get file size for progress tracking
            file_size = os.path.getsize(request.file_path)

            # Optimize chunk size based on file size
            chunk_size = self._optimize_chunk_size(file_size, request.chunk_size)

            # Get metadata if requested
            metadata = None
            if request.include_metadata:
                metadata = self._get_file_metadata(request.file_path)

            first_chunk = True
            with open(request.file_path, 'rb') as file:
                total_sent = 0

                while True:
                    chunk = file.read(chunk_size)
                    if not chunk:
                        break

                    total_sent += len(chunk)
                    progress = (total_sent / file_size) * 100 if file_size > 0 else 100

                    response = pb2.FileChunkResponse(
                        content=chunk,
                        offset=total_sent,
                        is_last=False,
                        progress=progress,
                        metadata=None
                    )
                    if first_chunk and metadata:
                        response.metadata.CopyFrom(metadata)
                    yield response
                    first_chunk = False

                # Send final chunk to indicate completion
                yield pb2.FileChunkResponse(
                    content=b"",
                    offset=total_sent,
                    is_last=True,
                    metadata=None,
                    progress=100.0
                )

        except Exception as e:
            error_msg = f"Error transferring file: {str(e)}"
            logger.error(error_msg)
            yield pb2.FileChunkResponse(
                error=error_msg,
                is_last=True,
                metadata=None
            )

    def IsFileExists(
            self,
            request: pb2.FileRequest,
            context: grpc.ServicerContext
    ) -> pb2.FileExistsResponse:
        """
        Check if a file exists and optionally return its metadata.

        Args:
            request: FileRequest containing file path and options
            context: gRPC servicer context

        Returns:
            FileExistsResponse with existence status and optional metadata
        """
        try:
            file_path = request.file_path
            exists = os.path.exists(file_path)
            metadata = None
            if exists and request.include_metadata:
                metadata = self._get_file_metadata(file_path)

            return pb2.FileExistsResponse(
                exists=exists,
                metadata=metadata,
                error=""
            )

        except Exception as e:
            error_msg = f"Error checking file existence: {str(e)}"
            logger.error(error_msg)
            return pb2.FileExistsResponse(
                exists=False,
                metadata=None,
                error=error_msg
            )

    def _optimize_chunk_size(self, file_size: int, requested_size: int = None) -> int:
        """
        Optimize chunk size based on file size and system constraints.

        Args:
            file_size: Size of the file in bytes
            requested_size: Requested chunk size from client

        Returns:
            Optimized chunk size in bytes
        """
        # Define size thresholds
        SMALL_FILE = 10 * 1024 * 1024  # 10MB
        MEDIUM_FILE = 100 * 1024 * 1024  # 100MB
        LARGE_FILE = 1024 * 1024 * 1024  # 1GB

        # Define chunk sizes
        DEFAULT_CHUNK = 1 * 1024 * 1024  # 1MB
        SMALL_CHUNK = 512 * 1024  # 512KB
        MEDIUM_CHUNK = 2 * 1024 * 1024  # 2MB
        LARGE_CHUNK = 4 * 1024 * 1024  # 4MB
        MAX_CHUNK = 8 * 1024 * 1024  # 8MB

        if requested_size:
            # Honor requested size but cap it at MAX_CHUNK
            return min(requested_size, MAX_CHUNK)

        # Choose chunk size based on file size
        if file_size < SMALL_FILE:
            return SMALL_CHUNK
        elif file_size < MEDIUM_FILE:
            return MEDIUM_CHUNK
        elif file_size < LARGE_FILE:
            return LARGE_CHUNK
        else:
            return MAX_CHUNK
