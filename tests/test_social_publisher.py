"""Tests for due computation and the Publisher orchestrator."""

import datetime
from pathlib import Path

from zoneinfo import ZoneInfo

from pyldz.social.models import Channel, PublishRecord, PublishStatus
from pyldz.social.publisher import Publisher, due_items
from pyldz.social.repository import SocialRepository

WARSAW = ZoneInfo("Europe/Warsaw")
AFTER_FIRST_SLOT = datetime.datetime(2026, 7, 8, 9, 0, 5, tzinfo=WARSAW)
AFTER_ALL_SLOTS = datetime.datetime(2026, 7, 28, 12, 0, tzinfo=WARSAW)


class DummyAdapter:
    def __init__(self):
        self.calls = []

    def publish(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return "ext-1"


class FailingAdapter:
    def publish(self, *args, **kwargs):
        raise RuntimeError("boom")


def make_publisher(social_content_dir: Path, adapters: dict) -> Publisher:
    return Publisher(
        SocialRepository(social_content_dir),
        adapters=adapters,
        site_base_url="https://pythonlodz.org",
    )


def test_due_items_skips_future_published_and_linkedin(social_content_dir: Path):
    repository = SocialRepository(social_content_dir)
    schedule = repository.load_schedule("65")
    status = PublishStatus()
    status.mark(
        "save-the-date",
        Channel.FACEBOOK,
        PublishRecord(at=AFTER_FIRST_SLOT),
    )
    due = due_items(schedule, status, AFTER_FIRST_SLOT)
    # last-call jest w przyszłości, FB już opublikowany, linkedin nieautomatyczny
    assert [(item.post, channel) for item, channel in due] == [
        ("save-the-date", Channel.INSTAGRAM),
        ("save-the-date", Channel.DISCORD),
    ]


def test_plan_builds_payloads(social_content_dir: Path):
    publisher = make_publisher(social_content_dir, adapters={})
    planned = publisher.plan("65", AFTER_FIRST_SLOT)
    by_channel = {p.channel: p for p in planned}
    assert set(by_channel) == {Channel.FACEBOOK, Channel.INSTAGRAM, Channel.DISCORD}
    assert by_channel[Channel.FACEBOOK].image_url == (
        "https://pythonlodz.org/spotkania/65/social/images/final/save-the-date-4x5.png"
    )
    assert by_channel[Channel.INSTAGRAM].ig_tagged == ["pythonlodz"]
    assert "#pythonlodz" in by_channel[Channel.INSTAGRAM].text
    assert by_channel[Channel.DISCORD].text.startswith("@everyone")  # override
    assert Path(by_channel[Channel.DISCORD].image_path).exists()


def test_publish_due_marks_status_and_is_idempotent(social_content_dir: Path):
    facebook = DummyAdapter()
    adapters = {
        Channel.FACEBOOK: facebook,
        Channel.INSTAGRAM: DummyAdapter(),
        Channel.DISCORD: DummyAdapter(),
    }
    publisher = make_publisher(social_content_dir, adapters)
    outcomes = publisher.publish_due("65", AFTER_FIRST_SLOT)
    assert all(outcome.ok for outcome in outcomes)
    assert len(outcomes) == 3
    # drugi run: nic nie jest due
    assert publisher.publish_due("65", AFTER_FIRST_SLOT) == []
    assert len(facebook.calls) == 1


def test_publish_due_continues_after_channel_failure(social_content_dir: Path):
    adapters = {
        Channel.FACEBOOK: FailingAdapter(),
        Channel.INSTAGRAM: DummyAdapter(),
        Channel.DISCORD: DummyAdapter(),
    }
    publisher = make_publisher(social_content_dir, adapters)
    outcomes = publisher.publish_due("65", AFTER_FIRST_SLOT)
    by_channel = {o.channel: o for o in outcomes}
    assert not by_channel[Channel.FACEBOOK].ok
    assert "boom" in by_channel[Channel.FACEBOOK].error
    assert by_channel[Channel.INSTAGRAM].ok
    assert by_channel[Channel.DISCORD].ok
    # failed FB pozostaje due na kolejny run
    repository = SocialRepository(social_content_dir)
    status = repository.load_status("65")
    assert not status.is_published("save-the-date", Channel.FACEBOOK)
    assert status.is_published("save-the-date", Channel.INSTAGRAM)


def test_missing_adapter_is_reported_not_raised(social_content_dir: Path):
    publisher = make_publisher(social_content_dir, adapters={})
    outcomes = publisher.publish_due("65", AFTER_FIRST_SLOT)
    assert outcomes and all(not o.ok for o in outcomes)
    assert "konfiguracji" in outcomes[0].error
