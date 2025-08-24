#!/usr/bin/env python3
"""Python Łódź Meetup Management CLI."""

import logging
from pathlib import Path

import typer
from typing_extensions import Annotated

from pyldz.config import AppConfig
from pyldz.hugo_generator import HugoMeetupGenerator
from pyldz.image_generator import MeetupImageGenerator
from pyldz.logging_config import setup_logging
from pyldz.models import GoogleSheetsAPI, GoogleSheetsRepository, Meetup, Speaker

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
        if talk.language.value == "EN":
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
    meetup_id: Annotated[
        str | None,
        typer.Option(
            "--meetup-id",
            "-m",
            help="Generate Hugo files for specific meetup ID (optional)",
        ),
    ] = None,
) -> None:
    """Generate Hugo markdown files for meetups from Google Sheets data."""
    setup_logging(level="INFO")

    log.info("🚀 Generating Hugo meetup files...")
    log.info("=" * 50)

    config = AppConfig()

    repository = GoogleSheetsRepository(GoogleSheetsAPI(config.google_sheets))
    generator = HugoMeetupGenerator(output_dir)

    log.info("Generating meetup markdown files...")
    if meetup_id:
        generated_files = [generator.generate_meetup(meetup_id, repository)]
    else:
        generated_files = generator.generate_all_meetups(repository)

    log.info(f"Generated {len(generated_files)} meetup files:")
    for file_path in generated_files:
        log.info(f"  - {file_path}")

    log.info("🎉 Hugo file generation completed successfully!")


@app.command()
def generate_images(
    output_dir: Annotated[
        Path,
        typer.Option(
            "--output-dir",
            "-o",
            help="Output directory for Hugo site (default: page)",
        ),
    ] = Path("page"),
    meetup_id: Annotated[
        str | None,
        typer.Option(
            "--meetup-id",
            "-m",
            help="Generate image for specific meetup ID (optional)",
        ),
    ] = None,
) -> None:
    """Generate featured images for meetups."""
    setup_logging(level="INFO")

    log.info("🖼️  Generating meetup featured images...")
    log.info("=" * 50)

    # Load configuration
    config = AppConfig()

    # Setup repository
    api = GoogleSheetsAPI(config.google_sheets)
    repository = GoogleSheetsRepository(api)

    # Setup image generator
    assets_dir = output_dir / "assets"
    cache_dir = output_dir.parent / "cache" / "avatars"
    image_generator = MeetupImageGenerator(assets_dir, cache_dir)

    if meetup_id:
        # Generate image for specific meetup
        meetup = repository.get_meetup_by_id(meetup_id)
        if not meetup:
            log.error(f"Meetup {meetup_id} not found or not enabled")
            raise typer.Exit(1)

        speakers = repository.get_speakers_for_meetup(
            meetup_id, repository._fetch_talks_data()
        )
        output_path = output_dir / "content" / "spotkania" / meetup_id / "featured.png"

        try:
            image_generator.generate_featured_image(meetup, speakers, output_path)
            log.info(f"Generated image for meetup {meetup_id}: {output_path}")
        except Exception as e:
            log.error(f"Failed to generate image for meetup {meetup_id}: {e}")
            raise typer.Exit(1)
    else:
        # Generate images for all enabled meetups
        meetups = repository.get_all_enabled_meetups()
        generated_count = 0

        for meetup in meetups:
            speakers = repository.get_speakers_for_meetup(
                meetup.meetup_id, repository._fetch_talks_data()
            )
            output_path = (
                output_dir / "content" / "spotkania" / meetup.meetup_id / "featured.png"
            )

            try:
                image_generator.generate_featured_image(meetup, speakers, output_path)
                log.info(f"Generated image for meetup {meetup.meetup_id}")
                generated_count += 1
            except Exception as e:
                log.error(
                    f"Failed to generate image for meetup {meetup.meetup_id}: {e}"
                )

        log.info(f"Generated {generated_count} images out of {len(meetups)} meetups")

    log.info("🎉 Image generation completed!")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
