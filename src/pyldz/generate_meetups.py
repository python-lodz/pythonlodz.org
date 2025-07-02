#!/usr/bin/env python3
"""Script to generate Hugo markdown files for meetups from Google Sheets data."""

import logging
from pathlib import Path

from pyldz.config import AppConfig
from pyldz.hugo_generator import HugoMeetupGenerator
from pyldz.meetup import GoogleSheetsAPI, GoogleSheetsRepository

log = logging.getLogger(__name__)


def main():
    """Generate meetup markdown files."""
    # Load configuration
    config = AppConfig()
    
    # Setup repository
    api = GoogleSheetsAPI(config.google_sheets)
    repository = GoogleSheetsRepository(api)
    
    # Setup generator
    page_dir = Path("page")
    generator = HugoMeetupGenerator(page_dir)
    
    # Generate all meetups
    log.info("Generating meetup markdown files...")
    generated_files = generator.generate_all_meetups(repository)
    
    log.info(f"Generated {len(generated_files)} meetup files:")
    for file_path in generated_files:
        log.info(f"  - {file_path}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
