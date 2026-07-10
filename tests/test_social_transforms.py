"""Tests for mechanical platform transforms (spec §6)."""

from pyldz.social.models import Channel, Post
from pyldz.social.transforms import IG_HASHTAGS, IG_LINK_LINE, render_text

CANONICAL = """\
☀️ Wakacyjna edycja wraca! Prowadzi @grzegorz.

➡️ Strona: https://pythonlodz.org/spotkania/65/
📝 Formularz: https://forms.example/lt

Do zobaczenia!"""


def make_post(**overrides):
    return Post(id="save-the-date", text=CANONICAL, overrides=overrides)


def test_facebook_and_discord_keep_canonical_text():
    post = make_post()
    assert render_text(post, Channel.FACEBOOK) == CANONICAL
    assert render_text(post, Channel.DISCORD) == CANONICAL


def test_instagram_replaces_link_lines_and_appends_hashtags():
    result = render_text(make_post(), Channel.INSTAGRAM)
    assert "https://" not in result
    assert result.count(IG_LINK_LINE) == 1
    assert result.endswith(IG_HASHTAGS)
    assert "@grzegorz" in result  # handle prelegenta zostaje


def test_override_wins_over_transform():
    post = make_post(**{Channel.INSTAGRAM: "własny tekst IG"})
    assert render_text(post, Channel.INSTAGRAM) == "własny tekst IG"
