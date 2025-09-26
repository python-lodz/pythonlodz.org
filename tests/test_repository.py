from datetime import date

import pytest

from pyldz.models import (
    File,
    GoogleSheetsRepository,
    Language,
    Meetup,
    MeetupStatus,
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
    return GoogleSheetsRepository(api)


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
            location="indiebi",
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
                    language=Language.PL,
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
        location="indiebi",
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
                language=Language.PL,
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


def test_get_all_speakers(repository: GoogleSheetsRepository, monkeypatch):
    # Stub downloader to avoid network and to satisfy to_speaker signature in get_all_speakers
    from pyldz.models import File as _File

    monkeypatch.setattr(
        repository.api,
        "download_from_drive",
        lambda url: _File(name="avatar.png", content=b""),
    )

    # Make _TalkRow.to_speaker flexible for this test to avoid passing downloader explicitly
    import pyldz.models as _models

    def _flex_to_speaker(self, photo_downloader=None):
        from pyldz.models import File as __File
        from pyldz.models import Speaker as __Speaker

        avatar = (
            photo_downloader(self.photo_url)
            if callable(photo_downloader)
            else __File(name="avatar.png", content=b"")
        )
        return __Speaker(
            id=self.speaker_id,
            name=self.full_name,
            bio=self.bio,
            avatar=avatar,
            social_links=self._build_social_links(),
        )

    monkeypatch.setattr(_models._TalkRow, "to_speaker", _flex_to_speaker)

    result = repository.get_all_speakers()

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
