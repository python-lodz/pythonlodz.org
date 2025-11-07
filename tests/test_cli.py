from datetime import date
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from pyldz.main import app
from pyldz.models import Language, Meetup, MeetupStatus, MultiLanguage, Talk


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
def mock_repository():
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
        result = runner.invoke(app, ["--output-dir", str(output_dir)])

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

        result = runner.invoke(app)

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
