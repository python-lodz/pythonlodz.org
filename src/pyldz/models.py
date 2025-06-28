import datetime as dt
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, computed_field, field_validator


class Language(str, Enum):
    POLISH = "pl"
    ENGLISH = "en"


class MeetupStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    CANCELLED = "cancelled"


class SocialLink(BaseModel):
    platform: str
    url: str

    @field_validator("url")
    @classmethod
    def ensure_url_has_protocol(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v


class Speaker(BaseModel):
    id: str
    name: str
    bio: str
    avatar_path: Optional[str] = None
    social_links: List[SocialLink] = Field(default_factory=list)


class Talk(BaseModel):
    speaker_id: str
    title: str
    description: Optional[str] = None
    title_en: Optional[str] = None
    language: Language = Language.POLISH
    youtube_id: Optional[str] = None


class Meetup(BaseModel):
    number: str
    title: str
    date: dt.date
    time: str
    location: str
    talks: List[Talk] = Field(default_factory=list)
    sponsors: List[str] = Field(default_factory=list)
    status: MeetupStatus = MeetupStatus.DRAFT
    meetup_url: Optional[str] = None
    feedback_url: Optional[str] = None
    livestream_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
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


class MeetupSheetRow(BaseModel):
    meetup_id: str = Field(alias="MEETUP_ID")
    title: str = Field(alias="TITLE")
    date: dt.date = Field(alias="DATE")
    time: str = Field(alias="TIME")
    location: str = Field(alias="LOCATION")
    enabled: bool = Field(alias="ENABLED")
    meetup_url: Optional[str] = Field(default=None, alias="MEETUP_URL")
    feedback_url: Optional[str] = Field(default=None, alias="FEEDBACK_URL")
    livestream_id: Optional[str] = Field(default=None, alias="LIVESTREAM_ID")
    sponsors: List[str] = Field(default_factory=list, alias="SPONSORS")
    tags: List[str] = Field(default_factory=list, alias="TAGS")
    featured: bool = Field(default=False, alias="FEATURED")

    @field_validator("enabled", "featured", mode="before")
    @classmethod
    def convert_sheet_boolean_strings(cls, v) -> bool:
        if isinstance(v, str):
            return v.upper() == "TRUE"
        return bool(v)

    @field_validator("sponsors", "tags", mode="before")
    @classmethod
    def split_comma_separated_values(cls, v) -> List[str]:
        if isinstance(v, str) and v.strip():
            return [item.strip() for item in v.split(",") if item.strip()]
        return []

    @field_validator("date", mode="before")
    @classmethod
    def convert_string_to_date(cls, v) -> dt.date:
        if isinstance(v, str):
            return dt.datetime.strptime(v, "%Y-%m-%d").date()
        return v

    def to_meetup(self, talks: List[Talk] = None) -> Meetup:
        return Meetup(
            number=self.meetup_id,
            title=self.title,
            date=self.date,
            time=self.time,
            location=self.location,
            talks=talks or [],
            sponsors=self.sponsors,
            meetup_url=self.meetup_url,
            feedback_url=self.feedback_url,
            livestream_id=self.livestream_id,
            tags=self.tags,
            featured=self.featured,
            status=MeetupStatus.PUBLISHED if self.enabled else MeetupStatus.DRAFT,
        )


class TalkSheetRow(BaseModel):
    meetup: str = Field(alias="Meetup")
    first_name: str = Field(alias="Imię")
    last_name: str = Field(alias="Nazwisko")
    bio: str = Field(default="", alias="BIO")
    photo_url: Optional[str] = Field(default=None, alias="Zdjęcie")
    talk_title: str = Field(alias="Tytuł prezentacji")
    talk_description: Optional[str] = Field(default=None, alias="Opis prezentacji")
    talk_title_en: Optional[str] = Field(default=None, alias="Tytuł prezentacji EN")
    language: str = Field(default="pl", alias="Język prezentacji")
    linkedin_url: Optional[str] = Field(default=None, alias="Link do LinkedIn")
    github_url: Optional[str] = Field(default=None, alias="Link do GitHub")
    twitter_url: Optional[str] = Field(default=None, alias="Link do Twitter")
    website_url: Optional[str] = Field(default=None, alias="Link do strony")

    @field_validator("bio", "talk_description", mode="before")
    @classmethod
    def strip_text_fields(cls, v) -> str:
        if v is None:
            return ""
        return str(v).strip()

    @field_validator("language", mode="before")
    @classmethod
    def convert_to_language_code(cls, v) -> str:
        if v is None or str(v).strip() == "":
            return "pl"
        lang = str(v).strip().lower()
        if lang in ["en", "english", "ang"]:
            return "en"
        return "pl"

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
            social_links=self._build_social_links(),
        )

    def _build_social_links(self) -> List[SocialLink]:
        social_links = []

        if self.linkedin_url:
            social_links.append(SocialLink(platform="linkedin", url=self.linkedin_url))
        if self.github_url:
            social_links.append(SocialLink(platform="github", url=self.github_url))
        if self.twitter_url:
            social_links.append(SocialLink(platform="twitter", url=self.twitter_url))
        if self.website_url:
            social_links.append(SocialLink(platform="website", url=self.website_url))

        return social_links

    def to_talk(self) -> Talk:
        return Talk(
            speaker_id=self.speaker_id,
            title=self.talk_title,
            description=self.talk_description,
            title_en=self.talk_title_en,
            language=Language.ENGLISH if self.language == "en" else Language.POLISH,
        )
