"""Integration tests for the complete Google Sheets data flow."""

from datetime import date
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from pyldz.config import AppConfig, GoogleSheetsConfig
from pyldz.models import (
    GoogleSheetsAPI,
    GoogleSheetsRepository,
    Language,
    MeetupStatus,
    _MeetupRow,
    _TalkRow,
)


@pytest.fixture
def app_config(tmp_path):
    """Create test application configuration."""
    # Create dummy credentials file for validation
    credentials_file = tmp_path / "test_credentials.json"
    credentials_file.write_text('{"type": "service_account"}')

    return AppConfig(
        google_sheets=GoogleSheetsConfig(
            sheet_id="test_sheet_id",
            credentials_path=credentials_file,
            token_cache_path=tmp_path / "test_token.json",
            meetups_sheet_name="meetups",
            talks_sheet_name="Sheet1",
        ),
        debug=True,
        dry_run=True,
    )


@pytest.fixture
def repository(app_config):
    """Create repository with test configuration."""
    return GoogleSheetsRepository(GoogleSheetsAPI(app_config.google_sheets))


@pytest.fixture
def complete_mock_data():
    """Complete mock data simulating real Google Sheets structure."""
    meetups_data = [
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
            "58",
            "Meetup #58",
            "2025-05-28",
            "18:00",
            "IndieBI, Piotrkowska 157A, budynek Hi Piotrkowska",
            "TRUE",
            "https://www.meetup.com/python-lodz/events/306971418/",
            "https://forms.gle/237YJFHy6G1jw9999",
            "b1rlgmlVHQo",
            "indiebi,sunscrapers",
            "Następne spotkanie!",
            "TRUE",
        ],
        [
            "59",
            "Meetup #59",
            "2025-07-30",
            "18:00",
            "IndieBI, Piotrkowska 157A, budynek Hi Piotrkowska",
            "TRUE",
            "https://www.meetup.com/python-lodz/events/306971418/",
            "",
            "",
            "indiebi,sunscrapers",
            "Następne spotkanie!",
            "TRUE",
        ],
        [
            "60",
            "Meetup #60",
            "2025-09-30",
            "18:00",
            "TBA",
            "FALSE",
            "",
            "",
            "",
            "",
            "",
            "FALSE",
        ],
    ]

    talks_data = [
        [
            "Meetup",
            "Imię",
            "Nazwisko",
            "BIO",
            "Zdjęcie",
            "Tytuł prezentacji",
            "Opis prezentacji",
            "Tytuł prezentacji EN",
            "Język prezentacji",
            "Link do LinkedIn",
            "Link do GitHub",
            "Link do Twitter",
            "Link do strony",
        ],
        [
            "58",
            "Grzegorz",
            "Kocjan",
            "Python developer z wieloletnim doświadczeniem w tworzeniu aplikacji webowych.",
            "https://example.com/grzegorz.jpg",
            "Pythonowa konfiguracja, która przyprawi Cię o dreszcze (w dobry sposób, obiecuję!)",
            "Konfiguracja — wszyscy jej potrzebujemy, wszyscy jej nienawidzimy. A mimo to, w każdym projekcie przynajmniej raz udaje nam się ją zepsuć.",
            "Python Config That Will Give You Chills (In a Good Way, I Promise!)",
            "pl",
            "https://linkedin.com/in/grzegorzkocjan",
            "https://github.com/gkocjan",
            "",
            "",
        ],
        [
            "58",
            "Sebastian",
            "Buczyński",
            "Senior Python Developer, entuzjasta clean code i dobrych praktyk programistycznych.",
            "https://example.com/sebastian.jpg",
            "Programista zoptymalizował aplikację, ale nikt mu nie pogratulował bo była w Pythonie 😔",
            "Wokół tematu wydajności w Pythonie narosło wiele mitów. Rozwiejmy te fałszywe przekonania opierając się na twardych danych.",
            "A software developer optimized the application, but no one congratulated them because it was written in Python 😔",
            "pl",
            "https://linkedin.com/in/sebastianbuczynski",
            "",
            "https://twitter.com/sebabuczynski",
            "",
        ],
        [
            "59",
            "Łukasz",
            "Langa",
            "Python Core Developer, twórca Black, były Python Release Manager.",
            "https://example.com/lukasz.jpg",
            "Nowość w Pythonie 3.14 oraz PyScript",
            "Przegląd najnowszych funkcjonalności w Pythonie 3.14 oraz wprowadzenie do PyScript.",
            "What's New in Python 3.14 and PyScript",
            "pl",
            "https://linkedin.com/in/lukaszlanga",
            "https://github.com/ambv",
            "",
            "https://lukasz.langa.pl",
        ],
    ]

    return meetups_data, talks_data


