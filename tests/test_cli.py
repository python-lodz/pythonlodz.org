import json
from datetime import date
from io import BytesIO
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from PIL import Image
from typer.testing import CliRunner

from pyldz.main import app
from pyldz.models import (
    File,
    Language,
    Meetup,
    MeetupRow,
    MeetupStatus,
    MultiLanguage,
    Speaker,
    Talk,
    TalkRow,
)


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_config(tmp_path):
    with patch("pyldz.main.AppConfig") as mock:
        config_instance = Mock()
        config_instance.google_sheets = Mock()
        config_instance.hugo = Mock()
        config_instance.hugo.data_dir = tmp_path / "data"
        (config_instance.hugo.data_dir / "locations").mkdir(parents=True)
        mock.return_value = config_instance
        yield config_instance


@pytest.fixture
def sample_speaker():
    buf = BytesIO()
    Image.new("RGBA", (300, 300), (255, 0, 0, 255)).save(buf, format="PNG")
    return Speaker(
        id="john-doe",
        name="John Doe",
        bio="A developer",
        avatar=File(name="avatar.png", content=buf.getvalue()),
        social_links=[],
    )


@pytest.fixture
def mock_repository(sample_speaker):
    with patch("pyldz.main.GoogleSheetsRepository") as mock_repo_class:
        repo_instance = Mock()
        mock_repo_class.return_value = repo_instance

        sample_meetup = Meetup(
            meetup_id="58",
            title="Meetup #58",
            date=date(2025, 5, 28),
            time="18:00",
            location=MultiLanguage(
                pl="IndieBI, Piotrkowska 157A, budynek Hi Piotrkowska",
                en="IndieBI, Piotrkowska 157A, building Hi Piotrkowska",
            ),
            status=MeetupStatus.PUBLISHED,
            meetup_url="https://www.meetup.com/python-lodz/events/306971418/",
            feedback_url=None,
            livestream_id=None,
            language=Language.PL,
            talks=[
                Talk(
                    speaker_id="john-doe",
                    title="Example Talk",
                    description="Example description",
                    language=Language.PL,
                    title_en="Example Talk EN",
                    youtube_id=None,
                )
            ],
            sponsors=["indiebi", "sunscrapers"],
        )

        repo_instance.get_all_enabled_meetups.return_value = [sample_meetup]
        # HugoMeetupGenerator.generate_all_meetups sięga też po prelegentów
        # (get_speakers_for_meetup + fetch_talk_rows) — bez tych stubów
        # goły Mock trafia do create_meetup_file i wywala się na iteracji.
        repo_instance.fetch_talk_rows.return_value = []
        repo_instance.get_speakers_for_meetup.return_value = [sample_speaker]
        yield repo_instance


def test_cli_help(runner):
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.stdout


def test_fill_hugo_command(runner, mock_config, mock_repository, tmp_path):
    output_dir = tmp_path / "test_page"
    output_dir.mkdir()
    (output_dir / "content" / "spotkania").mkdir(parents=True)
    (output_dir / "assets" / "images").mkdir(parents=True)

    # Create a mock logo file
    logo_file = (
        output_dir / "assets" / "images" / "python_lodz_logo_transparent_border.png"
    )
    logo_file.write_bytes(b"fake image data")

    with patch("pyldz.main.GoogleSheetsAPI"):
        result = runner.invoke(app, ["generate", "--output-dir", str(output_dir)])

        assert result.exit_code == 0
        assert "Generating Hugo meetup files..." in result.stdout
        assert "Generated 1 meetup files:" in result.stdout

        # Check that files were created
        meetup_dir = output_dir / "content" / "spotkania" / "58"
        assert meetup_dir.exists()
        assert (meetup_dir / "index.md").exists()
        assert (meetup_dir / "featured.png").exists()

        # Check content of generated markdown
        content = (meetup_dir / "index.md").read_text()
        assert 'title: "Meetup #58"' in content
        assert "## Informacje" in content
        assert "Example Talk" in content


def test_fill_hugo_command_with_default_output_dir(
    runner, mock_config, mock_repository
):
    """Test fill-hugo command with default output directory."""
    with patch("pyldz.main.GoogleSheetsAPI"), patch(
        "pyldz.main.HugoMeetupGenerator"
    ) as mock_generator_class:
        mock_generator = Mock()
        mock_generator_class.return_value = mock_generator
        mock_generator.generate_all_meetups.return_value = [
            Path("page/content/spotkania/58/index.md")
        ]

        result = runner.invoke(app, ["generate"])

        assert result.exit_code == 0

        mock_generator_class.assert_called_once_with(Path("page"))


def test_invalid_command(runner):
    result = runner.invoke(app, ["invalid-command"])
    assert result.exit_code != 0
    assert (
        "No such command" in result.stdout
        or "invalid-command" in result.stdout
        or result.exit_code == 2
    )


