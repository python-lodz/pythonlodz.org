import logging
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from pyldz.config import GoogleSheetsConfig
from pyldz.models import Meetup, MeetupSheetRow, Speaker, Talk, TalkSheetRow

log = logging.getLogger(__name__)


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

    def _fetch_sheet_data(self, sheet_name: str) -> list[list[str]]:
        try:
            credentials = self._get_credentials()
            sheets = build(
                "sheets", "v4", credentials=credentials, cache_discovery=False
            )

            range_name = f"{sheet_name}!A1:ZZ"

            result = (
                sheets.spreadsheets()
                .values()
                .get(
                    spreadsheetId=self.config.sheet_id,
                    range=range_name,
                    majorDimension="ROWS",
                )
                .execute()
            )

            return result.get("values", [])

        except Exception as e:
            log.error("Error fetching data from sheet '%s': %s", sheet_name, e)
            return []

    def fetch_meetups_data(self) -> list[dict[str, Any]]:
        rows = self._fetch_sheet_data(self.config.meetups_sheet_name)

        if not rows:
            return []

        header = rows[0]
        meetups_data = []

        for row in rows[1:]:
            padded_row = row + [""] * (len(header) - len(row))
            meetup_dict = dict(zip(header, padded_row))
            meetups_data.append(meetup_dict)

        return meetups_data

    def fetch_talks_data(self) -> list[dict[str, Any]]:
        rows = self._fetch_sheet_data(self.config.talks_sheet_name)

        if not rows:
            return []

        header = rows[0]
        talks_data = []

        for row in rows[1:]:
            padded_row = row + [""] * (len(header) - len(row))
            talk_dict = dict(zip(header, padded_row))

            if talk_dict.get("Meetup"):
                talks_data.append(talk_dict)

        return talks_data

    def get_enabled_meetups(
        self, meetups_data: list[dict[str, Any]]
    ) -> list[MeetupSheetRow]:
        enabled_meetups = []

        for meetup_data in meetups_data:
            try:
                meetup_row = MeetupSheetRow.model_validate(meetup_data)
                if meetup_row.enabled:
                    enabled_meetups.append(meetup_row)
            except Exception as e:
                log.error("Error parsing meetup data: %s", e)
                continue

        return enabled_meetups

    def get_talks_for_meetup(
        self, meetup_id: str, talks_data: list[dict[str, Any]]
    ) -> list[Talk]:
        talks = []

        for talk_data in talks_data:
            if talk_data.get("Meetup") == meetup_id:
                try:
                    talk_row = TalkSheetRow.model_validate(talk_data)
                    talk = talk_row.to_talk()
                    talks.append(talk)
                except Exception as e:
                    log.error("Error parsing talk data for meetup %s: %s", meetup_id, e)
                    continue

        return talks

    def get_speakers_for_meetup(
        self, meetup_id: str, talks_data: list[dict[str, Any]]
    ) -> list[Speaker]:
        speakers = []
        seen_speaker_ids = set()

        for talk_data in talks_data:
            if talk_data.get("Meetup") == meetup_id:
                try:
                    talk_row = TalkSheetRow.model_validate(talk_data)

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
        meetups_data = self.fetch_meetups_data()
        talks_data = self.fetch_talks_data()

        enabled_meetups = self.get_enabled_meetups(meetups_data)

        meetup_row = None
        for meetup in enabled_meetups:
            if meetup.meetup_id == meetup_id:
                meetup_row = meetup
                break

        if not meetup_row:
            return None

        talks = self.get_talks_for_meetup(meetup_id, talks_data)

        return meetup_row.to_meetup(talks)

    def get_all_enabled_meetups(self) -> list[Meetup]:
        meetups_data = self.fetch_meetups_data()
        talks_data = self.fetch_talks_data()

        enabled_meetups = self.get_enabled_meetups(meetups_data)

        meetups = []
        for meetup_row in enabled_meetups:
            talks = self.get_talks_for_meetup(meetup_row.meetup_id, talks_data)
            meetup = meetup_row.to_meetup(talks)
            meetups.append(meetup)

        return meetups

    def get_all_speakers(self) -> list[Speaker]:
        talks_data = self.fetch_talks_data()
        meetups_data = self.fetch_meetups_data()

        enabled_meetups = self.get_enabled_meetups(meetups_data)
        enabled_meetup_ids = {meetup.meetup_id for meetup in enabled_meetups}

        speakers = []
        seen_speaker_ids = set()

        for talk_data in talks_data:
            meetup_id = talk_data.get("Meetup")
            if meetup_id in enabled_meetup_ids:
                try:
                    talk_row = TalkSheetRow.model_validate(talk_data)

                    if talk_row.speaker_id not in seen_speaker_ids:
                        speaker = talk_row.to_speaker()
                        speakers.append(speaker)
                        seen_speaker_ids.add(talk_row.speaker_id)

                except Exception as e:
                    log.error("Error parsing speaker data: %s", e)
                    continue

        return speakers
