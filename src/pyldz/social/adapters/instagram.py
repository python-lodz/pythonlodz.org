"""Instagram Business adapter (Graph API: container -> status -> media_publish)."""

import json
import logging
import time

import requests

from pyldz.social.adapters.facebook import MetaGraphError, raise_for_graph_error

log = logging.getLogger(__name__)

GRAPH_API = "https://graph.facebook.com/v23.0"

READY = "FINISHED"
DEAD_ENDS = {"ERROR", "EXPIRED"}


class InstagramAdapter:
    def __init__(
        self,
        ig_user_id: str,
        access_token: str,
        poll_interval: float = 3.0,
        poll_timeout: float = 120.0,
    ):
        self.ig_user_id = ig_user_id
        self.access_token = access_token
        self.poll_interval = poll_interval
        self.poll_timeout = poll_timeout

    def publish(
        self, caption: str, image_url: str, user_tags: list[str] | None = None
    ) -> str:
        payload = {
            "image_url": image_url,
            "caption": caption,
            "access_token": self.access_token,
        }
        if user_tags:
            payload["user_tags"] = json.dumps(
                [{"username": username, "x": 0.5, "y": 0.8} for username in user_tags]
            )
        container = requests.post(
            f"{GRAPH_API}/{self.ig_user_id}/media", data=payload, timeout=60
        )
        raise_for_graph_error(container)
        creation_id = container.json()["id"]
        log.info(f"Instagram container: {creation_id}")

        self._wait_until_ready(creation_id)

        published = requests.post(
            f"{GRAPH_API}/{self.ig_user_id}/media_publish",
            data={"creation_id": creation_id, "access_token": self.access_token},
            timeout=60,
        )
        raise_for_graph_error(published)
        media_id = published.json()["id"]
        log.info(f"Instagram published: {media_id}")
        return media_id

    def _wait_until_ready(self, creation_id: str) -> None:
        """Czekaj, aż Meta przetworzy kontener.

        `POST /media` oddaje ID, zanim media są gotowe — publikacja wysłana od razu
        dostaje 400 z code 9007 / subcode 2207027 „Media ID is not available", co
        brzmi jak zły identyfikator, a znaczy „jeszcze nie przetworzone". Pomiar
        22.09.2026: kontener był IN_PROGRESS jeszcze 0,5 s po odpowiedzi POST-a
        i osiągnął FINISHED dopiero po ~2,5 s.
        """
        deadline = time.monotonic() + self.poll_timeout
        while True:
            response = requests.get(
                f"{GRAPH_API}/{creation_id}",
                params={
                    "fields": "status_code,status",
                    "access_token": self.access_token,
                },
                timeout=30,
            )
            raise_for_graph_error(response)
            state = response.json()
            status_code = state.get("status_code")

            if status_code == READY:
                return
            if status_code in DEAD_ENDS:
                raise MetaGraphError(
                    f"Kontener {creation_id}: {status_code} | {state.get('status')}"
                )
            if time.monotonic() >= deadline:
                raise MetaGraphError(
                    f"Kontener {creation_id} nie osiągnął {READY} w "
                    f"{self.poll_timeout:.0f}s (ostatni stan: {status_code})"
                )
            time.sleep(self.poll_interval)
