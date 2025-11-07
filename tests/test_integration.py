from datetime import date
from unittest.mock import Mock, patch

import pytest

from pyldz.config import AppConfig, GoogleSheetsConfig
from pyldz.models import (
    File,
    GoogleSheetsAPI,
    GoogleSheetsRepository,
    Language,
    LocationRepository,
    MeetupStatus,
    MultiLanguage,
    Speaker,
    _MeetupRow,
    _TalkRow,
)


@pytest.fixture
def app_config(tmp_path):
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
    location_repo = LocationRepository(app_config.hugo.data_dir / "locations")
    return GoogleSheetsRepository(
        GoogleSheetsAPI(app_config.google_sheets), location_repo
    )


@pytest.fixture
def complete_mock_data():
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
            "LANGUAGE",
        ],
        [
            "58",
            "Meetup #58",
            "2025-05-28",
            "18:00",
            "indiebi",
            "TRUE",
            "https://www.meetup.com/python-lodz/events/306971418/",
            "https://forms.gle/237YJFHy6G1jw9999",
            "b1rlgmlVHQo",
            "indiebi,sunscrapers",
            "Następne spotkanie!",
            "TRUE",
            "PL",
        ],
        [
            "59",
            "Meetup #59",
            "2025-07-30",
            "18:00",
            "indiebi",
            "TRUE",
            "https://www.meetup.com/python-lodz/events/306971418/",
            "",
            "",
            "indiebi,sunscrapers",
            "Następne spotkanie!",
            "TRUE",
            "PL",
        ],
        [
            "60",
            "Meetup #60",
            "2025-09-30",
            "18:00",
            "indiebi",
            "FALSE",
            "",
            "",
            "",
            "",
            "",
            "FALSE",
            "PL",
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
            "PL",
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
            "PL",
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
            "PL",
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
                "location": "indiebi",
                "enabled": "TRUE",
                "meetup_url": "https://www.meetup.com/python-lodz/events/306971418/",
                "feedback_url": "https://forms.gle/237YJFHy6G1jw9999",
                "livestream_id": "b1rlgmlVHQo",
                "sponsors": "indiebi,sunscrapers",
                "language": "PL",
            }
        ),
        _MeetupRow.model_validate(
            {
                "meetup_id": "59",
                "type": "talks",
                "date": "2025-07-30",
                "time": "18:00",
                "location": "indiebi",
                "enabled": "TRUE",
                "meetup_url": "https://www.meetup.com/python-lodz/events/306971418/",
                "feedback_url": "",
                "livestream_id": "",
                "sponsors": "indiebi,sunscrapers",
                "language": "PL",
            }
        ),
        _MeetupRow.model_validate(
            {
                "meetup_id": "60",
                "type": "talks",
                "date": "2025-09-30",
                "time": "18:00",
                "location": "indiebi",
                "enabled": "FALSE",
                "meetup_url": "",
                "feedback_url": "",
                "livestream_id": "",
                "sponsors": "",
                "language": "PL",
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
                "language": "PL",
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
                "language": "PL",
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
                "language": "PL",
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
    assert meetup.location_name == 'IndieBI, Piotrkowska 157A, budynek Hi Piotrkowska"'
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
    assert meetup.has_two_talks is True
    assert meetup.talk_count == 2


@patch("pyldz.models.GoogleSheetsRepository._fetch_meetups_data")
@patch("pyldz.models.GoogleSheetsRepository._fetch_talks_data")
def test_complete_data_flow_all_enabled_meetups(
    mock_fetch_talks, mock_fetch_meetups, repository, complete_mock_data
):
    meetups_data, talks_data = complete_mock_data

    # Setup mocks - return typed rows expected by repository
    mock_fetch_meetups.return_value = [
        _MeetupRow.model_validate(
            {
                "meetup_id": "58",
                "type": "talks",
                "date": "2025-05-28",
                "time": "18:00",
                "location": "indiebi",
                "enabled": "TRUE",
                "meetup_url": "https://www.meetup.com/python-lodz/events/306971418/",
                "feedback_url": "https://forms.gle/237YJFHy6G1jw9999",
                "livestream_id": "b1rlgmlVHQo",
                "sponsors": "indiebi,sunscrapers",
                "language": "PL",
            }
        ),
        _MeetupRow.model_validate(
            {
                "meetup_id": "59",
                "type": "talks",
                "date": "2025-07-30",
                "time": "18:00",
                "location": "indiebi",
                "enabled": "TRUE",
                "meetup_url": "https://www.meetup.com/python-lodz/events/306971418/",
                "feedback_url": "",
                "livestream_id": "",
                "sponsors": "indiebi,sunscrapers",
                "language": "PL",
            }
        ),
        _MeetupRow.model_validate(
            {
                "meetup_id": "60",
                "type": "talks",
                "date": "2025-09-30",
                "time": "18:00",
                "location": "indiebi",
                "enabled": "FALSE",
                "meetup_url": "",
                "feedback_url": "",
                "livestream_id": "",
                "sponsors": "",
                "language": "PL",
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
                "language": "PL",
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
                "language": "PL",
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
                "language": "PL",
                "linkedin_url": "https://linkedin.com/in/lukaszlanga",
                "github_url": "https://github.com/ambv",
                "facebook_url": "",
                "youtube_url": "",
                "other_urls": "https://lukasz.langa.pl",
            }
        ),
    ]

    # Test fetching all enabled meetups
    meetups = repository.get_all_enabled_meetups()

    # Should only return enabled meetups (58 and 59, not 60)
    assert len(meetups) == 2

    # Verify meetup 58
    meetup_58 = next(m for m in meetups if m.meetup_id == "58")
    assert len(meetup_58.talks) == 2

    # Verify meetup 59
    meetup_59 = next(m for m in meetups if m.meetup_id == "59")
    assert len(meetup_59.talks) == 1
    assert meetup_59.talks[0].speaker_id == "lukasz-langa"


@patch("pyldz.models.GoogleSheetsRepository._fetch_meetups_data")
@patch("pyldz.models.GoogleSheetsRepository._fetch_talks_data")
def test_disabled_meetup_filtering(
    mock_fetch_talks, mock_fetch_meetups, repository, complete_mock_data
):
    """Test that disabled meetups are properly filtered out."""
    meetups_data, talks_data = complete_mock_data

    # Setup mocks - convert raw data to dict format
    # Setup mocks - return typed rows expected by repository
    mock_fetch_meetups.return_value = [
        _MeetupRow.model_validate(
            {
                "meetup_id": "58",
                "type": "talks",
                "date": "2025-05-28",
                "time": "18:00",
                "location": "indiebi",
                "enabled": "TRUE",
                "meetup_url": "https://www.meetup.com/python-lodz/events/306971418/",
                "feedback_url": "https://forms.gle/237YJFHy6G1jw9999",
                "livestream_id": "b1rlgmlVHQo",
                "sponsors": "indiebi,sunscrapers",
                "language": "PL",
            }
        ),
        _MeetupRow.model_validate(
            {
                "meetup_id": "59",
                "type": "talks",
                "date": "2025-07-30",
                "time": "18:00",
                "location": "indiebi",
                "enabled": "TRUE",
                "meetup_url": "https://www.meetup.com/python-lodz/events/306971418/",
                "feedback_url": "",
                "livestream_id": "",
                "sponsors": "indiebi,sunscrapers",
                "language": "PL",
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
                "language": "PL",
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
                "language": "PL",
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
                "language": "PL",
                "linkedin_url": "https://linkedin.com/in/sebastianbuczynski",
                "github_url": "https://github.com/ambv",
                "facebook_url": "",
                "youtube_url": "",
                "other_urls": "https://twitter.com/sebabuczynski",
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
                "language": "PL",
                "linkedin_url": "https://linkedin.com/in/lukaszlanga",
                "github_url": "https://github.com/ambv",
                "facebook_url": "",
                "youtube_url": "",
                "other_urls": "https://lukasz.langa.pl",
            }
        ),
    ]

    # Test that disabled meetup (60) returns None
    disabled_meetup = repository.get_meetup_by_id("60")
    assert disabled_meetup is None

    # Test that it's not included in all enabled meetups
    all_meetups = repository.get_all_enabled_meetups()
    meetup_ids = {m.meetup_id for m in all_meetups}
    assert "60" not in meetup_ids
    assert "58" in meetup_ids
    assert "59" in meetup_ids


def test_configuration_validation(app_config):
    """Test that configuration is properly validated and structured."""
    # Test nested configuration structure
    assert app_config.google_sheets.sheet_id == "test_sheet_id"

    # Test that we're using the test values passed via fixture
    assert app_config.google_sheets.credentials_path.name == "test_credentials.json"
    assert app_config.google_sheets.token_cache_path.name == "test_token.json"

    # Test app-level config
    assert app_config.debug is True
    assert app_config.dry_run is True


@patch("pyldz.models.build")
def test_error_handling_and_resilience(mock_build, repository):
    """Test error handling and resilience of the complete flow."""
    # Setup mocks to simulate various error conditions
    mock_sheets = Mock()
    mock_build.return_value = mock_sheets

    # Test empty sheet handling by patching repository fetchers to return empty
    with patch(
        "pyldz.models.GoogleSheetsRepository._fetch_meetups_data", return_value=[]
    ), patch("pyldz.models.GoogleSheetsRepository._fetch_talks_data", return_value=[]):
        meetups = repository.get_all_enabled_meetups()
        assert meetups == []

        meetup = repository.get_meetup_by_id("42")
        assert meetup is None


def test_model_integration_and_validation():
    talk_data = {
        "meetup_id": "42",
        "first_name": "John",
        "last_name": "Doe",
        "bio": "A Python developer",
        "photo_url": "https://example.com/photo.jpg",
        "talk_title": "Test Talk",
        "talk_description": "desc",
        "talk_title_en": "Test Talk",
        "facebook_url": "",
        "linkedin_url": "",
        "youtube_url": "",
        "other_urls": "",
        "language": "EN",
    }

    talk_row = _TalkRow.model_validate(talk_data)

    # Avoid network by stubbing downloader
    from pyldz.models import File

    speaker = talk_row.to_speaker(lambda _: File(name="avatar.png", content=b""))
    talk = talk_row.to_talk()

    # Test meetup sheet row parsing
    meetup_data = {
        "meetup_id": "42",
        "type": "talks",
        "date": "2024-06-27",
        "time": "18:00",
        "location": "test_venue",
        "enabled": "TRUE",
        "sponsors": "",
        "meetup_url": "",
        "feedback_url": "",
        "livestream_id": "",
        "language": "EN",
    }

    # Create a mock LocationRepository
    from pathlib import Path

    from pyldz.models import Location

    location_repo = LocationRepository(Path("/tmp/nonexistent"))
    # Manually add a test location
    location_repo._locations_cache["test_venue"] = Location(
        name=MultiLanguage(pl="Test Venue PL", en="Test Venue EN")
    )

    meetup_row = _MeetupRow.model_validate(meetup_data)
    meetup = meetup_row.to_meetup([talk], location_repo)

    # Verify integration
    assert meetup.meetup_id == "42"
    assert len(meetup.talks) == 1
    assert meetup.talks[0].speaker_id == speaker.id
    assert meetup.talks[0].language == Language.EN
    assert speaker.name == "John Doe"
    assert meetup.location_name == "Test Venue EN"


def test_speaker_with_missing_photo_url_uses_fallback():
    # Test with None photo_url
    talk_data_none = {
        "meetup_id": "42",
        "first_name": "Jane",
        "last_name": "Smith",
        "bio": "A Python developer",
        "photo_url": None,
        "talk_title": "Test Talk",
        "talk_description": "desc",
        "language": "EN",
        "talk_title_en": "Test Talk",
        "facebook_url": "",
        "linkedin_url": "",
        "youtube_url": "",
        "other_urls": "",
    }

    talk_row_none = _TalkRow.model_validate(talk_data_none)
    speaker_none = talk_row_none.to_speaker(
        lambda _: File(name="avatar.png", content=b"")
    )

    # Verify fallback is used
    assert speaker_none.avatar.name == "no_photo.png"
    assert speaker_none.avatar.content != b""

    # Test with empty string photo_url
    talk_data_empty = {
        "meetup_id": "42",
        "first_name": "Bob",
        "last_name": "Johnson",
        "bio": "A Python developer",
        "photo_url": "",
        "talk_title": "Test Talk",
        "talk_description": "desc",
        "language": "EN",
        "talk_title_en": "Test Talk",
        "facebook_url": "",
        "linkedin_url": "",
        "youtube_url": "",
        "other_urls": "",
    }

    talk_row_empty = _TalkRow.model_validate(talk_data_empty)
    speaker_empty = talk_row_empty.to_speaker(
        lambda _: File(name="avatar.png", content=b"")
    )

    # Verify fallback is used
    assert speaker_empty.avatar.name == "no_photo.png"
    assert speaker_empty.avatar.content != b""
