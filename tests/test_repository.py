"""Tests for Google Sheets repository."""

from datetime import date
from unittest.mock import Mock, patch

import pytest

from pyldz.config import GoogleSheetsConfig
from pyldz.repository import GoogleSheetsRepository


@pytest.fixture
def config(tmp_path):
    """Create test configuration."""
    # Create dummy credentials file for validation
    credentials_file = tmp_path / "test_credentials.json"
    credentials_file.write_text('{"type": "service_account"}')

    return GoogleSheetsConfig(
        sheet_id="test_sheet_id",
        credentials_path=credentials_file,
        token_cache_path=tmp_path / "test_token.json",
        meetups_sheet_name="meetups",
        talks_sheet_name="Sheet1",
    )


@pytest.fixture
def repository(config):
    """Create repository instance."""
    return GoogleSheetsRepository(config)


@pytest.fixture
def mock_meetups_data():
    """Mock data from meetups sheet."""
    return [
        [
            "MEETUP_ID",
            "TITLE",
            "DATE",
            "TIME",
            "LOCATION",
            "ENABLED",
            "MEETUP_URL",
            "FEEDBACK_URL",
            "LIVESTREAM_ID",
            "SPONSORS",
            "TAGS",
            "FEATURED",
        ],
        [
            "42",
            "Meetup #42",
            "2024-06-27",
            "18:00",
            "Test Venue",
            "TRUE",
            "https://meetup.com/event/123",
            "https://forms.gle/123",
            "youtube123",
            "sponsor1,sponsor2",
            "python,meetup",
            "TRUE",
        ],
        [
            "43",
            "Meetup #43",
            "2024-07-27",
            "18:00",
            "Test Venue 2",
            "FALSE",
            "",
            "",
            "",
            "",
            "",
            "FALSE",
        ],
        [
            "44",
            "Meetup #44",
            "2024-08-27",
            "18:00",
            "Test Venue 3",
            "TRUE",
            "",
            "",
            "",
            "",
            "",
            "FALSE",
        ],
    ]


@pytest.fixture
def mock_talks_data():
    """Mock data from talks/main sheet."""
    return [
        [
            "Meetup",
            "Imię",
            "Nazwisko",
            "BIO",
            "Zdjęcie",
            "Tytuł prezentacji",
            "Opis prezentacji",
            "Język prezentacji",
            "Link do LinkedIn",
            "Link do GitHub",
        ],
        [
            "42",
            "John",
            "Doe",
            "A Python developer",
            "https://example.com/photo1.jpg",
            "Introduction to Python",
            "Learn Python basics",
            "en",
            "https://linkedin.com/in/johndoe",
            "https://github.com/johndoe",
        ],
        [
            "42",
            "Jane",
            "Smith",
            "Data scientist",
            "https://example.com/photo2.jpg",
            "Data Science with Python",
            "Advanced data analysis",
            "pl",
            "https://linkedin.com/in/janesmith",
            "",
        ],
        [
            "44",
            "Bob",
            "Wilson",
            "DevOps engineer",
            "",
            "Python in DevOps",
            "Automation with Python",
            "pl",
            "",
            "https://github.com/bobwilson",
        ],
    ]


def test_repository_initialization(config):
    """Test repository initialization."""
    repo = GoogleSheetsRepository(config)
    assert repo.config == config
    assert repo.scopes == (
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
    )


@patch("pyldz.repository.build")
@patch("pyldz.repository.GoogleSheetsRepository._get_credentials")
def test_fetch_meetups_data(mock_get_creds, mock_build, repository, mock_meetups_data):
    """Test fetching meetups data from sheet."""
    # Setup mocks
    mock_sheets = Mock()
    mock_build.return_value = mock_sheets

    mock_sheets.spreadsheets().get().execute.return_value = {
        "sheets": [{"properties": {"title": "meetups"}}]
    }
    mock_sheets.spreadsheets().values().get().execute.return_value = {
        "values": mock_meetups_data
    }

    # Test
    meetups_data = repository.fetch_meetups_data()

    # Assertions
    assert len(meetups_data) == 3  # Header row excluded
    assert meetups_data[0]["MEETUP_ID"] == "42"
    assert meetups_data[0]["ENABLED"] == "TRUE"
    assert meetups_data[1]["MEETUP_ID"] == "43"
    assert meetups_data[1]["ENABLED"] == "FALSE"


@patch("pyldz.repository.build")
@patch("pyldz.repository.GoogleSheetsRepository._get_credentials")
def test_fetch_talks_data(mock_get_creds, mock_build, repository, mock_talks_data):
    """Test fetching talks data from sheet."""
    # Setup mocks
    mock_sheets = Mock()
    mock_build.return_value = mock_sheets

    mock_sheets.spreadsheets().get().execute.return_value = {
        "sheets": [{"properties": {"title": "Sheet1"}}]
    }
    mock_sheets.spreadsheets().values().get().execute.return_value = {
        "values": mock_talks_data
    }

    # Test
    talks_data = repository.fetch_talks_data()

    # Assertions
    assert len(talks_data) == 3  # Header row excluded
    assert talks_data[0]["Meetup"] == "42"
    assert talks_data[0]["Imię"] == "John"
    assert talks_data[1]["Meetup"] == "42"
    assert talks_data[2]["Meetup"] == "44"


def test_get_enabled_meetups(repository, mock_meetups_data):
    """Test filtering enabled meetups."""
    # Convert mock data to list of dicts (simulating what fetch_meetups_data returns)
    header = mock_meetups_data[0]
    meetups_data = []
    for row in mock_meetups_data[1:]:
        meetups_data.append(dict(zip(header, row)))

    enabled_meetups = repository.get_enabled_meetups(meetups_data)

    # Should only return meetups with ENABLED=TRUE
    assert len(enabled_meetups) == 2
    assert enabled_meetups[0].meetup_id == "42"
    assert enabled_meetups[1].meetup_id == "44"
    assert all(meetup.enabled for meetup in enabled_meetups)


