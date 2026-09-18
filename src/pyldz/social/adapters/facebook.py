"""Facebook Page adapter (Graph API)."""

import logging

import requests

log = logging.getLogger(__name__)

GRAPH_API = "https://graph.facebook.com/v23.0"


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
        response.raise_for_status()
        data = response.json()
        post_id = data.get("post_id") or data["id"]
        log.info(f"Facebook published: {post_id}")
        return post_id