@patch("pyldz.models.GoogleSheetsRepository._fetch_meetups_data")
@patch("pyldz.models.GoogleSheetsRepository._fetch_talks_data")
def test_complete_data_flow_single_meetup(
    mock_fetch_talks, mock_fetch_meetups, repository, complete_mock_data
):
    """Test complete flow for fetching a single meetup with all data."""
    meetups_data, talks_data = complete_mock_data

    # Setup mocks - return typed rows expected by repository
    mock_fetch_meetups.return_value = [
        _MeetupRow.model_validate(
            {
                "meetup_id": "58",
                "type": "talks",
                "date": "2025-05-28",
                "time": "18:00",
                "location": "IndieBI, Piotrkowska 157A, budynek Hi Piotrkowska",
                "enabled": "TRUE",
                "meetup_url": "https://www.meetup.com/python-lodz/events/306971418/",
                "feedback_url": "https://forms.gle/237YJFHy6G1jw9999",
                "livestream_id": "b1rlgmlVHQo",
                "sponsors": "indiebi,sunscrapers",
            }
        ),
        _MeetupRow.model_validate(
            {
                "meetup_id": "59",
                "type": "talks",
                "date": "2025-07-30",
                "time": "18:00",
                "location": "IndieBI, Piotrkowska 157A, budynek Hi Piotrkowska",
                "enabled": "TRUE",
                "meetup_url": "https://www.meetup.com/python-lodz/events/306971418/",
                "feedback_url": "",
                "livestream_id": "",
                "sponsors": "indiebi,sunscrapers",
            }
        ),
        _MeetupRow.model_validate(
            {
                "meetup_id": "60",
                "type": "talks",
                "date": "2025-09-30",
                "time": "18:00",
                "location": "TBA",
                "enabled": "FALSE",
                "meetup_url": "",
                "feedback_url": "",
                "livestream_id": "",
                "sponsors": "",
            }
        ),
    ]

    mock_fetch_talks.return_value = [
        _TalkRow.model_validate(
            {
                "meetup_id": "58",
                "first_name": "Grzegorz",
                "last_name": "Kocjan",
                "bio": "Python developer z wieloletnim doświadczeniem w tworzeniu aplikacji webowych.",
                "photo_url": "https://example.com/grzegorz.jpg",
                "talk_title": "Pythonowa konfiguracja, która przyprawi Cię o dreszcze (w dobry sposób, obiecuję!)",
                "talk_description": "Konfiguracja — wszyscy jej potrzebujemy, wszyscy jej nienawidzimy. A mimo to, w każdym projekcie przynajmniej raz udaje nam się ją zepsuć.",
                "talk_title_en": "Python Config That Will Give You Chills (In a Good Way, I Promise!)",
                "language": "pl",
                "linkedin_url": "https://linkedin.com/in/grzegorzkocjan",
                "github_url": "https://github.com/gkocjan",
                "facebook_url": "",
                "youtube_url": "",
                "other_urls": "",
            }
        ),
        _TalkRow.model_validate(
            {
                "meetup_id": "58",
                "first_name": "Sebastian",
                "last_name": "Buczyński",
                "bio": "Senior Python Developer, entuzjasta clean code i dobrych praktyk programistycznych.",
                "photo_url": "https://example.com/sebastian.jpg",
                "talk_title": "Programista zoptymalizował aplikację, ale nikt mu nie pogratulował bo była w Pythonie 😔",
                "talk_description": "Wokół tematu wydajności w Pythonie narosło wiele mitów. Rozwiejmy te fałszywe przekonania opierając się na twardych danych.",
                "talk_title_en": "A software developer optimized the application, but no one congratulated them because it was written in Python 😔",
                "language": "pl",
                "linkedin_url": "https://linkedin.com/in/sebastianbuczynski",
                "github_url": "https://github.com/sebabuczynski",
                "facebook_url": "",
                "youtube_url": "https://twitter.com/sebabuczynski",
                "other_urls": "",
            }
        ),
        _TalkRow.model_validate(
            {
                "meetup_id": "59",
                "first_name": "Łukasz",
                "last_name": "Langa",
                "bio": "Python Core Developer, twórca Black, były Python Release Manager.",
                "photo_url": "https://example.com/lukasz.jpg",
                "talk_title": "Nowość w Pythonie 3.14 oraz PyScript",
                "talk_description": "Przegląd najnowszych funkcjonalności w Pythonie 3.14 oraz wprowadzenie do PyScript.",
                "talk_title_en": "What's New in Python 3.14 and PyScript",
                "language": "pl",
                "linkedin_url": "https://linkedin.com/in/lukaszlanga",
                "github_url": "https://github.com/ambv",
                "facebook_url": "",
                "youtube_url": "",
                "other_urls": "https://lukasz.langa.pl",
            }
        ),
    ]

    # Test fetching meetup #58
    meetup = repository.get_meetup_by_id("58")

    # Verify meetup data
    assert meetup is not None
    assert meetup.meetup_id == "58"
    assert meetup.title == "Meetup #58"
    assert meetup.date == date(2025, 5, 28)
    assert meetup.time == "18:00"
    assert meetup.location == "IndieBI, Piotrkowska 157A, budynek Hi Piotrkowska"
    # featured field removed in current model
    assert meetup.status == MeetupStatus.PUBLISHED
    assert (
        str(meetup.meetup_url) == "https://www.meetup.com/python-lodz/events/306971418/"
    )
    assert str(meetup.feedback_url) == "https://forms.gle/237YJFHy6G1jw9999"
    assert meetup.livestream_id == "b1rlgmlVHQo"
    assert "indiebi" in meetup.sponsors
    assert "sunscrapers" in meetup.sponsors
    # tags field removed in current model

    # Verify talks
    assert len(meetup.talks) == 2

    # First talk - Grzegorz
    talk1 = meetup.talks[0]
    assert talk1.speaker_id == "grzegorz-kocjan"
    assert (
        talk1.title
        == "Pythonowa konfiguracja, która przyprawi Cię o dreszcze (w dobry sposób, obiecuję!)"
    )
    assert (
        talk1.title_en
        == "Python Config That Will Give You Chills (In a Good Way, I Promise!)"
    )
    assert talk1.language == Language.PL
    assert "Konfiguracja — wszyscy jej potrzebujemy" in talk1.description

    # Second talk - Sebastian
    talk2 = meetup.talks[1]
    assert talk2.speaker_id == "sebastian-buczynski"
    assert (
        talk2.title
        == "Programista zoptymalizował aplikację, ale nikt mu nie pogratulował bo była w Pythonie 😔"
    )
    assert talk2.language == Language.PL

    # Verify computed properties
    assert meetup.has_talks is True
    assert meetup.talk_count == 2


