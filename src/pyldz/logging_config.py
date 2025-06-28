import logging
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler
from rich.traceback import install


def setup_logging(
    level: str = "INFO",
    show_time: bool = True,
    show_path: bool = False,
    enable_rich_tracebacks: bool = True,
    console: Optional[Console] = None,
) -> None:
    """
    Set up logging with rich formatting.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        show_time: Whether to show timestamps in logs
        show_path: Whether to show file paths in logs
        enable_rich_tracebacks: Whether to enable rich traceback formatting
        console: Optional console instance to use
    """
    if enable_rich_tracebacks:
        install(show_locals=True)

    if console is None:
        console = Console()

    # Configure rich handler
    rich_handler = RichHandler(
        console=console,
        show_time=show_time,
        show_path=show_path,
        rich_tracebacks=True,
        tracebacks_show_locals=True,
    )

    # Set up logging format
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(message)s",
        datefmt="[%X]",
        handlers=[rich_handler],
        force=True,  # Override any existing configuration
    )

    # Reduce noise from third-party libraries
    logging.getLogger("googleapiclient").setLevel(logging.WARNING)
    logging.getLogger("google_auth_httplib2").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the given name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# Convenience function for common usage
def setup_default_logging(debug: bool = False) -> None:
    """
    Set up default logging configuration.

    Args:
        debug: Whether to enable debug logging
    """
    level = "DEBUG" if debug else "INFO"
    setup_logging(
        level=level,
        show_time=True,
        show_path=debug,  # Only show paths in debug mode
        enable_rich_tracebacks=True,
    )
