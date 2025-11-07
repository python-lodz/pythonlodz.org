from datetime import date
from pathlib import Path

import pytest

from pyldz.models import (
    File,
    GoogleSheetsRepository,
    Language,
    Location,
    LocationRepository,
    Meetup,
    MeetupStatus,
    MultiLanguage,
    SocialLink,
    Speaker,
    Talk,
)


class FakeGoogleSheetsAPI:
    def __init__(self, data: dict):
        self.data = data

    def fetch_data(self, table_name: str) -> list[dict]:
        return self.data[table_name]

    def download_from_drive(self, file_url):
        from pyldz.models import File

        return File(name="avatar.png", content=b"")


@pytest.fixture
def fake_meetups():
    return [
        {
            "meetup_id": "58",
            "date": "2025-05-28",
            "type": "talks",
            "enabled": "TRUE",
            "meetup_url": "https://www.meetup.com/python-lodz/events/306971418/",
            "feedback_url": "",
            "livestream_id": "",
            "sponsors": "indiebi, sunscrapers",
            "location": "indiebi",
            "language": "PL",
        },
        {
            "meetup_id": "59",
            "date": "2025-07-30",
            "type": "summer_edition",
            "enabled": "FALSE",
            "meetup_url": "",
            "feedback_url": "",
            "livestream_id": "",
            "sponsors": "indiebi, sunscrapers",
            "location": "indiebi",
            "language": "PL",
        },
    ]


@pytest.fixture
def fake_talks():
    return [
        {
            "meetup_id": "58",
            "created_at": "2025-04-25 11:29:01",
            "email": "speaker1@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "bio": "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
            "photo_url": "https://i.pravatar.cc/300?img=68",
            "talk_title": "Example Talk Title 1",
            "talk_description": "Example talk description 1",
            "facebook_url": "https://facebook.com/example1",
            "linkedin_url": "https://linkedin.com/in/example1",
            "youtube_url": "https://youtube.com/@example1",
            "other_urls": "https://example1.com",
            "agrrements": "Example agreements text",
            "talk_title_en": "Example Talk Title 1 in English",
            "language": "PL",
        },
        {
            "meetup_id": "58",
            "created_at": "2025-04-22 12:49:57",
            "email": "speaker2@example.com",
            "first_name": "Jane",
            "last_name": "Smith",
            "bio": "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
            "photo_url": "https://i.pravatar.cc/300?img=49",
            "talk_title": "Example Talk Title 2 in English",
            "talk_description": "Example talk description 2",
            "facebook_url": "",
            "linkedin_url": "https://linkedin.com/in/example2",
            "youtube_url": "https://youtube.com/@example2",
            "other_urls": "https://example2.com",
            "agrrements": "Example agreements text",
            "talk_title_en": "Example Talk Title 2 in English",
            "language": "EN",
        },
        {
            "meetup_id": "60",
            "created_at": "2025-04-22 18:53:40",
            "email": "speaker3@example.com",
            "first_name": "Bob",
            "last_name": "Brown",
            "bio": "Ut enim ad minim veniam, quis nostrud exercitation ullamco.",
            "photo_url": "https://i.pravatar.cc/300?img=13",
            "talk_title": "Example Talk Title 3",
            "talk_description": "Example talk description 3",
            "facebook_url": "https://facebook.com/example3",
            "linkedin_url": "https://linkedin.com/in/example3",
            "youtube_url": "",
            "other_urls": "https://example3.com",
            "agrrements": "Example agreements text",
            "talk_title_en": "Example Talk Title 3 in English",
            "language": "PL",
        },
    ]


@pytest.fixture
def repository(fake_meetups, fake_talks):
    data = {"meetups": fake_meetups, "talks": fake_talks}
    api = FakeGoogleSheetsAPI(data)

    # Create a mock LocationRepository with test location
    location_repo = LocationRepository(Path("/tmp/nonexistent"))
    location_repo._locations_cache["indiebi"] = Location(
        name=MultiLanguage(
            pl="IndieBI, Piotrkowska 157A, budynek Hi Piotrkowska",
            en="IndieBI, Piotrkowska 157A, building Hi Piotrkowska",
        )
    )

    return GoogleSheetsRepository(api, location_repo)


