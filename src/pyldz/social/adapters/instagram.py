"""Instagram Business adapter (Graph API: container -> media_publish)."""

import json
import logging

import requests

from pyldz.social.adapters.facebook import raise_for_graph_error

log = logging.getLogger(__name__)

GRAPH_API = "https://graph.facebook.com/v23.0"


class InstagramAdapter:
    def __init__(self, ig_user_id: str, access_token: str):
        self.ig_user_id = ig_user_id
        self.access_token = access_token

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

        published = requests.post(
            f"{GRAPH_API}/{self.ig_user_id}/media_publish",
            data={"creation_id": creation_id, "access_token": self.access_token},
            timeout=60,
        )
        raise_for_graph_error(published)
        media_id = published.json()["id"]
        log.info(f"Instagram published: {media_id}")
        return media_id
