"""Tests for YouTubeLive (google client mocked)."""

import datetime

from zoneinfo import ZoneInfo

import pyldz.social.youtube as youtube_module
from pyldz.social.youtube import YouTubeLive


class FakeInsert:
    def __init__(self, captured: dict):
        self.captured = captured

    def execute(self) -> dict:
        return {"id": "abc123"}


class FakeBroadcasts:
    def __init__(self, captured: dict):
        self.captured = captured

    def insert(self, part: str, body: dict) -> FakeInsert:
        self.captured["part"] = part
        self.captured["body"] = body
        return FakeInsert(self.captured)


class FakeYouTube:
    def __init__(self, captured: dict):
        self.captured = captured

    def liveBroadcasts(self) -> FakeBroadcasts:  # noqa: N802 — API google
        return FakeBroadcasts(self.captured)


def test_create_live_schedules_broadcast_and_returns_watch_url(monkeypatch):
    captured: dict = {}
    monkeypatch.setattr(youtube_module, "build", lambda *a, **k: FakeYouTube(captured))
    monkeypatch.setattr(YouTubeLive, "_get_credentials", lambda self: object())
    live = YouTubeLive()
    start = datetime.datetime(2026, 7, 29, 17, 45, tzinfo=ZoneInfo("Europe/Warsaw"))
    url = live.create_live(title="Python Łódź #65", start=start, description="opis")

    assert url == "https://www.youtube.com/watch?v=abc123"
    assert captured["part"] == "snippet,status,contentDetails"
    snippet = captured["body"]["snippet"]
    assert snippet["title"] == "Python Łódź #65"
    assert snippet["description"] == "opis"
    assert snippet["scheduledStartTime"] == "2026-07-29T15:45:00+00:00"
    assert captured["body"]["status"]["privacyStatus"] == "public"
