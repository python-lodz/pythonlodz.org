"""Shared fixtures."""

from pathlib import Path

import pytest

POSTS_MD = """\
# Posty — Python Łódź #65

## post: save-the-date

☀️ Wakacyjna edycja wraca!

Zapisy: https://pythonlodz.org/spotkania/65/

### override: discord

@everyone ☀️ Wakacyjna edycja wraca!

## post: last-call

⚡ Ostatnie dni na zgłoszenia Lightning Talków!
Formularz: https://forms.example/lt
"""

SCHEDULE_YAML = """\
meetup: "65"
timezone: Europe/Warsaw
posts:
  - post: save-the-date
    channels: [facebook, instagram, discord, linkedin]
    scheduled: 2026-07-08 09:00:00
    image: images/final/save-the-date-4x5.png
    ig_tagged: [pythonlodz]
  - post: last-call
    channels: [facebook]
    scheduled: 2026-07-27 17:00:00
"""


@pytest.fixture
def social_content_dir(tmp_path: Path) -> Path:
    """Equivalent of page/content/spotkania with meetup 65 social/ artifacts."""
    social = tmp_path / "65" / "social"
    (social / "images" / "final").mkdir(parents=True)
    (social / "posts.md").write_text(POSTS_MD, encoding="utf-8")
    (social / "schedule.yaml").write_text(SCHEDULE_YAML, encoding="utf-8")
    (social / "images" / "final" / "save-the-date-4x5.png").write_bytes(b"\x89PNG")
    return tmp_path
