"""Tests for meetup descriptions generation."""

from datetime import date
from pathlib import Path

import pytest

from pyldz.descriptions.generators import (
    AGENDA_ONE_TALK,
    AGENDA_TWO_TALKS,
    MeetupDescriptionGenerator,
    SocialMediaLinks,
)
from pyldz.descriptions.models import MeetupDescriptions
from pyldz.descriptions.repository import DescriptionRepository
from pyldz.models import Language, Meetup, MultiLanguage, Speaker, Talk


@pytest.fixture
def sample_location():
    return MultiLanguage(
        pl="IndieBI, Piotrkowska 157A, budynek Hi Piotrkowska",
        en="IndieBI, Piotrkowska 157A, building Hi Piotrkowska",
    )


@pytest.fixture
def sample_talk():
    return Talk(
        speaker_id="john-doe",
        title="Introduction to Clean Architecture",
        description="Learn how to structure your Python applications using clean architecture principles.",
        language=Language.PL,
        title_en="Introduction to Clean Architecture",
    )


@pytest.fixture
def sample_speaker():
    from pyldz.models import File

    return Speaker(
        id="john-doe",
        name="John Doe",
        bio="A Python developer",
        avatar=File.no_photo(),
        social_links=[],
    )


@pytest.fixture
def sample_meetup_two_talks(sample_location):
    talk1 = Talk(
        speaker_id="john-doe",
        title="Clean Architecture",
        description="Learn clean architecture.",
        language=Language.PL,
        title_en="Clean Architecture",
    )
    talk2 = Talk(
        speaker_id="jane-smith",
        title="Python Visualization",
        description="Learn visualization in Python.",
        language=Language.PL,
        title_en="Python Visualization",
    )

    return Meetup(
        meetup_id="59",
        title="Meetup #59",
        date=date(2025, 9, 24),
        time="18:00",
        location=sample_location,
        language=Language.PL,
        talks=[talk1, talk2],
        sponsors=["indiebi", "sunscrapers"],
    )


@pytest.fixture
def sample_meetup_one_talk(sample_location):
    talk = Talk(
        speaker_id="john-doe",
        title="Clean Architecture",
        description="Learn clean architecture.",
        language=Language.PL,
        title_en="Clean Architecture",
    )

    return Meetup(
        meetup_id="60",
        title="Meetup #60",
        date=date(2025, 10, 22),
        time="18:00",
        location=sample_location,
        language=Language.PL,
        talks=[talk],
        sponsors=["indiebi"],
    )


def test_agenda_two_talks():
    """Test agenda for two talks."""
    assert len(AGENDA_TWO_TALKS) == 5
    assert AGENDA_TWO_TALKS[0].time == "18:00"
    assert AGENDA_TWO_TALKS[0].title == "Rozpoczęcie i sprawy organizacyjne"
    assert AGENDA_TWO_TALKS[4].time == "20:15"
    assert AGENDA_TWO_TALKS[4].title == "Networking"


def test_agenda_one_talk():
    """Test agenda for one talk."""
    assert len(AGENDA_ONE_TALK) == 3
    assert AGENDA_ONE_TALK[0].time == "18:00"
    assert AGENDA_ONE_TALK[2].time == "19:00"
    assert AGENDA_ONE_TALK[2].title == "Przerwa i networking"


def test_social_media_links():
    """Test social media links are defined."""
    assert SocialMediaLinks.OFFICIAL_WEBSITE == "https://pythonlodz.org"
    assert SocialMediaLinks.DISCORD == "https://discord.gg/jbvWBMufEf"
    assert SocialMediaLinks.FACEBOOK == "https://www.facebook.com/pythonlodz"


def test_description_generator_two_talks(
    sample_meetup_two_talks, sample_speaker, tmp_path
):
    """Test description generator with two talks."""
    generator = MeetupDescriptionGenerator(
        sample_meetup_two_talks, [sample_speaker], tmp_path
    )

    assert generator.meetup == sample_meetup_two_talks
    assert len(generator.speakers) == 1
    assert generator._get_agenda() == AGENDA_TWO_TALKS


def test_description_generator_one_talk(
    sample_meetup_one_talk, sample_speaker, tmp_path
):
    """Test description generator with one talk."""
    generator = MeetupDescriptionGenerator(
        sample_meetup_one_talk, [sample_speaker], tmp_path
    )

    assert generator._get_agenda() == AGENDA_ONE_TALK


def test_generate_meetup_com(sample_meetup_two_talks, sample_speaker, tmp_path):
    """Test meetup.com description generation."""
    generator = MeetupDescriptionGenerator(
        sample_meetup_two_talks, [sample_speaker], tmp_path
    )

    description = generator.generate_meetup_com()

    assert "Cześć!" in description
    assert "24 września 2025" in description
    assert "18:00" in description
    assert "IndieBI" in description
    assert "Clean Architecture" in description
    assert "Dołącz do nas na Discordzie!" in description
    assert SocialMediaLinks.DISCORD in description


