import logging
import signal
import sys
from typing import Optional

from fileservice.server import FileServer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def handle_shutdown(signum: int, frame, server: Optional[FileServer] = None) -> None:
    """
    Handle shutdown signals gracefully.

    Args:
        signum: Signal number
        frame: Current stack frame
        server: Optional FileServer instance to stop
    """
    logger.info(f"Received signal {signum}")
    if server:
        server.stop(grace=2.0)
    sys.exit(0)


def main() -> None:
    """Main entry point for the file service server."""
    server = FileServer()

    # Set up signal handlers
    signal.signal(signal.SIGTERM, lambda s, f: handle_shutdown(s, f, server))
    signal.signal(signal.SIGINT, lambda s, f: handle_shutdown(s, f, server))

    logger.info("Starting file service server...")
    if not server.start():
        logger.error("Failed to start server")
        sys.exit(1)

    logger.info(f"Server running on port {server.port}")

    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        server.stop(grace=2.0)


if __name__ == '__main__':
    main()