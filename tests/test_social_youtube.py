"""Tests for YouTubeLive (google client mocked)."""

import datetime

import pytest
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


class FakeChannels:
    def __init__(self, items: list[dict]):
        self.items = items

    def list(self, part: str, mine: bool) -> "FakeChannels":
        return self

    def execute(self) -> dict:
        return {"items": self.items}


class FakeYouTube:
    def __init__(
        self,
        captured: dict,
        channel_id: str = youtube_module.PYTHON_LODZ_CHANNEL_ID,
        title: str = "Python Łódź",
        channels_present: bool = True,
    ):
        self.captured = captured
        self.items = (
            [{"id": channel_id, "snippet": {"title": title}}]
            if channels_present
            else []
        )

    def liveBroadcasts(self) -> FakeBroadcasts:  # noqa: N802 — API google
        return FakeBroadcasts(self.captured)

    def channels(self) -> FakeChannels:
        return FakeChannels(self.items)


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


def test_create_live_refuses_a_channel_that_is_not_python_lodz(monkeypatch):
    """Token w `.yt_token.json` należy do konta, które autoryzowało się pierwsze.

    Incydent 21.09.2026: live #66 wylądował na prywatnym kanale Grzegorza. Zanim
    cokolwiek powstanie, sprawdzamy ID kanału — handle bywa pusty na kontach brandowych.
    """
    captured: dict = {}
    monkeypatch.setattr(
        youtube_module,
        "build",
        lambda *a, **k: FakeYouTube(
            captured, channel_id="UC9ePkxRdiwCDCXdCHt6mq7g", title="Grzegorz Kocjan"
        ),
    )
    monkeypatch.setattr(YouTubeLive, "_get_credentials", lambda self: object())
    start = datetime.datetime(2026, 9, 30, 17, 55, tzinfo=ZoneInfo("Europe/Warsaw"))

    with pytest.raises(youtube_module.WrongYouTubeChannelError) as error:
        YouTubeLive().create_live(title="Python Łódź #66", start=start)

    message = str(error.value)
    assert "Grzegorz Kocjan" in message
    assert youtube_module.PYTHON_LODZ_CHANNEL_ID in message
    assert ".yt_token.json" in message
    assert captured == {}, "nic nie może powstać na obcym kanale"


def test_create_live_refuses_a_token_without_any_channel(monkeypatch):
    captured: dict = {}
    monkeypatch.setattr(
        youtube_module,
        "build",
        lambda *a, **k: FakeYouTube(captured, channels_present=False),
    )
    monkeypatch.setattr(YouTubeLive, "_get_credentials", lambda self: object())
    start = datetime.datetime(2026, 9, 30, 17, 55, tzinfo=ZoneInfo("Europe/Warsaw"))

    with pytest.raises(youtube_module.WrongYouTubeChannelError):
        YouTubeLive().create_live(title="Python Łódź #66", start=start)

    assert captured == {}