def test_get_talks_for_meetup(repository, mock_talks_data):
    """Test getting talks for specific meetup."""
    # Convert mock data to list of dicts
    header = mock_talks_data[0]
    talks_data = []
    for row in mock_talks_data[1:]:
        talks_data.append(dict(zip(header, row)))

    talks_42 = repository.get_talks_for_meetup("42", talks_data)
    talks_44 = repository.get_talks_for_meetup("44", talks_data)
    talks_99 = repository.get_talks_for_meetup("99", talks_data)

    # Assertions
    assert len(talks_42) == 2
    assert talks_42[0].speaker_id == "john-doe"
    assert talks_42[1].speaker_id == "jane-smith"

    assert len(talks_44) == 1
    assert talks_44[0].speaker_id == "bob-wilson"

    assert len(talks_99) == 0


def test_get_speakers_for_meetup(repository, mock_talks_data):
    """Test getting speakers for specific meetup."""
    # Convert mock data to list of dicts
    header = mock_talks_data[0]
    talks_data = []
    for row in mock_talks_data[1:]:
        talks_data.append(dict(zip(header, row)))

    speakers_42 = repository.get_speakers_for_meetup("42", talks_data)
    speakers_44 = repository.get_speakers_for_meetup("44", talks_data)

    # Assertions
    assert len(speakers_42) == 2
    assert speakers_42[0].id == "john-doe"
    assert speakers_42[0].name == "John Doe"
    assert speakers_42[1].id == "jane-smith"
    assert speakers_42[1].name == "Jane Smith"

    assert len(speakers_44) == 1
    assert speakers_44[0].id == "bob-wilson"
    assert speakers_44[0].name == "Bob Wilson"


@patch("pyldz.repository.GoogleSheetsRepository.fetch_meetups_data")
@patch("pyldz.repository.GoogleSheetsRepository.fetch_talks_data")
def test_get_meetup_by_id(
    mock_fetch_talks,
    mock_fetch_meetups,
    repository,
    mock_meetups_data,
    mock_talks_data,
):
    """Test getting specific meetup by ID."""
    # Setup mocks
    header_meetups = mock_meetups_data[0]
    meetups_data = [dict(zip(header_meetups, row)) for row in mock_meetups_data[1:]]
    mock_fetch_meetups.return_value = meetups_data

    header_talks = mock_talks_data[0]
    talks_data = [dict(zip(header_talks, row)) for row in mock_talks_data[1:]]
    mock_fetch_talks.return_value = talks_data

    # Test
    meetup = repository.get_meetup_by_id("42")

    # Assertions
    assert meetup is not None
    assert meetup.number == "42"
    assert meetup.title == "Meetup #42"
    assert meetup.date == date(2024, 6, 27)
    assert meetup.time == "18:00"
    assert meetup.location == "Test Venue"
    assert meetup.featured is True
    assert len(meetup.talks) == 2
    assert len(meetup.sponsors) == 2
    assert "sponsor1" in meetup.sponsors
    assert "sponsor2" in meetup.sponsors


@patch("pyldz.repository.GoogleSheetsRepository.fetch_meetups_data")
@patch("pyldz.repository.GoogleSheetsRepository.fetch_talks_data")
def test_get_meetup_by_id_disabled(
    mock_fetch_talks,
    mock_fetch_meetups,
    repository,
    mock_meetups_data,
    mock_talks_data,
):
    """Test getting disabled meetup returns None."""
    # Setup mocks
    header_meetups = mock_meetups_data[0]
    meetups_data = [dict(zip(header_meetups, row)) for row in mock_meetups_data[1:]]
    mock_fetch_meetups.return_value = meetups_data

    header_talks = mock_talks_data[0]
    talks_data = [dict(zip(header_talks, row)) for row in mock_talks_data[1:]]
    mock_fetch_talks.return_value = talks_data

    # Test - meetup 43 is disabled
    meetup = repository.get_meetup_by_id("43")

    # Should return None for disabled meetup
    assert meetup is None


@patch("pyldz.repository.GoogleSheetsRepository.fetch_meetups_data")
@patch("pyldz.repository.GoogleSheetsRepository.fetch_talks_data")
def test_get_all_enabled_meetups(
    mock_fetch_talks,
    mock_fetch_meetups,
    repository,
    mock_meetups_data,
    mock_talks_data,
):
    """Test getting all enabled meetups."""
    # Setup mocks
    header_meetups = mock_meetups_data[0]
    meetups_data = [dict(zip(header_meetups, row)) for row in mock_meetups_data[1:]]
    mock_fetch_meetups.return_value = meetups_data

    header_talks = mock_talks_data[0]
    talks_data = [dict(zip(header_talks, row)) for row in mock_talks_data[1:]]
    mock_fetch_talks.return_value = talks_data

    # Test
    meetups = repository.get_all_enabled_meetups()

    # Assertions
    assert len(meetups) == 2  # Only enabled meetups
    assert meetups[0].number == "42"
    assert meetups[1].number == "44"
    assert len(meetups[0].talks) == 2  # Meetup 42 has 2 talks
    assert len(meetups[1].talks) == 1  # Meetup 44 has 1 talk


def test_error_handling_empty_sheet(repository):
    """Test handling of empty sheet data."""
    empty_data = []
    enabled_meetups = repository.get_enabled_meetups(empty_data)
    assert enabled_meetups == []

    talks = repository.get_talks_for_meetup("42", empty_data)
    assert talks == []

    speakers = repository.get_speakers_for_meetup("42", empty_data)
    assert speakers == []
