"""Models for meetup descriptions."""

from pydantic import BaseModel


class AgendaItem(BaseModel):
    """Single agenda item."""

    time: str
    title: str


class YouTubeRecordingDescription(BaseModel):
    """YouTube recording description for a single talk."""

    title: str
    description: str


class MeetupDescriptions(BaseModel):
    """All descriptions for a meetup."""

    meetup_id: str
    meetup_com: str
    youtube_live: str
    youtube_recording: str
    youtube_recording_talks: list[YouTubeRecordingDescription]
    chatgpt_prompt: str
