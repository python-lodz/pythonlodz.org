from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from pyldz.main import app


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_config():
    """Mock configuration to avoid needing real credentials."""
    with patch("pyldz.main.AppConfig") as mock:
        config_instance = Mock()
        config_instance.google_sheets = Mock()
        mock.return_value = config_instance
        yield config_instance


@pytest.fixture
def mock_repository():
    """Mock repository with sample data."""
    with patch("pyldz.main.GoogleSheetsRepository") as mock_repo_class:
        repo_instance = Mock()
        mock_repo_class.return_value = repo_instance

        # Mock meetup data
        from datetime import date

        from pyldz.meetup import Language, Meetup, MeetupStatus, Talk

        sample_meetup = Meetup(
            meetup_id="58",
            title="Meetup #58",
            date=date(2025, 5, 28),
            time="18:00",
            location="indiebi",
            status=MeetupStatus.PUBLISHED,
            meetup_url="https://www.meetup.com/python-lodz/events/306971418/",
            feedback_url=None,
            livestream_id=None,
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
    """Test that CLI help works."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Python Łódź Meetup Management CLI" in result.stdout
    assert "dry-run" in result.stdout
    assert "fill-hugo" in result.stdout


def test_dry_run_command(runner, mock_config, mock_repository):
    """Test dry-run command."""
    with patch("pyldz.main.GoogleSheetsAPI"):
        result = runner.invoke(app, ["dry-run"])

        assert result.exit_code == 0
        assert "Python Łódź Meetup Data Fetcher" in result.stdout
        assert "Meetup #58" in result.stdout
        assert "Data fetch completed successfully!" in result.stdout


def test_fill_hugo_command(runner, mock_config, mock_repository, tmp_path):
    """Test fill-hugo command."""
    # Create a temporary directory structure
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
        result = runner.invoke(app, ["fill-hugo", "--output-dir", str(output_dir)])

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

        result = runner.invoke(app, ["fill-hugo"])

        assert result.exit_code == 0
        # Check that generator was called with default path
        mock_generator_class.assert_called_once_with(Path("page"))


def test_dry_run_help(runner):
    """Test dry-run command help."""
    result = runner.invoke(app, ["dry-run", "--help"])
    assert result.exit_code == 0
    assert "Display meetup data without generating files" in result.stdout


def test_fill_hugo_help(runner):
    """Test fill-hugo command help."""
    result = runner.invoke(app, ["fill-hugo", "--help"])
    assert result.exit_code == 0
    assert "Generate Hugo markdown files" in result.stdout
    assert "--output-dir" in result.stdout


def test_invalid_command(runner):
    """Test invalid command returns error."""
    result = runner.invoke(app, ["invalid-command"])
    assert result.exit_code != 0
    # Typer outputs error messages to stderr, but CliRunner captures both
    assert (
        "No such command" in result.stdout
        or "invalid-command" in result.stdout
        or result.exit_code == 2
    )  # Typer returns exit code 2 for invalid commands


def test_dry_run_with_optional_fields(runner, mock_config):
    """Test dry-run command with meetup containing optional fields."""
    with patch("pyldz.main.GoogleSheetsRepository") as mock_repo_class:
        repo_instance = Mock()
        mock_repo_class.return_value = repo_instance

        # Mock meetup data with optional fields
        from datetime import date

        from pydantic import AnyHttpUrl

        from pyldz.meetup import Language, Meetup, MeetupStatus, Talk

        sample_meetup = Meetup(
            meetup_id="59",
            title="Meetup #59 with Optional Fields",
            date=date(2025, 6, 28),
            time="18:00",
            location="indiebi",
            status=MeetupStatus.PUBLISHED,
            meetup_url=AnyHttpUrl(
                "https://www.meetup.com/python-lodz/events/306971419/"
            ),
            feedback_url=AnyHttpUrl("https://feedback.example.com"),
            livestream_id="live123",
            talks=[
                Talk(
                    speaker_id="jane-doe",
                    title="Advanced Python",
                    description="Advanced description",
                    language=Language.EN,
                    title_en="Advanced Python",
                    youtube_id="abc123",
                )
            ],
            sponsors=["sponsor1"],
        )

        repo_instance.get_all_enabled_meetups.return_value = [sample_meetup]

        with patch("pyldz.main.GoogleSheetsAPI"):
            result = runner.invoke(app, ["dry-run"])

            assert result.exit_code == 0
            assert "Meetup #59" in result.stdout
            assert "Advanced Python" in result.stdout
            assert "Language: English" in result.stdout