@patch("pyldz.models.GoogleSheetsRepository._fetch_meetups_data")
@patch("pyldz.models.GoogleSheetsRepository._fetch_talks_data")
def test_complete_data_flow_all_enabled_meetups(
    mock_fetch_talks, mock_fetch_meetups, repository, complete_mock_data
):
    """Test complete flow for fetching all enabled meetups."""
    meetups_data, talks_data = complete_mock_data

    # Setup mocks - convert raw data to dict format
    header_meetups = meetups_data[0]
    meetups_dict_data = [dict(zip(header_meetups, row)) for row in meetups_data[1:]]
    mock_fetch_meetups.return_value = meetups_dict_data

    header_talks = talks_data[0]
    talks_dict_data = [dict(zip(header_talks, row)) for row in talks_data[1:]]
    mock_fetch_talks.return_value = talks_dict_data

    # Test fetching all enabled meetups
    meetups = repository.get_all_enabled_meetups()

    # Should only return enabled meetups (58 and 59, not 60)
    assert len(meetups) == 2

    # Verify meetup 58
    meetup_58 = next(m for m in meetups if m.number == "58")
    assert len(meetup_58.talks) == 2
    assert meetup_58.featured is True

    # Verify meetup 59
    meetup_59 = next(m for m in meetups if m.number == "59")
    assert len(meetup_59.talks) == 1
    assert meetup_59.talks[0].speaker_id == "lukasz-langa"


@patch("pyldz.models.GoogleSheetsRepository._fetch_meetups_data")
@patch("pyldz.models.GoogleSheetsRepository._fetch_talks_data")
def test_speakers_extraction_and_deduplication(
    mock_fetch_talks, mock_fetch_meetups, repository, complete_mock_data
):
    """Test speaker extraction and deduplication across meetups."""
    meetups_data, talks_data = complete_mock_data

    # Setup mocks - convert raw data to dict format
    header_meetups = meetups_data[0]
    meetups_dict_data = [dict(zip(header_meetups, row)) for row in meetups_data[1:]]
    mock_fetch_meetups.return_value = meetups_dict_data

    header_talks = talks_data[0]
    talks_dict_data = [dict(zip(header_talks, row)) for row in talks_data[1:]]
    mock_fetch_talks.return_value = talks_dict_data

    # Test getting all speakers
    speakers = repository.get_all_speakers()

    # Should have 3 unique speakers
    assert len(speakers) == 3

    speaker_ids = {speaker.id for speaker in speakers}
    assert "grzegorz-kocjan" in speaker_ids
    assert "sebastian-buczynski" in speaker_ids
    assert "lukasz-langa" in speaker_ids

    # Verify speaker details
    grzegorz = next(s for s in speakers if s.id == "grzegorz-kocjan")
    assert grzegorz.name == "Grzegorz Kocjan"
    assert "Python developer z wieloletnim doświadczeniem" in grzegorz.bio
    assert len(grzegorz.social_links) == 2  # LinkedIn and GitHub

    lukasz = next(s for s in speakers if s.id == "lukasz-langa")
    assert lukasz.name == "Łukasz Langa"
    assert len(lukasz.social_links) == 3  # LinkedIn, GitHub, and website


