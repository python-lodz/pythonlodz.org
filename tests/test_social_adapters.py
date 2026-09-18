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
    import pyldz.social.adapters.facebook as facebook_module
    import pyldz.social.adapters.instagram as instagram_module

    monkeypatch.setattr(discord_module.requests, "post", fake_post)
    monkeypatch.setattr(facebook_module.requests, "post", fake_post)
    monkeypatch.setattr(instagram_module.requests, "post", fake_post)
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


def test_facebook_photo_post_uses_photos_endpoint(posted):
    from pyldz.social.adapters.facebook import FacebookAdapter

    adapter = FacebookAdapter("111", "token")
    post_id = adapter.publish("tekst", image_url="https://pythonlodz.org/g.png")
    assert post_id == "fb-1"
    assert posted[0]["url"] == "https://graph.facebook.com/v23.0/111/photos"
    assert posted[0]["data"] == {
        "url": "https://pythonlodz.org/g.png",
        "message": "tekst",
        "access_token": "token",
    }


def test_facebook_text_only_uses_feed_endpoint(posted):
    from pyldz.social.adapters.facebook import FacebookAdapter

    adapter = FacebookAdapter("111", "token")
    adapter.publish("sam tekst")
    assert posted[0]["url"] == "https://graph.facebook.com/v23.0/111/feed"
    assert posted[0]["data"] == {"message": "sam tekst", "access_token": "token"}


def test_instagram_container_then_publish(posted):
    from pyldz.social.adapters.instagram import InstagramAdapter

    adapter = InstagramAdapter("222", "token")
    media_id = adapter.publish(
        "caption", image_url="https://pythonlodz.org/g.png", user_tags=["speaker1"]
    )
    assert media_id == "msg-2"
    assert posted[0]["url"] == "https://graph.facebook.com/v23.0/222/media"
    assert posted[0]["data"]["image_url"] == "https://pythonlodz.org/g.png"
    assert posted[0]["data"]["caption"] == "caption"
    assert json.loads(posted[0]["data"]["user_tags"]) == [
        {"username": "speaker1", "x": 0.5, "y": 0.8}
    ]
    assert posted[1]["url"] == "https://graph.facebook.com/v23.0/222/media_publish"
    assert posted[1]["data"] == {"creation_id": "msg-1", "access_token": "token"}


def test_instagram_without_tags_omits_user_tags(posted):
    from pyldz.social.adapters.instagram import InstagramAdapter

    adapter = InstagramAdapter("222", "token")
    adapter.publish("caption", image_url="https://pythonlodz.org/g.png")
    assert "user_tags" not in posted[0]["data"]
