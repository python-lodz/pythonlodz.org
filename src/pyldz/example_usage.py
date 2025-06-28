#!/usr/bin/env python3
"""Example usage of the logging configuration."""

import logging

from .logging_config import setup_default_logging

# Setup logging with rich formatting
setup_default_logging(debug=True)

# Get logger for this module
log = logging.getLogger(__name__)


def demonstrate_logging():
    """Demonstrate different logging levels with rich formatting."""
    log.debug("This is a debug message - shows detailed information")
    log.info("This is an info message - general information")
    log.warning("This is a warning message - something might be wrong")
    log.error("This is an error message - something went wrong")
    
    # Demonstrate logging with variables (using % formatting for performance)
    user_name = "john_doe"
    meetup_count = 42
    log.info("Processing %d meetups for user %s", meetup_count, user_name)
    
    # Demonstrate exception logging
    try:
        result = 1 / 0
    except ZeroDivisionError as e:
        log.error("Mathematical error occurred: %s", e)
        log.exception("Full traceback for debugging:")


def demonstrate_repository_logging():
    """Demonstrate how logging is used in the repository."""
    from .config import GoogleSheetsConfig
    from .repository import GoogleSheetsRepository
    from pathlib import Path
    
    # Create a test configuration
    config = GoogleSheetsConfig(
        sheet_id="test_sheet_id",
        credentials_path=Path("nonexistent.json"),
        token_cache_path=Path("nonexistent_token.json")
    )
    
    # Create repository instance
    repo = GoogleSheetsRepository(config)
    
    log.info("Created repository with config: %s", config.sheet_id)
    
    # This will demonstrate error logging when credentials file doesn't exist
    try:
        repo.fetch_meetups_data()
    except Exception as e:
        log.error("Expected error when fetching data: %s", e)


if __name__ == "__main__":
    log.info("Starting logging demonstration")
    demonstrate_logging()
    log.info("Basic logging demonstration completed")
    
    log.info("Starting repository logging demonstration")
    demonstrate_repository_logging()
    log.info("Repository logging demonstration completed")