def test_repository_fetch_meetups_data(repository: GoogleSheetsRepository):
    result: list[Meetup] = repository.get_all_enabled_meetups()
    assert result == [
        Meetup(
            meetup_id="58",
            title="Meetup #58",
            date=date(2025, 5, 28),
            time="18:00",
            status=MeetupStatus.PUBLISHED,
            meetup_url="https://www.meetup.com/python-lodz/events/306971418/",
            feedback_url=None,
            livestream_id=None,
            sponsors=["indiebi", "sunscrapers"],
            location=MultiLanguage(
                pl="IndieBI, Piotrkowska 157A, budynek Hi Piotrkowska",
                en="IndieBI, Piotrkowska 157A, building Hi Piotrkowska",
            ),
            language=Language.PL,
            talks=[
                Talk(
                    speaker_id="john-doe",
                    title="Example Talk Title 1",
                    description="Example talk description 1",
                    language=Language.PL,
                    title_en="Example Talk Title 1 in English",
                    youtube_id=None,
                ),
                Talk(
                    speaker_id="jane-smith",
                    title="Example Talk Title 2 in English",
                    description="Example talk description 2",
                    language=Language.EN,
                    title_en="Example Talk Title 2 in English",
                    youtube_id=None,
                ),
            ],
        )
    ]


def test_get_meetup_by_id_existing_enabled_meetup(repository: GoogleSheetsRepository):
    result = repository.get_meetup_by_id("58")

    expected = Meetup(
        meetup_id="58",
        title="Meetup #58",
        date=date(2025, 5, 28),
        time="18:00",
        status=MeetupStatus.PUBLISHED,
        meetup_url="https://www.meetup.com/python-lodz/events/306971418/",
        feedback_url=None,
        livestream_id=None,
        sponsors=["indiebi", "sunscrapers"],
        location=MultiLanguage(
            pl="IndieBI, Piotrkowska 157A, budynek Hi Piotrkowska",
            en="IndieBI, Piotrkowska 157A, building Hi Piotrkowska",
        ),
        language=Language.PL,
        talks=[
            Talk(
                speaker_id="john-doe",
                title="Example Talk Title 1",
                description="Example talk description 1",
                language=Language.PL,
                title_en="Example Talk Title 1 in English",
                youtube_id=None,
            ),
            Talk(
                speaker_id="jane-smith",
                title="Example Talk Title 2 in English",
                description="Example talk description 2",
                language=Language.EN,
                title_en="Example Talk Title 2 in English",
                youtube_id=None,
            ),
        ],
    )

    assert result == expected


def test_get_meetup_by_id_disabled_meetup(repository: GoogleSheetsRepository):
    result = repository.get_meetup_by_id("59")
    assert result is None


def test_get_meetup_by_id_nonexistent_meetup(repository: GoogleSheetsRepository):
    result = repository.get_meetup_by_id("999")
    assert result is None


def test_get_speakers_for_meetup_with_speakers(repository: GoogleSheetsRepository):
    # We need to get the talks data first to pass to the method
    talks_data = repository._fetch_talks_data()
    result = repository.get_speakers_for_meetup("58", talks_data)

    expected = [
        Speaker(
            id="john-doe",
            name="John Doe",
            bio="Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
            avatar=File(name="avatar.png", content=b""),
            social_links=[
                SocialLink(platform="facebook", url="https://facebook.com/example1"),
                SocialLink(platform="linkedin", url="https://linkedin.com/in/example1"),
                SocialLink(platform="youtube", url="https://youtube.com/@example1"),
                SocialLink(platform="website", url="https://example1.com"),
            ],
        ),
        Speaker(
            id="jane-smith",
            name="Jane Smith",
            bio="Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
            avatar=File(name="avatar.png", content=b""),
            social_links=[
                SocialLink(platform="linkedin", url="https://linkedin.com/in/example2"),
                SocialLink(platform="youtube", url="https://youtube.com/@example2"),
                SocialLink(platform="website", url="https://example2.com"),
            ],
        ),
    ]

    assert result == expected


def test_get_speakers_for_meetup_no_speakers(repository: GoogleSheetsRepository):
    talks_data = repository._fetch_talks_data()
    result = repository.get_speakers_for_meetup("999", talks_data)
    assert result == []


def test_get_speakers_for_meetup_different_meetup(repository: GoogleSheetsRepository):
    talks_data = repository._fetch_talks_data()
    result = repository.get_speakers_for_meetup("60", talks_data)

    expected = [
        Speaker(
            id="bob-brown",
            name="Bob Brown",
            bio="Ut enim ad minim veniam, quis nostrud exercitation ullamco.",
            avatar=File(name="avatar.png", content=b""),
            social_links=[
                SocialLink(platform="facebook", url="https://facebook.com/example3"),
                SocialLink(platform="linkedin", url="https://linkedin.com/in/example3"),
                SocialLink(platform="website", url="https://example3.com"),
            ],
        ),
    ]

    assert result == expected
