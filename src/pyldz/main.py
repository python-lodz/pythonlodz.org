#!/usr/bin/env python3
"""Python Łódź Meetup Management CLI."""

import logging
from pathlib import Path

import typer
from typing_extensions import Annotated

from pyldz.config import AppConfig
from pyldz.hugo_generator import HugoMeetupGenerator
from pyldz.logging_config import setup_logging
from pyldz.meetup import GoogleSheetsAPI, GoogleSheetsRepository, Meetup, Speaker

log = logging.getLogger(__name__)

app = typer.Typer(
    name="pyldz",
    help="Python Łódź Meetup Management CLI",
    no_args_is_help=True,
)


def display_meetup_summary(meetup: Meetup) -> None:
    """Display a summary of a meetup."""
    log.info("📅 Meetup #%s: %s", meetup.meetup_id, meetup.title)
    log.info("   📍 Location: %s", meetup.location)
    log.info("   🗓️  Date: %s at %s", meetup.date, meetup.time)
    log.info("   🎤 Talks: %d", meetup.talk_count)

    if meetup.sponsors:
        log.info("   🏢 Sponsors: %s", ", ".join(meetup.sponsors))

    if meetup.meetup_url:
        log.info("   🔗 Meetup URL: %s", meetup.meetup_url)

    _display_meetup_talks(meetup)


def _display_meetup_talks(meetup: Meetup) -> None:
    """Display talks for a meetup."""
    for i, talk in enumerate(meetup.talks, 1):
        log.info("   Talk %d: %s (Speaker: %s)", i, talk.title, talk.speaker_id)
        if talk.language.value == "en":
            log.info("           Language: English")


def display_speaker_summary(speaker: Speaker) -> None:
    """Display a summary of a speaker."""
    log.info("👤 %s (ID: %s)", speaker.name, speaker.id)
    if speaker.bio:
        bio_preview = _truncate_bio_for_summary(speaker.bio)
        log.info("   Bio: %s", bio_preview)

    if speaker.social_links:
        platforms = [link.platform for link in speaker.social_links]
        log.info("   Social: %s", ", ".join(platforms))


def _truncate_bio_for_summary(bio: str) -> str:
    """Truncate bio for summary display."""
    return bio[:100] + "..." if len(bio) > 100 else bio


def _display_all_meetups(meetups: list[Meetup]) -> None:
    """Display all meetups."""
    log.info("📅 MEETUPS:")
    log.info("-" * 30)
    for meetup in sorted(meetups, key=lambda m: m.date, reverse=True):
        display_meetup_summary(meetup)
        log.info("")


@app.command()
def dry_run() -> None:
    """Display meetup data without generating files (dry run)."""
    setup_logging(level="DEBUG")

    log.info("🚀 Python Łódź Meetup Data Fetcher")
    log.info("=" * 50)

    log.info("📋 Loading configuration...")
    config = AppConfig()

    repository = GoogleSheetsRepository(api=GoogleSheetsAPI(config.google_sheets))
    meetups = repository.get_all_enabled_meetups()
    _display_all_meetups(meetups)

    log.info("🎉 Data fetch completed successfully!")


@app.command()
def fill_hugo(
    output_dir: Annotated[
        Path,
        typer.Option(
            "--output-dir",
            "-o",
            help="Output directory for Hugo site (default: page)",
        ),
    ] = Path("page"),
) -> None:
    """Generate Hugo markdown files for meetups from Google Sheets data."""
    setup_logging(level="INFO")

    log.info("🚀 Generating Hugo meetup files...")
    log.info("=" * 50)

    # Load configuration
    config = AppConfig()

    # Setup repository
    api = GoogleSheetsAPI(config.google_sheets)
    repository = GoogleSheetsRepository(api)

    # Setup generator
    generator = HugoMeetupGenerator(output_dir)

    # Generate all meetups
    log.info("Generating meetup markdown files...")
    generated_files = generator.generate_all_meetups(repository)

    log.info(f"Generated {len(generated_files)} meetup files:")
    for file_path in generated_files:
        log.info(f"  - {file_path}")

    log.info("🎉 Hugo file generation completed successfully!")


def main() -> None:
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
