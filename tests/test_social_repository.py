"""Tests for SocialRepository."""

import datetime
from pathlib import Path

from pyldz.social.models import Channel, PublishRecord, PublishStatus
from pyldz.social.repository import SocialRepository


def test_load_posts(social_content_dir: Path):
    repository = SocialRepository(social_content_dir)
    posts = repository.load_posts("65")
    assert set(posts) == {"save-the-date", "last-call"}
    assert Channel.DISCORD in posts["save-the-date"].overrides


def test_load_schedule(social_content_dir: Path):
    repository = SocialRepository(social_content_dir)
    schedule = repository.load_schedule("65")
    assert schedule.meetup == "65"
    assert len(schedule.posts) == 2
    assert schedule.posts[0].scheduled == datetime.datetime(2026, 7, 8, 9, 0)
    assert schedule.posts[0].image == "images/final/save-the-date-4x5.png"


def test_load_status_returns_empty_when_file_missing(social_content_dir: Path):
    repository = SocialRepository(social_content_dir)
    assert repository.load_status("65") == PublishStatus()


def test_save_and_reload_status(social_content_dir: Path):
    repository = SocialRepository(social_content_dir)
    status = PublishStatus()
    status.mark(
        "save-the-date",
        Channel.FACEBOOK,
        PublishRecord(
            at=datetime.datetime(2026, 7, 8, 9, 0, tzinfo=datetime.UTC),
            external_id="123",
        ),
    )
    saved_path = repository.save_status("65", status)
    assert saved_path == social_content_dir / "65" / "social" / "status.json"
    reloaded = repository.load_status("65")
    assert reloaded.is_published("save-the-date", Channel.FACEBOOK)


def test_meetups_with_schedule(social_content_dir: Path):
    repository = SocialRepository(social_content_dir)
    assert repository.meetups_with_schedule() == ["65"]
