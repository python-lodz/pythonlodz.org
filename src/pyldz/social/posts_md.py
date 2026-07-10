"""Parser for social/posts.md — canonical post texts with per-platform overrides."""

import re

from pyldz.social.models import Channel, Post

_POST_RE = re.compile(r"^## post: ([a-z0-9][a-z0-9-]*)\s*$")
_OVERRIDE_RE = re.compile(r"^### override: (facebook|instagram|discord|linkedin)\s*$")


def parse_posts_md(content: str) -> dict[str, Post]:
    posts: dict[str, Post] = {}
    current_id: str | None = None
    current_channel: Channel | None = None
    buffer: list[str] = []

    def flush() -> None:
        nonlocal buffer
        if current_id is not None:
            text = "\n".join(buffer).strip()
            if current_channel is None:
                posts[current_id] = Post(id=current_id, text=text)
            else:
                posts[current_id].overrides[current_channel] = text
        buffer = []

    for line in content.splitlines():
        post_match = _POST_RE.match(line)
        override_match = _OVERRIDE_RE.match(line)
        if post_match:
            flush()
            current_id = post_match.group(1)
            current_channel = None
        elif override_match:
            flush()
            current_channel = Channel(override_match.group(1))
        else:
            buffer.append(line)
    flush()
    return posts
