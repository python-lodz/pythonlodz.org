"""Mechanical per-platform transforms of the canonical post text (spec §6)."""

import re

from pyldz.social.models import Channel, Post

IG_HASHTAGS = "#python #pythonlodz #lodz #meetup #itlodz #programowanie"
IG_LINK_LINE = "🔗 Link w bio → pythonlodz.org"

_URL_RE = re.compile(r"https?://\S+")


def render_text(post: Post, channel: Channel) -> str:
    if channel in post.overrides:
        return post.overrides[channel]
    if channel == Channel.INSTAGRAM:
        return _instagram_text(post.text)
    return post.text


def _instagram_text(text: str) -> str:
    """Links are not clickable on IG: fold link lines into one 'link in bio' line."""
    lines: list[str] = []
    link_line_added = False
    for line in text.splitlines():
        if _URL_RE.search(line):
            if not link_line_added:
                lines.append(IG_LINK_LINE)
                link_line_added = True
            continue
        lines.append(line)
    return "\n".join(lines).strip() + f"\n\n{IG_HASHTAGS}"