def test_generate_youtube_live(sample_meetup_two_talks, sample_speaker, tmp_path):
    """Test YouTube live description generation."""
    generator = MeetupDescriptionGenerator(
        sample_meetup_two_talks, [sample_speaker], tmp_path
    )

    description = generator.generate_youtube_live()

    assert "🔴 LIVE" in description
    assert "Meetup #59" in description
    assert "24 września 2025" in description
    assert "Agenda:" in description
    assert "18:00 - Rozpoczęcie" in description
    assert SocialMediaLinks.OFFICIAL_WEBSITE in description
    assert SocialMediaLinks.MEETUP in description


def test_generate_youtube_recording(sample_meetup_two_talks, sample_speaker, tmp_path):
    """Test YouTube recording description generation."""
    generator = MeetupDescriptionGenerator(
        sample_meetup_two_talks, [sample_speaker], tmp_path
    )

    description = generator.generate_youtube_recording()

    assert "Python Łódź Meetup #59" in description
    assert "24 września 2025" in description
    assert "Prezentacje:" in description
    assert SocialMediaLinks.OFFICIAL_WEBSITE in description


def test_generate_youtube_recording_talks(
    sample_meetup_two_talks, sample_speaker, tmp_path
):
    """Test generating YouTube recording descriptions for each talk."""
    generator = MeetupDescriptionGenerator(
        sample_meetup_two_talks, [sample_speaker], tmp_path
    )

    talks = generator.generate_youtube_recording_talks()

    assert len(talks) == 2
    assert talks[0].title == "Python Łódź #59 - Clean Architecture"
    assert talks[1].title == "Python Łódź #59 - Python Visualization"
    assert "Agenda:" in talks[0].description
    assert "Linki do społeczności:" in talks[0].description
    assert "John Doe" in talks[0].description


def test_generate_chatgpt_prompt(sample_meetup_two_talks, sample_speaker, tmp_path):
    """Test ChatGPT prompt generation."""
    generator = MeetupDescriptionGenerator(
        sample_meetup_two_talks, [sample_speaker], tmp_path
    )

    prompt = generator.generate_chatgpt_prompt()

    assert "Super Prompt do Generowania Postów" in prompt
    assert "Meetup #59" in prompt
    assert "24 września 2025" in prompt
    assert "Instrukcje do Generowania Postów" in prompt
    assert "Posty o Prelegentach" in prompt
    assert "Posty o Sponsorach" in prompt
    assert "Posty Informacyjne" in prompt
    assert SocialMediaLinks.OFFICIAL_WEBSITE in prompt


def test_generate_all(sample_meetup_two_talks, sample_speaker, tmp_path):
    """Test generating all descriptions."""
    generator = MeetupDescriptionGenerator(
        sample_meetup_two_talks, [sample_speaker], tmp_path
    )

    descriptions = generator.generate_all()

    assert isinstance(descriptions, MeetupDescriptions)
    assert descriptions.meetup_id == "59"
    assert len(descriptions.meetup_com) > 0
    assert len(descriptions.youtube_live) > 0
    assert len(descriptions.youtube_recording) > 0
    assert len(descriptions.youtube_recording_talks) == 2
    assert len(descriptions.chatgpt_prompt) > 0


def test_description_repository_save_all(
    sample_meetup_two_talks, sample_speaker, tmp_path
):
    """Test saving all descriptions to files."""
    generator = MeetupDescriptionGenerator(
        sample_meetup_two_talks, [sample_speaker], tmp_path
    )
    descriptions = generator.generate_all()

    repo = DescriptionRepository(tmp_path)
    created_files = repo.save_all("59", descriptions)

    # 4 main files + 2 talk files = 6 files
    assert len(created_files) == 6
    assert all(f.exists() for f in created_files)

    descriptions_dir = tmp_path / "59" / "descriptions"
    assert (descriptions_dir / "meetup-com.md").exists()
    assert (descriptions_dir / "youtube-live.md").exists()
    assert (descriptions_dir / "youtube-recording.md").exists()
    assert (descriptions_dir / "chatgpt-prompt.md").exists()

    # Check talk files
    talks_dir = descriptions_dir / "youtube-talks"
    assert talks_dir.exists()
    assert (talks_dir / "talk-1.md").exists()
    assert (talks_dir / "talk-2.md").exists()

    # Verify content
    meetup_com_content = (descriptions_dir / "meetup-com.md").read_text()
    assert "Cześć!" in meetup_com_content
