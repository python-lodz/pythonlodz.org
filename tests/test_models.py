"""Tests for Pydantic models business logic."""

from datetime import date

from pyldz.models import (
    Meetup,
    Talk,
    _MeetupSheetRow,
    _TalkSheetRow,
)


def test_meetup_properties():
    """Test meetup computed properties."""
    talk = Talk(speaker_id="john-doe", title="Test Talk")
    meetup = Meetup(
        meetup_id="42",
        title="Meetup #42",
        date=date(2024, 6, 27),
        time="18:00",
        location="Test Venue",
        talks=[talk],
    )
    assert meetup.has_talks is True
    assert meetup.talk_count == 1

    empty_meetup = Meetup(
        meetup_id="43",
        title="Meetup #43",
        date=date(2024, 6, 27),
        time="18:00",
        location="Test Venue",
    )
    assert empty_meetup.has_talks is False
    assert empty_meetup.talk_count == 0


def test_parse_enabled_meetup():
    """Test parsing enabled meetup from sheet."""
    data = {
        "MEETUP_ID": "42",
        "TITLE": "Meetup #42",
        "DATE": "2024-06-27",
        "TIME": "18:00",
        "LOCATION": "Test Venue",
        "ENABLED": "TRUE",
        "MEETUP_URL": "https://meetup.com/event/123",
        "FEEDBACK_URL": "https://forms.gle/123",
        "LIVESTREAM_ID": "youtube123",
        "SPONSORS": "sponsor1,sponsor2",
        "TAGS": "python,meetup",
        "FEATURED": "TRUE",
    }

    row = _MeetupSheetRow.model_validate(data)
    assert row.meetup_id == "42"
    assert row.title == "Meetup #42"
    assert row.date == date(2024, 6, 27)
    assert row.time == "18:00"
    assert row.location == "Test Venue"
    assert row.enabled is True
    assert row.featured is True
    assert row.sponsors == ["sponsor1", "sponsor2"]
    assert row.tags == ["python", "meetup"]


def test_parse_disabled_meetup():
    """Test parsing disabled meetup from sheet."""
    data = {
        "MEETUP_ID": "43",
        "TITLE": "Meetup #43",
        "DATE": "2024-07-27",
        "TIME": "18:00",
        "LOCATION": "Test Venue",
        "ENABLED": "FALSE",
    }

    row = _MeetupSheetRow.model_validate(data)
    assert row.enabled is False


def test_filter_enabled_meetups():
    """Test filtering only enabled meetups."""
    enabled_data = {
        "MEETUP_ID": "42",
        "TITLE": "Meetup #42",
        "DATE": "2024-06-27",
        "TIME": "18:00",
        "LOCATION": "Test Venue",
        "ENABLED": "TRUE",
    }

    disabled_data = {
        "MEETUP_ID": "43",
        "TITLE": "Meetup #43",
        "DATE": "2024-07-27",
        "TIME": "18:00",
        "LOCATION": "Test Venue",
        "ENABLED": "FALSE",
    }

    enabled_row = _MeetupSheetRow.model_validate(enabled_data)
    disabled_row = _MeetupSheetRow.model_validate(disabled_data)

    all_rows = [enabled_row, disabled_row]
    enabled_only = [row for row in all_rows if row.enabled]

    assert len(enabled_only) == 1
    assert enabled_only[0].meetup_id == "42"


def test_parse_talk_from_sheet():
    """Test parsing talk from main sheet."""
    data = {
        "Meetup": "42",
        "Imię": "John",
        "Nazwisko": "Doe",
        "BIO": "A Python developer",
        "Zdjęcie": "https://example.com/photo.jpg",
        "Tytuł prezentacji": "Introduction to Python",
        "Opis prezentacji": "Learn Python basics",
        "Język prezentacji": "en",
        "Link do LinkedIn": "https://linkedin.com/in/johndoe",
        "Link do GitHub": "https://github.com/johndoe",
    }

    row = _TalkSheetRow.model_validate(data)
    assert row.meetup_id == "42"
    assert row.first_name == "John"
    assert row.last_name == "Doe"
    assert row.bio == "A Python developer"
    assert str(row.photo_url) == "https://example.com/photo.jpg"
    assert row.talk_title == "Introduction to Python"
    assert row.talk_description == "Learn Python basics"
    assert row.language == "en"
    assert str(row.linkedin_url) == "https://linkedin.com/in/johndoe"
    assert str(row.github_url) == "https://github.com/johndoe"


def test_parse_talk_minimal_data():
    """Test parsing talk with minimal required data."""
    data = {
        "Meetup": "42",
        "Imię": "John",
        "Nazwisko": "Doe",
        "Tytuł prezentacji": "Introduction to Python",
    }

    row = _TalkSheetRow.model_validate(data)
    assert row.meetup_id == "42"
    assert row.first_name == "John"
    assert row.last_name == "Doe"
    assert row.talk_title == "Introduction to Python"
    assert row.bio == ""
    assert row.language == "pl"  # default
