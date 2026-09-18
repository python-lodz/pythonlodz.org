from pathlib import Path

import pytest

from pyldz.models import MeetupRow, TalkRow
from pyldz.preflight import Severity, build_preflight


@pytest.fixture
def data_dir(tmp_path) -> Path:
    data = tmp_path / "data"
    (data / "locations").mkdir(parents=True)
    (data / "locations" / "indiebi.yaml").write_text(
        "name_pl: IndieBI\nname_en: IndieBI\n", encoding="utf-8"
    )
    (data / "sponsors").mkdir()
    (data / "sponsors" / "indiebi.yaml").write_text("name: IndieBI\n", encoding="utf-8")
    (data / "speakers").mkdir()
    return data


def meetup_row(**overrides) -> MeetupRow:
    defaults = {
        "meetup_id": "66",
        "type": "talks",
        "date": "2026-09-30",
        "location": "indiebi",
        "enabled": "TRUE",
        "meetup_url": "https://www.meetup.com/python-lodz/events/1/",
        "feedback_url": "https://forms.gle/1",
        "livestream_id": "abc123",
        "sponsors": "indiebi",
        "language": "PL",
    }
    return MeetupRow.model_validate({**defaults, **overrides})


def talk_row(**overrides) -> TalkRow:
    defaults = {
        "meetup_id": "66",
        "first_name": "Jan",
        "last_name": "Kowalski",
        "bio": "Bio prelegenta",
        "photo_url": "https://drive.google.com/open?id=" + "x" * 25,
        "talk_title": "Tytuł prelekcji",
        "talk_description": "Opis prelekcji",
        "language": "PL",
        "talk_title_en": "Talk title",
        "facebook_url": "",
        "linkedin_url": "",
        "youtube_url": "",
        "other_urls": "",
        "order": "1",
    }
    return TalkRow.model_validate({**defaults, **overrides})


def fields(report, severity: Severity) -> list[str]:
    return [f.field for f in report.findings if f.severity is severity]


def test_complete_meetup_has_nothing_blocking(data_dir):
    report = build_preflight(
        meetup_row(),
        [talk_row(), talk_row(first_name="Anna", order="2")],
        data_dir,
    )

    assert report.has_errors is False
    assert fields(report, Severity.ERROR) == []
    assert fields(report, Severity.WARN) == []
    assert report.meetup_id == "66"
    assert len(report.talks) == 2


def test_missing_signup_link_is_a_warning(data_dir):
    report = build_preflight(meetup_row(meetup_url=""), [talk_row()], data_dir)

    assert "meetup_url" in fields(report, Severity.WARN)
    assert report.has_errors is False


def test_unknown_location_blocks_generation(data_dir):
    report = build_preflight(meetup_row(location="nieznane"), [talk_row()], data_dir)

    assert "location" in fields(report, Severity.ERROR)
    assert report.has_errors is True


def test_summer_edition_blocks_generation(data_dir):
    report = build_preflight(meetup_row(type="summer_edition"), [talk_row()], data_dir)

    assert "type" in fields(report, Severity.ERROR)
    assert any("ręcznie" in f.message for f in report.findings)


def test_disabled_meetup_blocks_generation(data_dir):
    report = build_preflight(meetup_row(enabled="FALSE"), [talk_row()], data_dir)

    assert "enabled" in fields(report, Severity.ERROR)


def test_incomplete_submission_is_reported_per_talk(data_dir):
    report = build_preflight(
        meetup_row(feedback_url="", livestream_id=""),
        [
            talk_row(photo_url="", talk_title_en="", order=""),
            talk_row(first_name="Anna", bio="", talk_description="", order=""),
        ],
        data_dir,
    )

    warns = fields(report, Severity.WARN)
    infos = fields(report, Severity.INFO)
    assert "photo_url" in warns
    assert "bio" in warns
    assert "talk_description" in warns
    assert "talk_title_en" in infos
    assert "order" in infos
    assert "feedback_url" in infos
    assert "livestream_id" in infos


def test_unknown_sponsor_is_a_warning(data_dir):
    report = build_preflight(
        meetup_row(sponsors="indiebi, nieznany"), [talk_row()], data_dir
    )

    assert "sponsors" in fields(report, Severity.WARN)


def test_missing_instagram_handle_is_reported_for_social_tagging(data_dir):
    report = build_preflight(meetup_row(), [talk_row()], data_dir)
    assert "instagram" in fields(report, Severity.INFO)

    (data_dir / "speakers" / "jan-kowalski.yaml").write_text(
        'name: "Jan Kowalski"\ninstagram: "jan"\nsocial: []\n', encoding="utf-8"
    )
    report = build_preflight(meetup_row(), [talk_row()], data_dir)
    assert "instagram" not in fields(report, Severity.INFO)


def test_meetup_without_talks_is_a_warning(data_dir):
    report = build_preflight(meetup_row(), [], data_dir)

    assert "talks" in fields(report, Severity.WARN)


def test_report_renders_for_humans_and_for_agents(data_dir):
    report = build_preflight(meetup_row(meetup_url=""), [talk_row()], data_dir)

    text = report.to_text()
    assert "#66" in text
    assert "2026-09-30" in text
    assert "Tytuł prelekcji" in text
    assert "meetup_url" in text

    payload = report.model_dump(mode="json")
    assert payload["meetup_id"] == "66"
    assert payload["talks"][0]["title"] == "Tytuł prelekcji"
    assert payload["findings"][0]["severity"] in {"error", "warn", "info"}