@pytest.fixture
def sheet_data(mock_config):
    """Arkusz w formie, jaką widzi CLI: surowe wiersze + dane referencyjne w repo."""
    data_dir = mock_config.hugo.data_dir
    (data_dir / "locations" / "indiebi.yaml").write_text(
        "name_pl: IndieBI\nname_en: IndieBI\n", encoding="utf-8"
    )
    (data_dir / "sponsors").mkdir(parents=True)
    (data_dir / "sponsors" / "indiebi.yaml").write_text(
        "name: IndieBI\n", encoding="utf-8"
    )
    (data_dir / "speakers").mkdir(parents=True)

    def rows(**meetup_overrides):
        meetup = {
            "meetup_id": "66",
            "type": "talks",
            "date": "2026-09-30",
            "location": "indiebi",
            "enabled": "TRUE",
            "meetup_url": "",
            "feedback_url": "",
            "livestream_id": "",
            "sponsors": "indiebi",
            "language": "PL",
        }
        talk = {
            "meetup_id": "66",
            "first_name": "Jan",
            "last_name": "Kowalski",
            "bio": "Bio",
            "photo_url": "https://drive.google.com/open?id=" + "x" * 25,
            "talk_title": "Największe mity w pracy z kolejkami",
            "talk_description": "Opis",
            "language": "PL",
            "talk_title_en": "",
            "facebook_url": "",
            "linkedin_url": "",
            "youtube_url": "",
            "other_urls": "",
            "order": "",
        }
        return (
            [MeetupRow.model_validate({**meetup, **meetup_overrides})],
            [TalkRow.model_validate(talk)],
        )

    return rows


@pytest.fixture
def stub_repository(sheet_data):
    """Podstaw repozytorium zwracające surowe wiersze arkusza."""

    def build(**meetup_overrides):
        meetup_rows, talk_rows = sheet_data(**meetup_overrides)
        repo = Mock()
        repo.fetch_meetup_rows.return_value = meetup_rows
        repo.fetch_talk_rows.return_value = talk_rows
        return repo

    return build


def test_show_prints_sheet_data_and_missing_fields(runner, stub_repository):
    with patch("pyldz.main.GoogleSheetsAPI"), patch(
        "pyldz.main.GoogleSheetsRepository", return_value=stub_repository()
    ):
        result = runner.invoke(app, ["show", "66"])

    assert result.exit_code == 0
    assert "#66" in result.stdout
    assert "2026-09-30" in result.stdout
    assert "Największe mity w pracy z kolejkami" in result.stdout
    assert "meetup_url" in result.stdout


def test_show_json_is_machine_readable(runner, stub_repository):
    with patch("pyldz.main.GoogleSheetsAPI"), patch(
        "pyldz.main.GoogleSheetsRepository", return_value=stub_repository()
    ):
        result = runner.invoke(app, ["show", "66", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["meetup_id"] == "66"
    assert payload["date"] == "2026-09-30"
    assert payload["talks"][0]["speaker_id"] == "jan-kowalski"
    assert any(f["field"] == "meetup_url" for f in payload["findings"])


def test_show_explains_unknown_meetup(runner, stub_repository):
    repo = stub_repository()
    repo.fetch_meetup_rows.return_value = []

    with patch("pyldz.main.GoogleSheetsAPI"), patch(
        "pyldz.main.GoogleSheetsRepository", return_value=repo
    ):
        result = runner.invoke(app, ["show", "99"])

    assert result.exit_code == 1
    assert "arkusz" in result.stdout


def test_generate_refuses_a_meetup_with_blocking_findings(runner, stub_repository):
    with patch("pyldz.main.GoogleSheetsAPI"), patch(
        "pyldz.main.GoogleSheetsRepository",
        return_value=stub_repository(type="summer_edition"),
    ), patch("pyldz.main.HugoMeetupGenerator") as generator_class:
        result = runner.invoke(app, ["generate", "-m", "66"])

    assert result.exit_code == 1
    assert "ręcznie" in result.stdout
    generator_class.return_value.generate_meetup.assert_not_called()


def test_generate_reports_missing_fields_after_writing(
    runner, stub_repository, tmp_path
):
    with patch("pyldz.main.GoogleSheetsAPI"), patch(
        "pyldz.main.GoogleSheetsRepository", return_value=stub_repository()
    ), patch("pyldz.main.HugoMeetupGenerator") as generator_class:
        generator_class.return_value.generate_meetup.return_value = (
            tmp_path / "index.md"
        )
        result = runner.invoke(app, ["generate", "-m", "66"])

    assert result.exit_code == 0
    generator_class.return_value.generate_meetup.assert_called_once()
    assert "meetup_url" in result.stdout
