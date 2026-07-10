"""Tests for channel adapters (requests mocked)."""

import json
from pathlib import Path

import pytest

from pyldz.social.adapters.discord import DiscordAdapter, split_content


class FakeResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def raise_for_status(self) -> None:
        pass

    def json(self) -> dict:
        return self._payload


@pytest.fixture
def posted(monkeypatch):
    """Capture requests.post calls; return canned ids."""
    calls: list[dict] = []

    def fake_post(url, **kwargs):
        calls.append({"url": url, **kwargs})
        return FakeResponse({"id": f"msg-{len(calls)}", "post_id": f"fb-{len(calls)}"})

    import pyldz.social.adapters.discord as discord_module

    monkeypatch.setattr(discord_module.requests, "post", fake_post)
    return calls


def test_split_content_short_text_is_single_chunk():
    assert split_content("krótki") == ["krótki"]


def test_split_content_splits_on_paragraphs():
    text = "a" * 1500 + "\n\n" + "b" * 1500
    chunks = split_content(text)
    assert chunks == ["a" * 1500, "b" * 1500]


def test_discord_publishes_text_only(posted):
    adapter = DiscordAdapter("https://discord.example/webhook")
    message_id = adapter.publish("cześć")
    assert message_id == "msg-1"
    assert posted[0]["url"] == "https://discord.example/webhook?wait=true"
    assert posted[0]["json"] == {"content": "cześć"}


def test_discord_attaches_image_to_first_chunk(posted, tmp_path: Path):
    image = tmp_path / "grafika.png"
    image.write_bytes(b"\x89PNG")
    adapter = DiscordAdapter("https://discord.example/webhook")
    adapter.publish("cześć", image_path=image)
    assert "files" in posted[0]
    assert json.loads(posted[0]["data"]["payload_json"]) == {"content": "cześć"}
