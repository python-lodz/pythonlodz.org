from datetime import date

from pyldz.models import (
    Language,
    Meetup,
    Talk,
)
from pyldz.models import (
    _MeetupRow as _MeetupSheetRow,
)
from pyldz.models import (
    _TalkRow as _TalkSheetRow,
)


def test_meetup_properties():
    """Test meetup computed properties."""
    talk = Talk(
        speaker_id="john-doe",
        title="Test Talk",
        description="desc",
        language=Language.EN,
        title_en="Test Talk",
    )
    meetup = Meetup(
        meetup_id="42",
        title="Meetup #42",
        date=date(2024, 6, 27),
        time="18:00",
        location="Test Venue",
        talks=[talk],
        sponsors=[],
    )
    assert meetup.has_talks is True
    assert meetup.talk_count == 1

    empty_meetup = Meetup(
        meetup_id="43",
        title="Meetup #43",
        date=date(2024, 6, 27),
        time="18:00",
        location="Test Venue",
        talks=[],
        sponsors=[],
    )
    assert empty_meetup.has_talks is False
    assert empty_meetup.talk_count == 0


def test_parse_enabled_meetup():
    """Test parsing enabled meetup from sheet."""
    data = {
        "meetup_id": "42",
        "type": "talks",
        "date": "2024-06-27",
        "time": "18:00",
        "location": "Test Venue",
        "enabled": "TRUE",
        "meetup_url": "https://meetup.com/event/123",
        "feedback_url": "https://forms.gle/123",
        "livestream_id": "youtube123",
        "sponsors": "sponsor1,sponsor2",
    }

    row = _MeetupSheetRow.model_validate(data)
    assert row.meetup_id == "42"
    assert row.title == "Meetup #42"
    assert row.date == date(2024, 6, 27)
    assert row.time == "18:00"
    assert row.location == "Test Venue"
    assert row.enabled is True
    assert row.sponsors == ["sponsor1", "sponsor2"]


def test_parse_disabled_meetup():
    """Test parsing disabled meetup from sheet."""
    data = {
        "meetup_id": "43",
        "type": "talks",
        "date": "2024-07-27",
        "time": "18:00",
        "location": "Test Venue",
        "enabled": "FALSE",
        "sponsors": "",
        "meetup_url": "",
        "feedback_url": "",
        "livestream_id": "",
    }

    row = _MeetupSheetRow.model_validate(data)
    assert row.enabled is False


def test_filter_enabled_meetups():
    """Test filtering only enabled meetups."""
    enabled_data = {
        "meetup_id": "42",
        "type": "talks",
        "date": "2024-06-27",
        "time": "18:00",
        "location": "Test Venue",
        "enabled": "TRUE",
        "meetup_url": "",
        "feedback_url": "",
        "livestream_id": "",
        "sponsors": "",
    }

    disabled_data = {
        "meetup_id": "43",
        "type": "talks",
        "date": "2024-07-27",
        "time": "18:00",
        "location": "Test Venue",
        "enabled": "FALSE",
        "meetup_url": "",
        "feedback_url": "",
        "livestream_id": "",
        "sponsors": "",
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
        "meetup_id": "42",
        "first_name": "John",
        "last_name": "Doe",
        "bio": "A Python developer",
        "photo_url": "https://example.com/photo.jpg",
        "talk_title": "Introduction to Python",
        "talk_description": "Learn Python basics",
        "language": "en",
        "linkedin_url": "https://linkedin.com/in/johndoe",
        "github_url": "https://github.com/johndoe",
        "talk_title_en": "",
        "facebook_url": "",
        "youtube_url": "",
        "other_urls": "",
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


def test_parse_talk_minimal_data():
    """Test parsing talk with minimal required data."""
    data = {
        "meetup_id": "42",
        "first_name": "John",
        "last_name": "Doe",
        "talk_title": "Introduction to Python",
        "bio": "",
        "photo_url": "https://example.com/photo.jpg",
        "talk_description": "",
        "language": "pl",
        "talk_title_en": "",
        "facebook_url": "",
        "linkedin_url": "",
        "youtube_url": "",
        "other_urls": "",
    }

    row = _TalkSheetRow.model_validate(data)
    assert row.meetup_id == "42"
    assert row.first_name == "John"
    assert row.last_name == "Doe"
    assert row.talk_title == "Introduction to Python"
    assert row.bio == ""
    assert row.language == "pl"  # default
