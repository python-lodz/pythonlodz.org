from __future__ import annotations

import datetime
import logging
from enum import Enum, StrEnum
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from pydantic import AnyHttpUrl, BaseModel, Field, computed_field, field_validator

from pyldz.config import GoogleSheetsConfig

log = logging.getLogger(__name__)


class Language(str, Enum):
    PL = "PL"
    EN = "EN"


class MeetupStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    CANCELLED = "cancelled"


class SocialLink(BaseModel):
    platform: str
    url: AnyHttpUrl


class Speaker(BaseModel):
    id: str
    name: str
    bio: str
    avatar_path: AnyHttpUrl
    social_links: list[SocialLink]


class Talk(BaseModel):
    speaker_id: str
    title: str
    description: str
    language: Language
    title_en: str | None
    youtube_id: str | None = None


class Meetup(BaseModel):
    meetup_id: str
    title: str
    date: datetime.date
    time: str
    location: str
    talks: list[Talk]
    sponsors: list[str]
    status: MeetupStatus = MeetupStatus.DRAFT
    meetup_url: AnyHttpUrl | None = None
    feedback_url: AnyHttpUrl | None = None
    livestream_id: str | None = None
    tags: list[str] = Field(default_factory=list)
    featured: bool = False

    @computed_field
    @property
    def has_talks(self) -> bool:
        return len(self.talks) > 0

    @computed_field
    @property
    def talk_count(self) -> int:
        return len(self.talks)

    @computed_field
    @property
    def formatted_date_polish(self) -> str:
        return self._format_date_with_polish_day_name()

    def _format_date_with_polish_day_name(self) -> str:
        polish_days = {
            0: "PONIEDZIAŁEK",
            1: "WTOREK",
            2: "ŚRODA",
            3: "CZWARTEK",
            4: "PIĄTEK",
            5: "SOBOTA",
            6: "NIEDZIELA",
        }
        day_name = polish_days[self.date.weekday()]
        return f"{day_name} {self.date.strftime('%d.%m.%Y')}r. godz. {self.time}"


class MeetupType(StrEnum):
    TALKS = "talks"
    SUMMER_EDITION = "summer_edition"


class _MeetupSheetRow(BaseModel):
    meetup_id: str
    type: MeetupType
    date: datetime.date
    time: str = "18:00"
    location: str
    enabled: bool
    sponsors: list[str]
    meetup_url: AnyHttpUrl | None
    feedback_url: AnyHttpUrl | None
    livestream_id: str | None

    @computed_field
    @property
    def title(self) -> str:
        return f"Meetup {self.meetup_id}"

    @field_validator("sponsors", mode="before")
    @classmethod
    def split_comma_separated_values(cls, v) -> list[str]:
        if isinstance(v, str) and v.strip():
            return [item.strip() for item in v.split(",") if item.strip()]
        return []

    @field_validator("meetup_url", "feedback_url", "livestream_id", mode="before")
    @classmethod
    def convert_empty_string_to_none(cls, v) -> str | None:
        if isinstance(v, str) and v.strip() == "":
            return None
        return v

    def to_meetup(self, talks: list[Talk] | None = None) -> Meetup:
        return Meetup(
            meetup_id=self.meetup_id,
            title=self.title,
            date=self.date,
            time=self.time,
            location=self.location,
            talks=talks or [],
            sponsors=self.sponsors,
            meetup_url=self.meetup_url,
            feedback_url=self.feedback_url,
            livestream_id=self.livestream_id,
            status=MeetupStatus.PUBLISHED if self.enabled else MeetupStatus.DRAFT,
        )


class _TalkSheetRow(BaseModel):
    meetup_id: str
    first_name: str
    last_name: str
    bio: str
    photo_url: AnyHttpUrl
    talk_title: str
    talk_description: str
    language: str
    talk_title_en: str | None
    facebook_url: AnyHttpUrl | None
    linkedin_url: AnyHttpUrl | None
    youtube_url: AnyHttpUrl | None
    other_urls: list[AnyHttpUrl] = []

    @field_validator("talk_title_en", "talk_description", mode="before")
    @classmethod
    def strip_text_fields(cls, v) -> str:
        if v is None:
            return ""
        return str(v).strip()

    @computed_field
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    @computed_field
    @property
    def speaker_id(self) -> str:
        return self._generate_speaker_id_from_name()

    def _generate_speaker_id_from_name(self) -> str:
        import re

        from unidecode import unidecode

        name = self.full_name.lower()
        name = unidecode(name)
        name = re.sub(r"[^a-z0-9\s-]", "", name)
        name = re.sub(r"\s+", "-", name)
        return name.strip("-")

    def to_speaker(self) -> Speaker:
        return Speaker(
            id=self.speaker_id,
            name=self.full_name,
            bio=self.bio,
            avatar_path=self.photo_url,
            social_links=self._build_social_links(),
        )

    @field_validator(
        "talk_title_en",
        "facebook_url",
        "linkedin_url",
        "youtube_url",
        mode="before",
    )
    @classmethod
    def convert_empty_url_to_none(cls, v) -> str | None:
        if isinstance(v, str) and v.strip() == "":
            return None
        return v

    @field_validator("other_urls", mode="before")
    @classmethod
    def split_comma_separated_values(cls, v) -> list[str]:
        if isinstance(v, str) and v.strip():
            return [item.strip() for item in v.split(",") if item.strip()]
        return []

    def _build_social_links(self) -> list[SocialLink]:
        social_links = []

        if self.facebook_url:
            social_links.append(SocialLink(platform="facebook", url=self.facebook_url))
        if self.linkedin_url:
            social_links.append(SocialLink(platform="linkedin", url=self.linkedin_url))
        if self.youtube_url:
            social_links.append(SocialLink(platform="youtube", url=self.youtube_url))

        for other in self.other_urls:
            social_links.append(SocialLink(platform="website", url=other))

        return social_links

    def to_talk(self) -> Talk:
        return Talk(
            speaker_id=self.speaker_id,
            title=self.talk_title,
            description=self.talk_description,
            title_en=self.talk_title_en,
            language=Language.EN if self.language == "en" else Language.PL,
        )


