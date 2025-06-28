"""Tests for Pydantic models."""

from datetime import date

import pytest
from pydantic import ValidationError

from pyldz.models import (
    Language,
    Meetup,
    MeetupSheetRow,
    MeetupStatus,
    SocialLink,
    Speaker,
    Talk,
    TalkSheetRow,
)


class TestLanguage:
    """Test Language enum."""

    def test_language_values(self):
        """Test language enum values."""
        assert Language.POLISH == "pl"
        assert Language.ENGLISH == "en"


class TestMeetupStatus:
    """Test MeetupStatus enum."""

    def test_status_values(self):
        """Test status enum values."""
        assert MeetupStatus.DRAFT == "draft"
        assert MeetupStatus.PUBLISHED == "published"
        assert MeetupStatus.CANCELLED == "cancelled"


class TestSocialLink:
    """Test SocialLink model."""

    def test_create_social_link(self):
        """Test creating a social link."""
        link = SocialLink(platform="linkedin", url="https://linkedin.com/in/test")
        assert link.platform == "linkedin"
        assert link.url == "https://linkedin.com/in/test"

    def test_social_link_validation(self):
        """Test social link validation."""
        with pytest.raises(ValidationError):
            SocialLink(platform="", url="invalid-url")


class TestSpeaker:
    """Test Speaker model."""

    def test_create_speaker_minimal(self):
        """Test creating speaker with minimal data."""
        speaker = Speaker(id="john-doe", name="John Doe", bio="A Python developer")
        assert speaker.id == "john-doe"
        assert speaker.name == "John Doe"
        assert speaker.bio == "A Python developer"
        assert speaker.avatar_path is None
        assert speaker.social_links == []

    def test_create_speaker_full(self):
        """Test creating speaker with full data."""
        social_links = [
            SocialLink(platform="linkedin", url="https://linkedin.com/in/johndoe"),
            SocialLink(platform="github", url="https://github.com/johndoe"),
        ]
        speaker = Speaker(
            id="john-doe",
            name="John Doe",
            bio="A Python developer",
            avatar_path="/path/to/avatar.jpg",
            social_links=social_links,
        )
        assert speaker.avatar_path == "/path/to/avatar.jpg"
        assert len(speaker.social_links) == 2


class TestTalk:
    """Test Talk model."""

    def test_create_talk_minimal(self):
        """Test creating talk with minimal data."""
        talk = Talk(speaker_id="john-doe", title="Introduction to Python")
        assert talk.speaker_id == "john-doe"
        assert talk.title == "Introduction to Python"
        assert talk.description is None
        assert talk.title_en is None
        assert talk.language == Language.POLISH
        assert talk.youtube_id is None

    def test_create_talk_full(self):
        """Test creating talk with full data."""
        talk = Talk(
            speaker_id="john-doe",
            title="Wprowadzenie do Pythona",
            description="Podstawy programowania w Pythonie",
            title_en="Introduction to Python",
            language=Language.ENGLISH,
            youtube_id="abc123",
        )
        assert talk.title_en == "Introduction to Python"
        assert talk.language == Language.ENGLISH
        assert talk.youtube_id == "abc123"


