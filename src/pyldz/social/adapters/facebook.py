"""Facebook Page adapter (Graph API)."""

import logging

import requests

log = logging.getLogger(__name__)

GRAPH_API = "https://graph.facebook.com/v23.0"


class MetaGraphError(Exception):
    """Błąd z Graph API wraz z treścią odpowiedzi — sam status HTTP nic nie mówi."""


def raise_for_graph_error(response) -> None:
    """Zamień błąd HTTP na komunikat z powodem podanym przez Metę.

    Graph zwraca powód (code, subkod, typ, fbtrace_id) w ciele odpowiedzi, a
    `raise_for_status()` go gubi — w logach CI zostaje samo „403 Forbidden",
    z którego nie wynika, czy to wygasły token, brak uprawnienia, czy zła strona.
    """
    try:
        response.raise_for_status()
    except requests.HTTPError as http_error:
        try:
            error = response.json().get("error", {})
        except ValueError:
            error = {}

        if not error:
            raise MetaGraphError(
                f"{http_error} (brak szczegółów w ciele)"
            ) from http_error

        parts = [
            f"HTTP {response.status_code}",
            f"code {error.get('code')}",
        ]
        if error.get("error_subcode"):
            parts.append(f"subcode {error['error_subcode']}")
        parts.append(str(error.get("type")))
        parts.append(str(error.get("message")))
        if error.get("fbtrace_id"):
            parts.append(f"fbtrace_id {error['fbtrace_id']}")
        raise MetaGraphError(" | ".join(parts)) from http_error


def page_access_token(page_id: str, token: str) -> str:
    """Zamień token System Usera na token STRONY.

    Graph odmawia publikacji tokenem System Usera nawet z pełnym zestawem zakresów
    i zwraca mylące „(#200) The permission(s) publish_actions are not available"
    (uprawnienie skasowane w 2018). Publikować wolno tokenem strony, który Graph
    oddaje w polu `access_token` samej strony. Gdy się nie da — zwracamy token
    wejściowy, żeby zachowanie degradowało się do poprzedniego zamiast wybuchać.
    """
    try:
        response = requests.get(
            f"{GRAPH_API}/{page_id}",
            params={"fields": "access_token", "access_token": token},
            timeout=30,
        )
        payload = response.json()
    except (requests.RequestException, ValueError) as error:  # pragma: no cover — sieć
        log.warning(f"Nie udało się pobrać tokena strony: {type(error).__name__}")
        return token

    page_token = payload.get("access_token")
    if not page_token:
        error = payload.get("error", {})
        log.warning(
            "Strona nie oddała tokena publikacyjnego"
            + (f": code {error.get('code')} {error.get('message')}" if error else "")
            + " — publikuję tokenem z konfiguracji."
        )
        return token

    return page_token


class FacebookAdapter:
    def __init__(self, page_id: str, access_token: str):
        self.page_id = page_id
        self.access_token = access_token

    def publish(self, text: str, image_url: str | None = None) -> str:
        if image_url is not None:
            endpoint = f"{GRAPH_API}/{self.page_id}/photos"
            payload = {
                "url": image_url,
                "message": text,
                "access_token": self.access_token,
            }
        else:
            endpoint = f"{GRAPH_API}/{self.page_id}/feed"
            payload = {"message": text, "access_token": self.access_token}
        response = requests.post(endpoint, data=payload, timeout=60)
        raise_for_graph_error(response)
        data = response.json()
        post_id = data.get("post_id") or data["id"]
        log.info(f"Facebook published: {post_id}")
        return post_id
