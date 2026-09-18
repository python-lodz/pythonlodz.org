"""Podgląd danych spotkania z arkusza + lista braków, bez generowania czegokolwiek.

Wejście to surowe wiersze zakładek `meetups` i `talks`, więc raport powstaje bez
pobierania zdjęć z Drive i bez renderowania grafik. `pyldz show` drukuje go
człowiekowi (albo agentowi przez `--json`), a `pyldz generate` używa go jako bramki.
"""

import datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel
from ruamel.yaml import YAML

from pyldz.models import Language, MeetupRow, MeetupType, TalkRow


class Severity(StrEnum):
    ERROR = "error"  # generacja nie ma sensu
    WARN = "warn"  # strona powstanie, ale czegoś na niej zabraknie
    INFO = "info"  # do wiedzy / do uzupełnienia później


class Finding(BaseModel):
    severity: Severity
    field: str
    message: str


class TalkSummary(BaseModel):
    order: int | None
    speaker: str
    speaker_id: str
    title: str
    language: Language
    description_length: int
    has_photo: bool
    has_title_en: bool


class MeetupPreflight(BaseModel):
    meetup_id: str
    type: MeetupType
    date: datetime.date
    time: str
    location: str
    language: Language
    enabled: bool
    sponsors: list[str]
    meetup_url: str | None
    feedback_url: str | None
    livestream_id: str | None
    talks: list[TalkSummary]
    findings: list[Finding]

    @property
    def has_errors(self) -> bool:
        return any(f.severity is Severity.ERROR for f in self.findings)

    def to_text(self) -> str:
        lines = [
            f"Python Łódź #{self.meetup_id} · {self.date} {self.time} "
            f"· {self.location} · {self.language.value} · {self.type.value}",
            f"zapisy: {self.meetup_url or '—'}",
            f"ankieta: {self.feedback_url or '—'} · live: {self.livestream_id or '—'}",
            f"sponsorzy: {', '.join(self.sponsors) or '—'}",
            "",
            f"Prelekcje ({len(self.talks)}):",
        ]
        for index, talk in enumerate(self.talks, start=1):
            position = talk.order if talk.order is not None else index
            lines.append(
                f"  {position}. {talk.speaker} — {talk.title} "
                f"[{talk.language.value}, opis {talk.description_length} zn., "
                f"zdjęcie: {'tak' if talk.has_photo else 'BRAK'}]"
            )

        lines.append("")
        if not self.findings:
            lines.append("Braki: żadnych.")
            return "\n".join(lines)

        lines.append("Braki:")
        marks = {Severity.ERROR: "✖", Severity.WARN: "!", Severity.INFO: "·"}
        for finding in self.findings:
            lines.append(
                f"  {marks[finding.severity]} [{finding.field}] {finding.message}"
            )
        return "\n".join(lines)


def _speaker_instagram(speakers_dir: Path, speaker_id: str) -> str | None:
    profile = speakers_dir / f"{speaker_id}.yaml"
    if not profile.exists():
        return None
    data = YAML().load(profile.read_text(encoding="utf-8")) or {}
    return data.get("instagram")


def _talk_findings(talk_rows: list[TalkRow], speakers_dir: Path) -> list[Finding]:
    findings: list[Finding] = []

    if not talk_rows:
        findings.append(
            Finding(
                severity=Severity.WARN,
                field="talks",
                message="brak prelekcji w zakładce talks — strona wyjdzie z "
                "komunikatem „agendę ogłosimy wkrótce”",
            )
        )
        return findings

    for talk in talk_rows:
        who = talk.full_name
        if talk.photo_url is None:
            findings.append(
                Finding(
                    severity=Severity.WARN,
                    field="photo_url",
                    message=f"{who}: brak zdjęcia — grafiki wezmą no_photo.png",
                )
            )
        if not talk.bio:
            findings.append(
                Finding(
                    severity=Severity.WARN,
                    field="bio",
                    message=f"{who}: puste bio — profil prelegenta zostanie bez opisu",
                )
            )
        if not talk.talk_description:
            findings.append(
                Finding(
                    severity=Severity.WARN,
                    field="talk_description",
                    message=f"{who}: pusty opis prelekcji",
                )
            )
        if talk.talk_title_en is None:
            findings.append(
                Finding(
                    severity=Severity.INFO,
                    field="talk_title_en",
                    message=f"{who}: brak tytułu EN — grafiki EN wezmą tytuł PL",
                )
            )
        if _speaker_instagram(speakers_dir, talk.speaker_id) is None:
            findings.append(
                Finding(
                    severity=Severity.INFO,
                    field="instagram",
                    message=f"{who}: brak handle'a IG w page/data/speakers/"
                    f"{talk.speaker_id}.yaml — gk-sm nie oznaczy go na Instagramie",
                )
            )

    if len(talk_rows) > 1 and all(talk.order is None for talk in talk_rows):
        findings.append(
            Finding(
                severity=Severity.INFO,
                field="order",
                message="puste order przy kilku prelekcjach — kolejność weźmie się "
                "z kolejności wierszy w arkuszu",
            )
        )

    return findings


