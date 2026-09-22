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


class FakeErrorResponse:
    """Odpowiedź Graph API z błędem — status 403 i szczegóły w ciele."""

    status_code = 403

    def __init__(self, payload: dict):
        self._payload = payload

    def raise_for_status(self) -> None:
        import requests

        raise requests.HTTPError(f"{self.status_code} Client Error: Forbidden")

    def json(self) -> dict:
        return self._payload


@pytest.fixture
def graph_error(monkeypatch):
    """Podstaw odpowiedź błędu Graph API pod oba adaptery Meta."""

    def install(payload: dict) -> None:
        def fake_post(url, **kwargs):
            return FakeErrorResponse(payload)

        import pyldz.social.adapters.facebook as facebook_module
        import pyldz.social.adapters.instagram as instagram_module

        monkeypatch.setattr(facebook_module.requests, "post", fake_post)
        monkeypatch.setattr(instagram_module.requests, "post", fake_post)

    return install


GRAPH_403 = {
    "error": {
        "message": "(#200) If posting to a group, requires app being installed in the group",
        "type": "OAuthException",
        "code": 200,
        "fbtrace_id": "AbCdEf123",
    }
}


def test_facebook_error_carries_graph_details(graph_error):
    from pyldz.social.adapters.facebook import FacebookAdapter, MetaGraphError

    graph_error(GRAPH_403)
    adapter = FacebookAdapter("123", "token")

    with pytest.raises(MetaGraphError) as error:
        adapter.publish("tekst", image_url="https://example.com/a.png")

    message = str(error.value)
    assert "403" in message
    assert "code 200" in message
    assert "OAuthException" in message
    assert "AbCdEf123" in message
    assert "token" not in message, "token nigdy nie może wyciec do logów"


def test_instagram_error_carries_graph_details(graph_error):
    from pyldz.social.adapters.facebook import MetaGraphError
    from pyldz.social.adapters.instagram import InstagramAdapter

    graph_error(GRAPH_403)
    adapter = InstagramAdapter("999", "token")

    with pytest.raises(MetaGraphError) as error:
        adapter.publish("podpis", image_url="https://example.com/a.png")

    assert "code 200" in str(error.value)


def test_graph_error_survives_a_body_that_is_not_json(graph_error):
    from pyldz.social.adapters.facebook import FacebookAdapter, MetaGraphError

    class NotJson(FakeErrorResponse):
        def json(self):
            raise ValueError("no json")

    def fake_post(url, **kwargs):
        return NotJson({})

    import pyldz.social.adapters.facebook as facebook_module

    monkeypatch_target = facebook_module.requests
    original = monkeypatch_target.post
    monkeypatch_target.post = fake_post
    try:
        with pytest.raises(MetaGraphError) as error:
            FacebookAdapter("123", "token").publish("tekst")
        assert "403" in str(error.value)
    finally:
        monkeypatch_target.post = original