class GoogleSheetsRepository:
    def __init__(self, config: GoogleSheetsConfig):
        self.config = config
        self.scopes = (
            "https://www.googleapis.com/auth/spreadsheets.readonly",
            "https://www.googleapis.com/auth/drive.readonly",
        )

    def _get_credentials(self) -> Credentials:
        if not self.config.credentials_path.exists():
            raise FileNotFoundError(
                f"Credentials file not found: {self.config.credentials_path}"
            )

        credentials = None

        if self.config.token_cache_path.exists():
            credentials = Credentials.from_authorized_user_file(
                str(self.config.token_cache_path), self.scopes
            )
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())

        if credentials is None or not credentials.valid:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(self.config.credentials_path), self.scopes
            )
            credentials = flow.run_local_server(port=0)

        self.config.token_cache_path.write_text(credentials.to_json())
        return credentials

    def _fetch_sheet_data(self, sheet_name: str) -> list[dict]:
        credentials = self._get_credentials()
        sheets = build("sheets", "v4", credentials=credentials, cache_discovery=False)

        range_name = f"{sheet_name}!A1:ZZ"

        sheet_result = (
            sheets.spreadsheets()
            .values()
            .get(
                spreadsheetId=self.config.sheet_id,
                range=range_name,
                majorDimension="ROWS",
            )
            .execute()
        )

        raw_rows = sheet_result.get("values", [])

        header: dict = raw_rows[0]
        result: list[dict] = []

        for row in raw_rows[1:]:
            padded_row = row + [""] * (len(header) - len(row))
            result.append(dict(zip(header, padded_row)))

        return result

    def fetch_meetups_data(self) -> list[_MeetupSheetRow]:
        rows = self._fetch_sheet_data(self.config.meetups_sheet_name)
        return [_MeetupSheetRow.model_validate(row) for row in rows]

    def fetch_talks_data(self) -> list[_TalkSheetRow]:
        rows = self._fetch_sheet_data(self.config.talks_sheet_name)
        return [_TalkSheetRow.model_validate(row) for row in rows]

    def _get_enabled_meetups(
        self, meetups_data: list[dict[str, Any]]
    ) -> list[_MeetupSheetRow]:
        enabled_meetups = []

        for meetup_data in meetups_data:
            meetup_row = _MeetupSheetRow.model_validate(meetup_data)
            if meetup_row.enabled:
                enabled_meetups.append(meetup_row)

        return enabled_meetups

    def _get_talks_for_meetup(
        self, meetup_id: str, talks_data: list[_TalkSheetRow]
    ) -> list[Talk]:
        return [
            talk_row.to_talk()
            for talk_row in talks_data
            if talk_row.meetup_id == meetup_id
        ]

    def get_speakers_for_meetup(
        self, meetup_id: str, talks_data: list[dict[str, Any]]
    ) -> list[Speaker]:
        speakers = []
        seen_speaker_ids = set()

        for talk_data in talks_data:
            if talk_data.get("Meetup") == meetup_id:
                try:
                    talk_row = _TalkSheetRow.model_validate(talk_data)

                    if talk_row.speaker_id not in seen_speaker_ids:
                        speaker = talk_row.to_speaker()
                        speakers.append(speaker)
                        seen_speaker_ids.add(talk_row.speaker_id)

                except Exception as e:
                    log.error(
                        "Error parsing speaker data for meetup %s: %s", meetup_id, e
                    )
                    continue

        return speakers

    def get_meetup_by_id(self, meetup_id: str) -> Meetup | None:
        meetups_data: list[_MeetupSheetRow] = self.fetch_meetups_data()

        meetup: _MeetupSheetRow | None = next(
            filter(lambda m: m.meetup_id == meetup_id, meetups_data), None
        )
        if not meetup or not meetup.enabled:
            return None

        talks_data: list[_TalkSheetRow] = self.fetch_talks_data()

        talks = self._get_talks_for_meetup(meetup_id, talks_data)

        return meetup.to_meetup(talks)

    def get_all_enabled_meetups(self) -> list[Meetup]:
        meetups_data: list[_MeetupSheetRow] = self.fetch_meetups_data()
        talks_data: list[_TalkSheetRow] = self.fetch_talks_data()

        meetups = []
        for meetup_row in meetups_data:
            if not meetup_row.enabled:
                continue

            talks: list[Talk] = self._get_talks_for_meetup(
                meetup_row.meetup_id, talks_data
            )
            meetup = meetup_row.to_meetup(talks)
            meetups.append(meetup)

        return meetups

    def get_all_speakers(self) -> list[Speaker]:
        talks_data = self.fetch_talks_data()
        meetups_data = self.fetch_meetups_data()

        enabled_meetup_ids = {
            meetup.meetup_id for meetup in meetups_data if meetup.enabled
        }

        speakers = []
        seen_speaker_ids = set()

        for talk_data in talks_data:
            if talk_data.meetup_id in enabled_meetup_ids:
                talk_row = _TalkSheetRow.model_validate(talk_data)

                if talk_row.speaker_id not in seen_speaker_ids:
                    speaker = talk_row.to_speaker()
                    speakers.append(speaker)
                    seen_speaker_ids.add(talk_row.speaker_id)

        return speakers
