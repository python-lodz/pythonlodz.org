#!/usr/bin/env python3

import logging
import sys
from pathlib import Path

from .config import AppConfig
from .logging_config import setup_default_logging
from .repository import GoogleSheetsRepository

log = logging.getLogger(__name__)


def display_meetup_summary(meetup):
    log.info("📅 Meetup #%s: %s", meetup.number, meetup.title)
    log.info("   📍 Location: %s", meetup.location)
    log.info("   🗓️  Date: %s at %s", meetup.date, meetup.time)
    log.info("   🎤 Talks: %d", meetup.talk_count)

    if meetup.sponsors:
        log.info("   🏢 Sponsors: %s", ", ".join(meetup.sponsors))

    if meetup.meetup_url:
        log.info("   🔗 Meetup URL: %s", meetup.meetup_url)

    if meetup.featured:
        log.info("   ⭐ Featured meetup")

    _display_meetup_talks(meetup)


def _display_meetup_talks(meetup):
    for i, talk in enumerate(meetup.talks, 1):
        log.info("   Talk %d: %s (Speaker: %s)", i, talk.title, talk.speaker_id)
        if talk.language.value == "en":
            log.info("           Language: English")


def display_speaker_summary(speaker):
    log.info("👤 %s (ID: %s)", speaker.name, speaker.id)
    if speaker.bio:
        bio_preview = _truncate_bio_for_summary(speaker.bio)
        log.info("   Bio: %s", bio_preview)

    if speaker.social_links:
        platforms = [link.platform for link in speaker.social_links]
        log.info("   Social: %s", ", ".join(platforms))


def _truncate_bio_for_summary(bio):
    return bio[:100] + "..." if len(bio) > 100 else bio


def main():
    setup_default_logging(debug=False)

    log.info("🚀 Python Łódź Meetup Data Fetcher")
    log.info("=" * 50)

    try:
        config = _load_and_validate_configuration()
        repository = _create_repository(config)
        meetups = _fetch_and_validate_meetups(repository)
        _display_all_meetups(meetups)
        _display_all_speakers(repository)

        log.info("🎉 Data fetch completed successfully!")
        return 0

    except KeyboardInterrupt:
        log.info("⏹️  Operation cancelled by user")
        return 1
    except Exception as e:
        log.error("💥 An error occurred: %s", e)
        log.exception("Full traceback:")
        return 1


def _load_and_validate_configuration():
    log.info("📋 Loading configuration...")
    config = AppConfig()

    if not config.google_sheets.credentials_path.exists():
        log.error(
            "❌ Credentials file not found: %s",
            config.google_sheets.credentials_path,
        )
        log.info("💡 Please ensure you have the Google Sheets API credentials file.")
        log.info("   You can get it from: https://console.cloud.google.com/")
        sys.exit(1)

    return config


def _create_repository(config):
    log.info("🔗 Connecting to Google Sheets...")
    return GoogleSheetsRepository(config.google_sheets)


def _fetch_and_validate_meetups(repository):
    log.info("📊 Fetching enabled meetups...")
    meetups = repository.get_all_enabled_meetups()

    if not meetups:
        log.warning("⚠️  No enabled meetups found.")
        sys.exit(0)

    log.info("✅ Found %d enabled meetup(s)", len(meetups))
    log.info("")
    return meetups


def _display_all_meetups(meetups):
    log.info("📅 MEETUPS:")
    log.info("-" * 30)
    for meetup in sorted(meetups, key=lambda m: m.date, reverse=True):
        display_meetup_summary(meetup)
        log.info("")


def _display_all_speakers(repository):
    log.info("👥 SPEAKERS:")
    log.info("-" * 30)
    speakers = repository.get_all_speakers()
    log.info("✅ Found %d unique speaker(s)", len(speakers))
    log.info("")

    for speaker in sorted(speakers, key=lambda s: s.name):
        display_speaker_summary(speaker)
        log.info("")


if __name__ == "__main__":
    sys.exit(main())
