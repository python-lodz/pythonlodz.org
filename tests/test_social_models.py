"""Tests for social domain models."""

import datetime

from pyldz.social.models import (
    AUTOMATED_CHANNELS,
    Channel,
    Post,
    PublishRecord,
    PublishStatus,
    Schedule,
)


def test_post_text_for_returns_override_when_present():
    post = Post(
        id="save-the-date",
        text="kanoniczny",
        overrides={Channel.DISCORD: "@everyone kanoniczny"},
    )
    assert post.text_for(Channel.DISCORD) == "@everyone kanoniczny"


def test_post_text_for_falls_back_to_canonical():
    post = Post(id="save-the-date", text="kanoniczny")
    assert post.text_for(Channel.FACEBOOK) == "kanoniczny"


def test_publish_status_mark_and_is_published():
    status = PublishStatus()
    assert not status.is_published("save-the-date", Channel.FACEBOOK)
    record = PublishRecord(
        at=datetime.datetime(2026, 7, 8, 9, 0, tzinfo=datetime.UTC),
        external_id="123_456",
    )
    status.mark("save-the-date", Channel.FACEBOOK, record)
    assert status.is_published("save-the-date", Channel.FACEBOOK)
    assert status.published["save-the-date:facebook"].external_id == "123_456"


def test_schedule_accepts_numeric_meetup_id_from_yaml():
    schedule = Schedule.model_validate(
        {
            "meetup": 65,
            "posts": [
                {
                    "post": "save-the-date",
                    "channels": ["facebook", "linkedin"],
                    "scheduled": "2026-07-08 09:00:00",
                }
            ],
        }
    )
    assert schedule.meetup == "65"
    assert schedule.timezone == "Europe/Warsaw"
    assert schedule.posts[0].channels == [Channel.FACEBOOK, Channel.LINKEDIN]
    assert schedule.posts[0].image is None
    assert schedule.posts[0].ig_tagged == []


def test_linkedin_is_not_automated():
    assert Channel.LINKEDIN not in AUTOMATED_CHANNELS
    assert set(AUTOMATED_CHANNELS) == {
        Channel.FACEBOOK,
        Channel.INSTAGRAM,
        Channel.DISCORD,
    }
