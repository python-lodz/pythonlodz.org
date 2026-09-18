"""Discord webhook adapter."""

import json
import logging
from pathlib import Path

import requests

log = logging.getLogger(__name__)

MAX_CONTENT_LENGTH = 2000


def split_content(text: str, limit: int = MAX_CONTENT_LENGTH) -> list[str]:
    """Split text into <=limit chunks at paragraph boundaries."""
    if len(text) <= limit:
        return [text]
    chunks: list[str] = []
    current = ""
    for paragraph in text.split("\n\n"):
        candidate = f"{current}\n\n{paragraph}" if current else paragraph
        if len(candidate) > limit and current:
            chunks.append(current)
            current = paragraph
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


class DiscordAdapter:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def publish(self, text: str, image_path: Path | None = None) -> str | None:
        message_id: str | None = None
        for i, chunk in enumerate(split_content(text)):
            if i == 0 and image_path is not None:
                with image_path.open("rb") as image_file:
                    response = requests.post(
                        f"{self.webhook_url}?wait=true",
                        data={"payload_json": json.dumps({"content": chunk})},
                        files={"file": (image_path.name, image_file, "image/png")},
                        timeout=60,
                    )
            else:
                response = requests.post(
                    f"{self.webhook_url}?wait=true",
                    json={"content": chunk},
                    timeout=30,
                )
            response.raise_for_status()
            message_id = response.json()["id"]
        log.info(f"Discord published, last message id: {message_id}")
        return message_id
