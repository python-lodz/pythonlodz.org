"""Domain models for the social media publishing system (gk-sm)."""

import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class Channel(StrEnum):
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    DISCORD = "discord"
    LINKEDIN = "linkedin"


# LinkedIn goes into the paste pack (linkedin-paste.md), never through the publisher.
AUTOMATED_CHANNELS: tuple[Channel, ...] = (
    Channel.FACEBOOK,
    Channel.INSTAGRAM,
    Channel.DISCORD,
)


class Post(BaseModel):
    """One canonical post text with rare per-platform overrides."""

    id: str
    text: str
    overrides: dict[Channel, str] = Field(default_factory=dict)

    def text_for(self, channel: Channel) -> str:
        return self.overrides.get(channel, self.text)


class ScheduleItem(BaseModel):
    post: str
    channels: list[Channel]
    scheduled: datetime.datetime  # naive, local time in Schedule.timezone
    image: str | None = None  # path relative to social/, e.g. images/final/x.png
    ig_tagged: list[str] = Field(default_factory=list)  # IG handles without @


class Schedule(BaseModel):
    model_config = ConfigDict(coerce_numbers_to_str=True)

    meetup: str
    timezone: str = "Europe/Warsaw"
    posts: list[ScheduleItem]


class PublishRecord(BaseModel):
    at: datetime.datetime
    external_id: str | None = None


class PublishStatus(BaseModel):
    """Contents of status.json — the idempotency ledger."""

    published: dict[str, PublishRecord] = Field(default_factory=dict)

    @staticmethod
    def key(post_id: str, channel: Channel) -> str:
        return f"{post_id}:{channel}"

    def is_published(self, post_id: str, channel: Channel) -> bool:
        return self.key(post_id, channel) in self.published

    def mark(self, post_id: str, channel: Channel, record: PublishRecord) -> None:
        self.published[self.key(post_id, channel)] = record