def build_preflight(
    meetup_row: MeetupRow,
    talk_rows: list[TalkRow],
    data_dir: Path,
) -> MeetupPreflight:
    """Zbuduj raport dla jednego spotkania. `data_dir` to `page/data`."""
    findings: list[Finding] = []

    if meetup_row.type is MeetupType.SUMMER_EDITION:
        findings.append(
            Finding(
                severity=Severity.ERROR,
                field="type",
                message="edycja letnia — index.md pisze się ręcznie "
                "(wzór #59/#65, tasks/lessons.md); generator jej nie tyka",
            )
        )

    if not meetup_row.enabled:
        findings.append(
            Finding(
                severity=Severity.ERROR,
                field="enabled",
                message="enabled=FALSE w arkuszu — ustaw TRUE, żeby generować stronę",
            )
        )

    if not (data_dir / "locations" / f"{meetup_row.location}.yaml").exists():
        findings.append(
            Finding(
                severity=Severity.ERROR,
                field="location",
                message=f"nieznana lokalizacja „{meetup_row.location}” — brakuje "
                f"page/data/locations/{meetup_row.location}.yaml",
            )
        )

    if meetup_row.meetup_url is None:
        findings.append(
            Finding(
                severity=Severity.WARN,
                field="meetup_url",
                message="brak linku do zapisów (meetup.com) — strona wyjdzie bez "
                "przycisku zapisów",
            )
        )

    unknown_sponsors = [
        sponsor
        for sponsor in meetup_row.sponsors
        if not (data_dir / "sponsors" / f"{sponsor}.yaml").exists()
    ]
    if unknown_sponsors:
        findings.append(
            Finding(
                severity=Severity.WARN,
                field="sponsors",
                message=f"sponsorzy bez danych w page/data/sponsors: "
                f"{', '.join(unknown_sponsors)}",
            )
        )

    if meetup_row.feedback_url is None:
        findings.append(
            Finding(
                severity=Severity.INFO,
                field="feedback_url",
                message="brak linku do ankiety — wpisuje się go zwykle po spotkaniu",
            )
        )

    if meetup_row.livestream_id is None:
        findings.append(
            Finding(
                severity=Severity.INFO,
                field="livestream_id",
                message="brak ID transmisji — live zakłada gk-sm-4-harmonogram",
            )
        )

    findings.extend(_talk_findings(talk_rows, data_dir / "speakers"))

    return MeetupPreflight(
        meetup_id=meetup_row.meetup_id,
        type=meetup_row.type,
        date=meetup_row.date,
        time=meetup_row.time,
        location=meetup_row.location,
        language=meetup_row.language,
        enabled=meetup_row.enabled,
        sponsors=meetup_row.sponsors,
        meetup_url=str(meetup_row.meetup_url) if meetup_row.meetup_url else None,
        feedback_url=str(meetup_row.feedback_url) if meetup_row.feedback_url else None,
        livestream_id=meetup_row.livestream_id,
        talks=[
            TalkSummary(
                order=talk.order,
                speaker=talk.full_name,
                speaker_id=talk.speaker_id,
                title=talk.talk_title,
                language=talk.language,
                description_length=len(talk.talk_description),
                has_photo=talk.photo_url is not None,
                has_title_en=talk.talk_title_en is not None,
            )
            for talk in talk_rows
        ],
        findings=findings,
    )
