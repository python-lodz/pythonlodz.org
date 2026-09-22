"""Diagnostyka tokena Meta — po incydencie 403 na ogloszenie:facebook (22.09.2026)."""

import pytest

from pyldz.social.config import SocialSettings
from pyldz.social.meta_check import run_meta_checks


@pytest.fixture
def graph(monkeypatch):
    """Podstaw odpowiedzi Graph API per ścieżka URL-a."""

    def install(responses: dict[str, tuple[int, dict]]) -> list[str]:
        asked: list[str] = []

        class Response:
            def __init__(self, status: int, payload: dict):
                self.status_code = status
                self._payload = payload

            def json(self) -> dict:
                return self._payload

        def fake_get(url, params=None, timeout=None):
            asked.append(url)
            for fragment, (status, payload) in responses.items():
                if fragment in url:
                    return Response(status, payload)
            return Response(404, {"error": {"code": 803, "message": "not found"}})

        import pyldz.social.meta_check as module

        monkeypatch.setattr(module.requests, "get", fake_get)
        return asked

    return install


def settings() -> SocialSettings:
    return SocialSettings(
        meta_page_id="111",
        meta_access_token="sekret",
        ig_user_id="222",
    )


def test_all_green_when_token_sees_page_and_instagram(graph):
    graph(
        {
            "/me": (200, {"id": "sys-1", "name": "pyldz system user"}),
            "/111": (
                200,
                {
                    "id": "111",
                    "name": "Python Łódź",
                    "instagram_business_account": {"id": "222"},
                },
            ),
            "/222": (200, {"id": "222", "username": "pythonlodz"}),
        }
    )

    checks = run_meta_checks(settings())

    assert all(c.ok for c in checks), [c for c in checks if not c.ok]
    assert any("Python Łódź" in c.detail for c in checks)


def test_dead_token_is_reported_with_graph_code(graph):
    graph(
        {
            "": (
                401,
                {
                    "error": {
                        "message": "Error validating access token: Session has expired",
                        "type": "OAuthException",
                        "code": 190,
                        "error_subcode": 463,
                    }
                },
            )
        }
    )

    checks = run_meta_checks(settings())

    assert not any(c.ok for c in checks)
    joined = " ".join(c.detail for c in checks)
    assert "190" in joined
    assert "463" in joined
    assert "sekret" not in joined, "token nie może trafić do raportu"


def test_instagram_mismatch_is_flagged(graph):
    graph(
        {
            "/me": (200, {"id": "sys-1", "name": "pyldz"}),
            "/111": (
                200,
                {
                    "id": "111",
                    "name": "Python Łódź",
                    "instagram_business_account": {"id": "999"},
                },
            ),
            "/222": (200, {"id": "222", "username": "pythonlodz"}),
        }
    )

    checks = run_meta_checks(settings())

    mismatch = [c for c in checks if not c.ok]
    assert mismatch, "niezgodne IG_USER_ID musi być błędem"
    assert "999" in mismatch[0].detail


def test_missing_settings_are_reported_instead_of_crashing(graph):
    graph({})
    empty = SocialSettings(meta_page_id=None, meta_access_token=None, ig_user_id=None)

    checks = run_meta_checks(empty)

    assert not checks[0].ok
    assert "META_ACCESS_TOKEN" in checks[0].detail
