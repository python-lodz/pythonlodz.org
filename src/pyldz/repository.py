"""Google Sheets repository for fetching meetup data."""

from typing import List, Dict, Any, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from .config import GoogleSheetsConfig
from .models import Meetup, Speaker, Talk, MeetupSheetRow, TalkSheetRow


class GoogleSheetsRepository:
    """Repository for fetching data from Google Sheets."""

    def __init__(self, config: GoogleSheetsConfig):
        """Initialize repository with configuration."""
        self.config = config
        self.scopes = (
            "https://www.googleapis.com/auth/spreadsheets.readonly",
            "https://www.googleapis.com/auth/drive.readonly",
        )

    def _get_credentials(self) -> Credentials:
        """Get Google API credentials."""
        if not self.config.credentials_path.exists():
            raise FileNotFoundError(
                f"Credentials file not found: {self.config.credentials_path}"
            )

        credentials = None

        # Load existing token
        if self.config.token_cache_path.exists():
            credentials = Credentials.from_authorized_user_file(
                str(self.config.token_cache_path), self.scopes
            )
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())

        # Get new credentials if needed
        if credentials is None or not credentials.valid:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(self.config.credentials_path), self.scopes
            )
            credentials = flow.run_local_server(port=0)

        # Save token
        self.config.token_cache_path.write_text(credentials.to_json())
        return credentials

    def _fetch_sheet_data(self, sheet_name: str) -> List[List[str]]:
        """Fetch data from a specific sheet."""
        try:
            credentials = self._get_credentials()
            sheets = build("sheets", "v4", credentials=credentials, cache_discovery=False)

            range_name = f"{sheet_name}!A1:ZZ"

            result = (
                sheets.spreadsheets()
                .values()
                .get(
                    spreadsheetId=self.config.sheet_id,
                    range=range_name,
                    majorDimension="ROWS"
                )
                .execute()
            )

            return result.get("values", [])

        except Exception as e:
            print(f"Error fetching data from sheet '{sheet_name}': {e}")
            return []

    def fetch_meetups_data(self) -> List[Dict[str, Any]]:
        """Fetch meetups data from the meetups sheet."""
        rows = self._fetch_sheet_data(self.config.meetups_sheet_name)
        
        if not rows:
            return []

        # Convert to list of dictionaries
        header = rows[0]
        meetups_data = []

        for row in rows[1:]:
            # Pad row to match header length
            padded_row = row + [''] * (len(header) - len(row))
            meetup_dict = dict(zip(header, padded_row))
            meetups_data.append(meetup_dict)

        return meetups_data

    def fetch_talks_data(self) -> List[Dict[str, Any]]:
        """Fetch talks data from the main sheet."""
        rows = self._fetch_sheet_data(self.config.talks_sheet_name)
        
        if not rows:
            return []

        # Convert to list of dictionaries
        header = rows[0]
        talks_data = []

        for row in rows[1:]:
            # Pad row to match header length
            padded_row = row + [''] * (len(header) - len(row))
            talk_dict = dict(zip(header, padded_row))
            
            # Only include rows with meetup number
            if talk_dict.get("Meetup"):
                talks_data.append(talk_dict)

        return talks_data

    def get_enabled_meetups(self, meetups_data: List[Dict[str, Any]]) -> List[MeetupSheetRow]:
        """Filter and parse enabled meetups."""
        enabled_meetups = []
        
        for meetup_data in meetups_data:
            try:
                meetup_row = MeetupSheetRow.model_validate(meetup_data)
                if meetup_row.enabled:
                    enabled_meetups.append(meetup_row)
            except Exception as e:
                print(f"Error parsing meetup data: {e}")
                continue

        return enabled_meetups

    def get_talks_for_meetup(self, meetup_id: str, talks_data: List[Dict[str, Any]]) -> List[Talk]:
        """Get talks for a specific meetup."""
        talks = []
        
        for talk_data in talks_data:
            if talk_data.get("Meetup") == meetup_id:
                try:
                    talk_row = TalkSheetRow.model_validate(talk_data)
                    talk = talk_row.to_talk()
                    talks.append(talk)
                except Exception as e:
                    print(f"Error parsing talk data for meetup {meetup_id}: {e}")
                    continue

        return talks

    def get_speakers_for_meetup(self, meetup_id: str, talks_data: List[Dict[str, Any]]) -> List[Speaker]:
        """Get speakers for a specific meetup."""
        speakers = []
        seen_speaker_ids = set()
        
        for talk_data in talks_data:
            if talk_data.get("Meetup") == meetup_id:
                try:
                    talk_row = TalkSheetRow.model_validate(talk_data)
                    
                    # Avoid duplicate speakers
                    if talk_row.speaker_id not in seen_speaker_ids:
                        speaker = talk_row.to_speaker()
                        speakers.append(speaker)
                        seen_speaker_ids.add(talk_row.speaker_id)
                        
                except Exception as e:
                    print(f"Error parsing speaker data for meetup {meetup_id}: {e}")
                    continue

        return speakers

    def get_meetup_by_id(self, meetup_id: str) -> Optional[Meetup]:
        """Get a specific meetup by ID (only if enabled)."""
        meetups_data = self.fetch_meetups_data()
        talks_data = self.fetch_talks_data()
        
        enabled_meetups = self.get_enabled_meetups(meetups_data)
        
        # Find the specific meetup
        meetup_row = None
        for meetup in enabled_meetups:
            if meetup.meetup_id == meetup_id:
                meetup_row = meetup
                break
        
        if not meetup_row:
            return None
        
        # Get talks for this meetup
        talks = self.get_talks_for_meetup(meetup_id, talks_data)
        
        # Convert to Meetup entity
        return meetup_row.to_meetup(talks)

    def get_all_enabled_meetups(self) -> List[Meetup]:
        """Get all enabled meetups with their talks."""
        meetups_data = self.fetch_meetups_data()
        talks_data = self.fetch_talks_data()
        
        enabled_meetups = self.get_enabled_meetups(meetups_data)
        
        meetups = []
        for meetup_row in enabled_meetups:
            talks = self.get_talks_for_meetup(meetup_row.meetup_id, talks_data)
            meetup = meetup_row.to_meetup(talks)
            meetups.append(meetup)
        
        return meetups

    def get_all_speakers(self) -> List[Speaker]:
        """Get all unique speakers from enabled meetups."""
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
                    
                    # Avoid duplicate speakers
                    if talk_row.speaker_id not in seen_speaker_ids:
                        speaker = talk_row.to_speaker()
                        speakers.append(speaker)
                        seen_speaker_ids.add(talk_row.speaker_id)
                        
                except Exception as e:
                    print(f"Error parsing speaker data: {e}")
                    continue
        
        return speakers
