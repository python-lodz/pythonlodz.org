"""Orchestrates due computation, transforms, and channel adapters."""

import datetime
import logging
from pathlib import Path

from pydantic import BaseModel
from zoneinfo import ZoneInfo

from pyldz.social.models import (
    AUTOMATED_CHANNELS,
    Channel,
    PublishRecord,
    PublishStatus,
    Schedule,
    ScheduleItem,
)
from pyldz.social.repository import SocialRepository
from pyldz.social.transforms import render_text

log = logging.getLogger(__name__)


class PlannedPublication(BaseModel):
    meetup_id: str
    post_id: str
    channel: Channel
    scheduled: datetime.datetime
    text: str
    image_url: str | None
    image_path: str | None
    ig_tagged: list[str]


class PublishOutcome(BaseModel):
    post_id: str
    channel: Channel
    ok: bool
    external_id: str | None = None
    error: str | None = None


def due_items(
    schedule: Schedule, status: PublishStatus, now: datetime.datetime
) -> list[tuple[ScheduleItem, Channel]]:
    """Everything scheduled in the past and not yet published (catch-up safe)."""
    tz = ZoneInfo(schedule.timezone)
    due: list[tuple[ScheduleItem, Channel]] = []
    for item in schedule.posts:
        if item.scheduled.replace(tzinfo=tz) > now:
            continue
        for channel in item.channels:
            if channel not in AUTOMATED_CHANNELS:
                continue
            if status.is_published(item.post, channel):
                continue
            due.append((item, channel))
    return due


class Publisher:
    def __init__(
        self,
        repository: SocialRepository,
        adapters: dict[Channel, object],
        site_base_url: str,
    ):
        self.repository = repository
        self.adapters = adapters
        self.site_base_url = site_base_url

    def plan(
        self, meetup_id: str, now: datetime.datetime
    ) -> list[PlannedPublication]:
        posts = self.repository.load_posts(meetup_id)
        schedule = self.repository.load_schedule(meetup_id)
        status = self.repository.load_status(meetup_id)
        planned: list[PlannedPublication] = []
        for item, channel in due_items(schedule, status, now):
            post = posts[item.post]
            planned.append(
                PlannedPublication(
                    meetup_id=meetup_id,
                    post_id=item.post,
                    channel=channel,
                    scheduled=item.scheduled,
                    text=render_text(post, channel),
                    image_url=self._image_url(meetup_id, item),
                    image_path=self._image_path(meetup_id, item),
                    ig_tagged=item.ig_tagged,
                )
            )
        return planned

    def publish_due(
        self, meetup_id: str, now: datetime.datetime
    ) -> list[PublishOutcome]:
        status = self.repository.load_status(meetup_id)
        outcomes: list[PublishOutcome] = []
        for planned in self.plan(meetup_id, now):
            try:
                external_id = self._send(planned)
            except Exception as exc:  # publikuj resztę, raportuj błąd
                log.error(f"FAILED {planned.post_id}:{planned.channel}: {exc}")
                outcomes.append(
                    PublishOutcome(
                        post_id=planned.post_id,
                        channel=planned.channel,
                        ok=False,
                        error=str(exc),
                    )
                )
                continue
            status.mark(
                planned.post_id,
                planned.channel,
                PublishRecord(at=now, external_id=external_id),
            )
            self.repository.save_status(meetup_id, status)
            log.info(f"Published {planned.post_id}:{planned.channel} -> {external_id}")
            outcomes.append(
                PublishOutcome(
                    post_id=planned.post_id,
                    channel=planned.channel,
                    ok=True,
                    external_id=external_id,
                )
            )
        return outcomes

    def _send(self, planned: PlannedPublication) -> str | None:
        adapter = self.adapters.get(planned.channel)
        if adapter is None:
            raise RuntimeError(
                f"Brak konfiguracji kanału '{planned.channel}' "
                f"(sekrety w env — patrz SocialSettings)"
            )
        if planned.channel == Channel.FACEBOOK:
            return adapter.publish(planned.text, image_url=planned.image_url)
        if planned.channel == Channel.INSTAGRAM:
            if planned.image_url is None:
                raise ValueError(
                    f"Post '{planned.post_id}' na Instagram wymaga grafiki "
                    f"(image w schedule.yaml)"
                )
            return adapter.publish(
                planned.text,
                image_url=planned.image_url,
                user_tags=planned.ig_tagged,
            )
        image_path = Path(planned.image_path) if planned.image_path else None
        return adapter.publish(planned.text, image_path=image_path)

    def _image_url(self, meetup_id: str, item: ScheduleItem) -> str | None:
        if item.image is None:
            return None
        return f"{self.site_base_url}/spotkania/{meetup_id}/social/{item.image}"

    def _image_path(self, meetup_id: str, item: ScheduleItem) -> str | None:
        if item.image is None:
            return None
        return str(self.repository.social_dir(meetup_id) / item.image)
