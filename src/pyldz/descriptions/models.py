"""Models for meetup descriptions."""

from pydantic import BaseModel


class AgendaItem(BaseModel):
    """Single agenda item."""

    time: str
    title: str


class MeetupDescriptions(BaseModel):
    """All descriptions for a meetup."""

    meetup_id: str
    meetup_com: str
    youtube_live: str
    youtube_recording: str
    chatgpt_prompt: str

