#!/usr/bin/env python3

import logging
import sys

from pyldz.config import AppConfig
from pyldz.logging_config import setup_logging
from pyldz.meetup import GoogleSheetsAPI, GoogleSheetsRepository, Meetup, Speaker

log = logging.getLogger(__name__)


def display_meetup_summary(meetup: Meetup):
    log.info("📅 Meetup #%s: %s", meetup.meetup_id, meetup.title)
    log.info("   📍 Location: %s", meetup.location)
    log.info("   🗓️  Date: %s at %s", meetup.date, meetup.time)
    log.info("   🎤 Talks: %d", meetup.talk_count)

    if meetup.sponsors:
        log.info("   🏢 Sponsors: %s", ", ".join(meetup.sponsors))

    if meetup.meetup_url:
        log.info("   🔗 Meetup URL: %s", meetup.meetup_url)

    _display_meetup_talks(meetup)


def _display_meetup_talks(meetup: Meetup):
    for i, talk in enumerate(meetup.talks, 1):
        log.info("   Talk %d: %s (Speaker: %s)", i, talk.title, talk.speaker_id)
        if talk.language.value == "en":
            log.info("           Language: English")


def display_speaker_summary(speaker: Speaker):
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
    setup_logging(level="DEBUG")

    log.info("🚀 Python Łódź Meetup Data Fetcher")
    log.info("=" * 50)

    log.info("📋 Loading configuration...")
    config = AppConfig()

    repository = GoogleSheetsRepository(api=GoogleSheetsAPI(config.google_sheets))
    meetups = repository.get_all_enabled_meetups()
    _display_all_meetups(meetups)

    log.info("🎉 Data fetch completed successfully!")
    return 0


def _display_all_meetups(meetups):
    log.info("📅 MEETUPS:")
    log.info("-" * 30)
    for meetup in sorted(meetups, key=lambda m: m.date, reverse=True):
        display_meetup_summary(meetup)
        log.info("")


if __name__ == "__main__":
    sys.exit(main())
