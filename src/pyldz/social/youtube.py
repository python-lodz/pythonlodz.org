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

# Kanał Python Łódź (studio.youtube.com/channel/UCX_qQucsHqodP4Hwlfn2Pcw).
# ID, nie handle: konta brandowe nierzadko nie mają jeszcze `customUrl`.
PYTHON_LODZ_CHANNEL_ID = "UCX_qQucsHqodP4Hwlfn2Pcw"


class WrongYouTubeChannelError(Exception):
    """Token z cache należy do innego kanału niż ten, na którym robimy transmisje."""


class YouTubeLive:
    def __init__(
        self,
        credentials_path: Path = Path(".client_secret.json"),
        token_cache_path: Path = Path(".yt_token.json"),
        channel_id: str = PYTHON_LODZ_CHANNEL_ID,
    ):
        self.credentials_path = credentials_path
        self.token_cache_path = token_cache_path
        self.channel_id = channel_id

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

    def _verify_channel(self, youtube) -> str:
        """Upewnij się, czyj jest token, ZANIM powstanie transmisja.

        `.yt_token.json` należy do konta, które autoryzowało się pierwsze — bez tej
        kontroli transmisja ląduje na prywatnym kanale osoby uruchamiającej komendę.
        """
        items = (
            youtube.channels()
            .list(part="snippet", mine=True)
            .execute()
            .get("items", [])
        )
        if not items:
            raise WrongYouTubeChannelError(
                f"Token {self.token_cache_path} nie widzi żadnego kanału YouTube. "
                f"Usuń ten plik i autoryzuj się ponownie, wybierając kanał "
                f"Python Łódź ({self.channel_id})."
            )

        channel = items[0]
        if channel.get("id") != self.channel_id:
            raise WrongYouTubeChannelError(
                f"Token {self.token_cache_path} należy do kanału "
                f"„{channel.get('snippet', {}).get('title', '?')}” "
                f"(id {channel.get('id')}), a transmisje zakładamy na kanale "
                f"Python Łódź (id {self.channel_id}). Usuń {self.token_cache_path} "
                f"i autoryzuj się ponownie, wybierając w przeglądarce konto marki "
                f"Python Łódź — nie konto osobiste."
            )

        return channel.get("snippet", {}).get("title", "")

    def create_live(
        self, title: str, start: datetime.datetime, description: str = ""
    ) -> str:
        credentials = self._get_credentials()
        youtube = build("youtube", "v3", credentials=credentials, cache_discovery=False)
        channel_title = self._verify_channel(youtube)
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
        log.info(f"Scheduled YouTube live on „{channel_title}”: {url}")
        return url
