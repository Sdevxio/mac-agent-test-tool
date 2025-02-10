import logging
import signal
import sys
from pathlib import Path
from typing import Optional

import google
from fileservice.server import FileServer
# Ensure the google.protobuf module is correctly added to sys.path
sys.path.insert(0, google.protobuf.__path__[0])
# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.info("Starting FileService app...")


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


def get_base_path() -> Path:
    """Get the base path for resources and data."""
    if hasattr(sys, '_MEIPASS'):  # Used when running from .app
        return Path(sys._MEIPASS)
    return Path(__file__).parent


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

    BASE_PATH = get_base_path()
    logger.info(f"Application base path: {BASE_PATH}")

if __name__ == '__main__':
    main()