"""Create scheduled YouTube live broadcasts (used in the planning session)."""

import datetime
import logging
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

log = logging.getLogger(__name__)

SCOPES = ("https://www.googleapis.com/auth/youtube.force-ssl",)


class YouTubeLive:
    def __init__(
        self,
        credentials_path: Path = Path(".client_secret.json"),
        token_cache_path: Path = Path(".yt_token.json"),
    ):
        self.credentials_path = credentials_path
        self.token_cache_path = token_cache_path

    def _get_credentials(self) -> Credentials:
        credentials = None
        if self.token_cache_path.exists():
            credentials = Credentials.from_authorized_user_file(
                str(self.token_cache_path), SCOPES
            )
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())

        if credentials is None or not credentials.valid:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(self.credentials_path), SCOPES
            )
            credentials = flow.run_local_server(port=0)

        self.token_cache_path.write_text(credentials.to_json())
        return credentials

    def create_live(
        self, title: str, start: datetime.datetime, description: str = ""
    ) -> str:
        credentials = self._get_credentials()
        youtube = build("youtube", "v3", credentials=credentials, cache_discovery=False)
        broadcast = (
            youtube.liveBroadcasts()
            .insert(
                part="snippet,status,contentDetails",
                body={
                    "snippet": {
                        "title": title,
                        "description": description,
                        "scheduledStartTime": start.astimezone(
                            datetime.UTC
                        ).isoformat(),
                    },
                    "status": {
                        "privacyStatus": "public",
                        "selfDeclaredMadeForKids": False,
                    },
                    "contentDetails": {
                        "enableAutoStart": False,
                        "enableAutoStop": True,
                    },
                },
            )
            .execute()
        )
        url = f"https://www.youtube.com/watch?v={broadcast['id']}"
        log.info(f"Scheduled YouTube live: {url}")
        return url
