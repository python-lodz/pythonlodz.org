from datetime import date
from pathlib import Path
from unittest.mock import Mock

import pytest

from pyldz.hugo_generator import HugoMeetupGenerator, MeetupGenerationError
from pyldz.models import Language, Meetup, MeetupType, MultiLanguage


def make_meetup(meetup_id: str = "58", **overrides) -> Meetup:
    defaults = {
        "meetup_id": meetup_id,
        "title": f"Meetup #{meetup_id}",
        "date": date(2026, 9, 30),
        "time": "18:00",
        "location": MultiLanguage(pl="IndieBI", en="IndieBI"),
        "language": Language.PL,
        "talks": [],
        "sponsors": [],
    }
    return Meetup(**{**defaults, **overrides})


def test_meetup_carries_its_type_from_the_sheet():
    assert make_meetup().type is MeetupType.TALKS


def test_generate_meetup_refuses_summer_edition(tmp_path):
    # Edycje letnie mają ręcznie pisany index.md (wzór #59/#65) — patrz tasks/lessons.md.
    repository = Mock()
    repository.get_meetup_by_id.return_value = make_meetup(
        "65", type=MeetupType.SUMMER_EDITION
    )
    generator = HugoMeetupGenerator(tmp_path)

    with pytest.raises(MeetupGenerationError, match="ręcznie"):
        generator.generate_meetup("65", repository)


def test_generate_meetup_explains_a_missing_meetup(tmp_path):
    repository = Mock()
    repository.get_meetup_by_id.return_value = None
    generator = HugoMeetupGenerator(tmp_path)

    with pytest.raises(MeetupGenerationError, match="arkusz"):
        generator.generate_meetup("99", repository)


def test_generate_all_meetups_skips_summer_editions(tmp_path, monkeypatch):
    repository = Mock()
    repository.get_all_enabled_meetups.return_value = [
        make_meetup("58"),
        make_meetup("65", type=MeetupType.SUMMER_EDITION),
    ]
    repository.get_speakers_for_meetup.return_value = []
    generator = HugoMeetupGenerator(tmp_path)

    generated: list[str] = []

    def fake_create(meetup, speakers) -> Path:
        generated.append(meetup.meetup_id)
        return tmp_path / f"{meetup.meetup_id}.md"

    monkeypatch.setattr(generator, "create_meetup_file", fake_create)

    files = generator.generate_all_meetups(repository)

    assert generated == ["58"]
    assert len(files) == 1
