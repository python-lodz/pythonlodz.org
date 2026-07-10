"""Tests for the social/posts.md parser."""

from pyldz.social.models import Channel
from pyldz.social.posts_md import parse_posts_md

SAMPLE = """\
# Posty — Python Łódź #65

Metryczka dla ludzi — parser ma to zignorować.

## post: save-the-date

☀️ Wakacyjna edycja wraca!

Zapisy: https://pythonlodz.org/spotkania/65/

### override: discord

@everyone ☀️ Wakacyjna edycja wraca!

## post: last-call

⚡ Ostatnie dni na zgłoszenia Lightning Talków!
"""


def test_parses_all_posts():
    posts = parse_posts_md(SAMPLE)
    assert set(posts) == {"save-the-date", "last-call"}


def test_canonical_text_is_stripped_block():
    posts = parse_posts_md(SAMPLE)
    assert posts["save-the-date"].text == (
        "☀️ Wakacyjna edycja wraca!\n\nZapisy: https://pythonlodz.org/spotkania/65/"
    )
    assert posts["last-call"].text == "⚡ Ostatnie dni na zgłoszenia Lightning Talków!"


def test_override_is_attached_to_platform():
    posts = parse_posts_md(SAMPLE)
    assert posts["save-the-date"].overrides == {
        Channel.DISCORD: "@everyone ☀️ Wakacyjna edycja wraca!"
    }
    assert posts["last-call"].overrides == {}


def test_preamble_before_first_post_is_ignored():
    posts = parse_posts_md("intro bez postów\n")
    assert posts == {}
