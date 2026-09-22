"""Publikacja na stronie wymaga tokena STRONY, nie tokena System Usera.

Incydent 22.09.2026: token miał komplet zakresów (`pages_manage_posts`,
`instagram_content_publish`), a Graph i tak odbijał publikację błędem
„(#200) The permission(s) publish_actions are not available" — mylącym, bo
`publish_actions` zniknęło z API w 2018 roku.
"""

import pytest

from pyldz.social.adapters.facebook import page_access_token
from pyldz.social.config import SocialSettings


@pytest.fixture
def graph_get(monkeypatch):
    def install(status: int, payload: dict) -> list[dict]:
        asked: list[dict] = []

        class Response:
            status_code = status

            def json(self) -> dict:
                return payload

        def fake_get(url, params=None, timeout=None):
            asked.append({"url": url, "params": params or {}})
            return Response()

        import pyldz.social.adapters.facebook as module

        monkeypatch.setattr(module.requests, "get", fake_get)
        return asked

    return install


def test_exchanges_system_user_token_for_page_token(graph_get):
    asked = graph_get(200, {"id": "111", "access_token": "TOKEN-STRONY"})

    assert page_access_token("111", "TOKEN-SYSTEM-USERA") == "TOKEN-STRONY"
    assert asked[0]["url"].endswith("/111")
    assert asked[0]["params"]["fields"] == "access_token"


def test_falls_back_to_the_given_token_when_page_has_none(graph_get):
    graph_get(200, {"id": "111"})

    assert page_access_token("111", "TOKEN-SYSTEM-USERA") == "TOKEN-SYSTEM-USERA"


def test_falls_back_instead_of_crashing_when_graph_refuses(graph_get):
    graph_get(403, {"error": {"code": 200, "message": "brak dostępu"}})

    assert page_access_token("111", "TOKEN-SYSTEM-USERA") == "TOKEN-SYSTEM-USERA"


def test_both_meta_adapters_get_the_page_token(graph_get, monkeypatch):
    graph_get(200, {"id": "111", "access_token": "TOKEN-STRONY"})
    from pyldz.social.cli import _build_adapters
    from pyldz.social.models import Channel

    adapters = _build_adapters(
        SocialSettings(
            meta_page_id="111",
            meta_access_token="TOKEN-SYSTEM-USERA",
            ig_user_id="222",
            discord_webhook_url=None,
        )
    )

    assert adapters[Channel.FACEBOOK].access_token == "TOKEN-STRONY"
    assert adapters[Channel.INSTAGRAM].access_token == "TOKEN-STRONY"