class TestMeetup:
    """Test Meetup model."""

    def test_create_meetup_minimal(self):
        """Test creating meetup with minimal data."""
        meetup = Meetup(
            number="42",
            title="Meetup #42",
            date=date(2024, 6, 27),
            time="18:00",
            location="Test Venue",
        )
        assert meetup.number == "42"
        assert meetup.title == "Meetup #42"
        assert meetup.date == date(2024, 6, 27)
        assert meetup.time == "18:00"
        assert meetup.location == "Test Venue"
        assert meetup.talks == []
        assert meetup.sponsors == []
        assert meetup.status == MeetupStatus.DRAFT
        assert meetup.featured is False

    def test_create_meetup_full(self):
        """Test creating meetup with full data."""
        talk = Talk(speaker_id="john-doe", title="Test Talk")
        meetup = Meetup(
            number="42",
            title="Meetup #42",
            date=date(2024, 6, 27),
            time="18:00",
            location="Test Venue",
            talks=[talk],
            sponsors=["sponsor1", "sponsor2"],
            status=MeetupStatus.PUBLISHED,
            meetup_url="https://meetup.com/event/123",
            feedback_url="https://forms.gle/123",
            livestream_id="youtube123",
            tags=["python", "meetup"],
            featured=True,
        )
        assert len(meetup.talks) == 1
        assert len(meetup.sponsors) == 2
        assert meetup.status == MeetupStatus.PUBLISHED
        assert meetup.featured is True

    def test_meetup_properties(self):
        """Test meetup computed properties."""
        talk = Talk(speaker_id="john-doe", title="Test Talk")
        meetup = Meetup(
            number="42",
            title="Meetup #42",
            date=date(2024, 6, 27),
            time="18:00",
            location="Test Venue",
            talks=[talk],
        )
        assert meetup.has_talks is True
        assert meetup.talk_count == 1

        empty_meetup = Meetup(
            number="43",
            title="Meetup #43",
            date=date(2024, 6, 27),
            time="18:00",
            location="Test Venue",
        )
        assert empty_meetup.has_talks is False
        assert empty_meetup.talk_count == 0


class TestMeetupSheetRow:
    """Test MeetupSheetRow model for parsing meetup sheet data."""

    def test_parse_enabled_meetup(self):
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

        row = MeetupSheetRow.model_validate(data)
        assert row.meetup_id == "42"
        assert row.title == "Meetup #42"
        assert row.date == date(2024, 6, 27)
        assert row.time == "18:00"
        assert row.location == "Test Venue"
        assert row.enabled is True
        assert row.featured is True
        assert row.sponsors == ["sponsor1", "sponsor2"]
        assert row.tags == ["python", "meetup"]

    def test_parse_disabled_meetup(self):
        """Test parsing disabled meetup from sheet."""
        data = {
            "MEETUP_ID": "43",
            "TITLE": "Meetup #43",
            "DATE": "2024-07-27",
            "TIME": "18:00",
            "LOCATION": "Test Venue",
            "ENABLED": "FALSE",
        }

        row = MeetupSheetRow.model_validate(data)
        assert row.enabled is False

    def test_filter_enabled_meetups(self):
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

        enabled_row = MeetupSheetRow.model_validate(enabled_data)
        disabled_row = MeetupSheetRow.model_validate(disabled_data)

        all_rows = [enabled_row, disabled_row]
        enabled_only = [row for row in all_rows if row.enabled]

        assert len(enabled_only) == 1
        assert enabled_only[0].meetup_id == "42"


class TestTalkSheetRow:
    """Test TalkSheetRow model for parsing talk sheet data."""

    def test_parse_talk_from_sheet(self):
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

        row = TalkSheetRow.model_validate(data)
        assert row.meetup == "42"
        assert row.first_name == "John"
        assert row.last_name == "Doe"
        assert row.bio == "A Python developer"
        assert row.photo_url == "https://example.com/photo.jpg"
        assert row.talk_title == "Introduction to Python"
        assert row.talk_description == "Learn Python basics"
        assert row.language == "en"
        assert row.linkedin_url == "https://linkedin.com/in/johndoe"
        assert row.github_url == "https://github.com/johndoe"

    def test_parse_talk_minimal_data(self):
        """Test parsing talk with minimal required data."""
        data = {
            "Meetup": "42",
            "Imię": "John",
            "Nazwisko": "Doe",
            "Tytuł prezentacji": "Introduction to Python",
        }

        row = TalkSheetRow.model_validate(data)
        assert row.meetup == "42"
        assert row.first_name == "John"
        assert row.last_name == "Doe"
        assert row.talk_title == "Introduction to Python"
        assert row.bio == ""
        assert row.language == "pl"  # default

    def test_talk_validation_requires_meetup(self):
        """Test that talk validation requires meetup number."""
        data = {
            "Imię": "John",
            "Nazwisko": "Doe",
            "Tytuł prezentacji": "Introduction to Python",
        }

        with pytest.raises(ValidationError):
            TalkSheetRow.model_validate(data)