@patch("pyldz.models.GoogleSheetsRepository._fetch_meetups_data")
@patch("pyldz.models.GoogleSheetsRepository._fetch_talks_data")
def test_disabled_meetup_filtering(
    mock_fetch_talks, mock_fetch_meetups, repository, complete_mock_data
):
    """Test that disabled meetups are properly filtered out."""
    meetups_data, talks_data = complete_mock_data

    # Setup mocks - convert raw data to dict format
    header_meetups = meetups_data[0]
    meetups_dict_data = [dict(zip(header_meetups, row)) for row in meetups_data[1:]]
    mock_fetch_meetups.return_value = meetups_dict_data

    header_talks = talks_data[0]
    talks_dict_data = [dict(zip(header_talks, row)) for row in talks_data[1:]]
    mock_fetch_talks.return_value = talks_dict_data

    # Test that disabled meetup (60) returns None
    disabled_meetup = repository.get_meetup_by_id("60")
    assert disabled_meetup is None

    # Test that it's not included in all enabled meetups
    all_meetups = repository.get_all_enabled_meetups()
    meetup_numbers = {m.number for m in all_meetups}
    assert "60" not in meetup_numbers
    assert "58" in meetup_numbers
    assert "59" in meetup_numbers


def test_configuration_validation(app_config):
    """Test that configuration is properly validated and structured."""
    # Test nested configuration structure
    assert app_config.google_sheets.sheet_id == "test_sheet_id"
    assert app_config.google_sheets.meetups_sheet_name == "meetups"
    assert app_config.google_sheets.talks_sheet_name == "Sheet1"

    # Test that we're using the test values, not defaults
    assert app_config.google_sheets.credentials_path == Path("test_credentials.json")
    assert app_config.google_sheets.token_cache_path == Path("test_token.json")

    # Test app-level config
    assert app_config.debug is True
    assert app_config.dry_run is True


@patch("pyldz.models.build")
@patch("pyldz.models.GoogleSheetsRepository._get_credentials")
def test_error_handling_and_resilience(mock_get_creds, mock_build, repository):
    """Test error handling and resilience of the complete flow."""
    # Setup mocks to simulate various error conditions
    mock_sheets = Mock()
    mock_build.return_value = mock_sheets

    # Test empty sheet handling
    mock_sheets.spreadsheets().values().get().execute.return_value = {"values": []}

    meetups = repository.get_all_enabled_meetups()
    assert meetups == []

    meetup = repository.get_meetup_by_id("42")
    assert meetup is None

    speakers = repository.get_all_speakers()
    assert speakers == []


def test_model_integration_and_validation():
    """Test that models work correctly together in integration scenarios."""
    # Test creating a complete meetup with talks and speakers

    # Test talk sheet row parsing
    talk_data = {
        "Meetup": "42",
        "Imię": "John",
        "Nazwisko": "Doe",
        "BIO": "A Python developer",
        "Tytuł prezentacji": "Test Talk",
        "Język prezentacji": "en",
    }

    talk_row = _TalkRow.model_validate(talk_data)
    speaker = talk_row.to_speaker()
    talk = talk_row.to_talk()

    # Test meetup sheet row parsing
    meetup_data = {
        "MEETUP_ID": "42",
        "TITLE": "Test Meetup",
        "DATE": "2024-06-27",
        "TIME": "18:00",
        "LOCATION": "Test Venue",
        "ENABLED": "TRUE",
    }

    meetup_row = _MeetupRow.model_validate(meetup_data)
    meetup = meetup_row.to_meetup([talk])

    # Verify integration
    assert meetup.meetup_id == "42"
    assert len(meetup.talks) == 1
    assert meetup.talks[0].speaker_id == speaker.id
    assert meetup.talks[0].language == Language.EN
    assert speaker.name == "John Doe"
