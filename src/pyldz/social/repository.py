"""Load and persist page/content/spotkania/<nr>/social/ artifacts."""

import logging
from pathlib import Path

from ruamel.yaml import YAML

from pyldz.social.models import Post, PublishStatus, Schedule
from pyldz.social.posts_md import parse_posts_md

log = logging.getLogger(__name__)


class SocialRepository:
    def __init__(self, meetups_content_dir: Path):
        self.meetups_content_dir = meetups_content_dir

    def social_dir(self, meetup_id: str) -> Path:
        return self.meetups_content_dir / meetup_id / "social"

    def load_posts(self, meetup_id: str) -> dict[str, Post]:
        posts_file = self.social_dir(meetup_id) / "posts.md"
        return parse_posts_md(posts_file.read_text(encoding="utf-8"))

    def load_schedule(self, meetup_id: str) -> Schedule:
        yaml = YAML(typ="safe")
        data = yaml.load(self.social_dir(meetup_id) / "schedule.yaml")
        return Schedule.model_validate(data)

    def load_status(self, meetup_id: str) -> PublishStatus:
        status_file = self.social_dir(meetup_id) / "status.json"
        if not status_file.exists():
            return PublishStatus()
        return PublishStatus.model_validate_json(
            status_file.read_text(encoding="utf-8")
        )

    def save_status(self, meetup_id: str, status: PublishStatus) -> Path:
        status_file = self.social_dir(meetup_id) / "status.json"
        status_file.write_text(
            status.model_dump_json(indent=2) + "\n", encoding="utf-8"
        )
        log.info(f"Saved publish status: {status_file}")
        return status_file

    def meetups_with_schedule(self) -> list[str]:
        return sorted(
            path.parent.parent.name
            for path in self.meetups_content_dir.glob("*/social/schedule.yaml")
        )
