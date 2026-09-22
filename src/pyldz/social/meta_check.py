"""Diagnostyka tokena Meta — co token faktycznie widzi.

Powstało po incydencie 22.09.2026: publikacja na Facebooku padła z „403 Forbidden"
bez żadnej wskazówki, czy problem jest w tokenie, uprawnieniach, czy w ID strony.
Komenda `pyldz social check-meta` odpowiada na to pytanie bez publikowania czegokolwiek
(same odczyty GET) i bez pokazywania tokena w wyjściu.
"""

import logging

import requests
from pydantic import BaseModel

from pyldz.social.config import SocialSettings

log = logging.getLogger(__name__)

GRAPH_API = "https://graph.facebook.com/v23.0"
TIMEOUT = 30


class CheckResult(BaseModel):
    name: str
    ok: bool
    detail: str


def _graph_get(
    path: str, token: str, fields: str | None = None
) -> tuple[bool, str, dict]:
    params = {"access_token": token}
    if fields:
        params["fields"] = fields

    try:
        response = requests.get(f"{GRAPH_API}/{path}", params=params, timeout=TIMEOUT)
    except requests.RequestException as error:  # pragma: no cover — sieć
        return False, f"połączenie nie wyszło: {type(error).__name__}", {}

    try:
        payload = response.json()
    except ValueError:
        payload = {}

    if response.status_code >= 400 or "error" in payload:
        error = payload.get("error", {})
        bits = [f"HTTP {response.status_code}"]
        if error.get("code") is not None:
            bits.append(f"code {error['code']}")
        if error.get("error_subcode"):
            bits.append(f"subcode {error['error_subcode']}")
        if error.get("type"):
            bits.append(str(error["type"]))
        if error.get("message"):
            bits.append(str(error["message"]))
        return False, " | ".join(bits), payload

    return True, "", payload


def run_meta_checks(settings: SocialSettings) -> list[CheckResult]:
    """Odczyty, które rozdzielają „martwy token" od „brak uprawnień do strony"."""
    missing = [
        name
        for name, value in (
            ("META_ACCESS_TOKEN", settings.meta_access_token),
            ("META_PAGE_ID", settings.meta_page_id),
        )
        if not value
    ]
    if missing:
        return [
            CheckResult(
                name="konfiguracja",
                ok=False,
                detail=f"brakuje zmiennych: {', '.join(missing)}",
            )
        ]

    token = settings.meta_access_token
    page_id = settings.meta_page_id
    checks: list[CheckResult] = []

    ok, detail, payload = _graph_get("me", token, fields="id,name")
    checks.append(
        CheckResult(
            name="tożsamość tokena (GET /me)",
            ok=ok,
            detail=detail
            or f"{payload.get('name', '?')} (id {payload.get('id', '?')})",
        )
    )

    ok, detail, page = _graph_get(
        page_id, token, fields="id,name,instagram_business_account"
    )
    checks.append(
        CheckResult(
            name=f"strona (GET /{page_id[:4]}…)",
            ok=ok,
            detail=detail or f"{page.get('name', '?')} (id {page.get('id', '?')})",
        )
    )

    linked = (page.get("instagram_business_account") or {}).get("id")
    if settings.ig_user_id:
        matches = linked == settings.ig_user_id
        checks.append(
            CheckResult(
                name="powiązanie Instagrama ze stroną",
                ok=bool(linked) and matches,
                detail=(
                    "zgodne z IG_USER_ID"
                    if matches
                    else f"strona wskazuje na konto IG {linked!r}, a IG_USER_ID to {settings.ig_user_id!r}"
                ),
            )
        )

        ok, detail, ig = _graph_get(settings.ig_user_id, token, fields="id,username")
        checks.append(
            CheckResult(
                name="konto Instagram (GET /IG_USER_ID)",
                ok=ok,
                detail=detail or f"@{ig.get('username', '?')}",
            )
        )

    return checks


def format_report(checks: list[CheckResult]) -> str:
    lines = []
    for check in checks:
        mark = "OK  " if check.ok else "BŁĄD"
        lines.append(f"[{mark}] {check.name}: {check.detail}")
    if all(c.ok for c in checks):
        lines.append("")
        lines.append(
            "Odczyty przechodzą, więc token żyje i widzi stronę. Jeśli publikacja "
            "nadal zwraca 403, brakuje uprawnienia do pisania (pages_manage_posts) "
            "albo System User nie ma roli na stronie — patrz docs/social/setup.md."
        )
    return "\n".join(lines)
