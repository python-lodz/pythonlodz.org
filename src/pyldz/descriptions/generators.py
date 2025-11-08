"""Generators for meetup descriptions."""

import logging
from datetime import datetime, timedelta
from pathlib import Path

from ruamel.yaml import YAML

from pyldz.descriptions.models import (
    AgendaItem,
    MeetupDescriptions,
    YouTubeRecordingDescription,
)
from pyldz.models import Language, Meetup, Speaker

log = logging.getLogger(__name__)


AGENDA_TWO_TALKS = [
    AgendaItem(time="18:00", title="Rozpoczęcie i sprawy organizacyjne"),
    AgendaItem(time="18:15", title="Prezentacja 1"),
    AgendaItem(time="19:00", title="Przerwa"),
    AgendaItem(time="19:30", title="Prezentacja 2"),
    AgendaItem(time="20:15", title="Networking"),
]

AGENDA_ONE_TALK = [
    AgendaItem(time="18:00", title="Rozpoczęcie i sprawy organizacyjne"),
    AgendaItem(time="18:15", title="Prezentacja"),
    AgendaItem(time="19:00", title="Przerwa i networking"),
]


class SocialMediaLinks:
    """Social media links from Hugo config."""

    OFFICIAL_WEBSITE = "https://pythonlodz.org"
    MEETUP = "https://www.meetup.com/python-lodz"
    DISCORD = "https://discord.gg/jbvWBMufEf"
    FACEBOOK = "https://www.facebook.com/pythonlodz"
    LINKEDIN = "https://www.linkedin.com/company/python-lodz"
    INSTAGRAM = "https://www.instagram.com/pythonlodz"
    YOUTUBE = "https://www.youtube.com/@pythonlodz"


class SponsorRepository:
    """Load sponsor data from YAML files."""

    def __init__(self, sponsors_dir: Path):
        self.sponsors_dir = sponsors_dir
        self._cache: dict[str, dict] = {}
        self._load_all_sponsors()

    def _load_all_sponsors(self) -> None:
        """Load all sponsor YAML files into cache."""
        yaml = YAML()
        if not self.sponsors_dir.exists():
            log.warning(f"Sponsors directory not found: {self.sponsors_dir}")
            return

        for sponsor_file in self.sponsors_dir.glob("*.yaml"):
            sponsor_id = sponsor_file.stem
            try:
                with open(sponsor_file, encoding="utf-8") as f:
                    data = yaml.load(f)
                    if data:
                        self._cache[sponsor_id] = data
                        log.debug(f"Loaded sponsor: {sponsor_id}")
            except Exception as e:
                log.error(f"Failed to load sponsor {sponsor_id}: {e}")

    def get_sponsor(self, sponsor_id: str) -> dict | None:
        """Get sponsor data by ID."""
        return self._cache.get(sponsor_id)


class MeetupDescriptionGenerator:
    """Generate all types of descriptions for a meetup."""

    def __init__(
        self,
        meetup: Meetup,
        speakers: list[Speaker],
        sponsors_dir: Path,
    ):
        self.meetup = meetup
        self.speakers = speakers
        self.sponsor_repo = SponsorRepository(sponsors_dir)
        self.agenda = self._get_agenda()

    def _get_agenda(self) -> list[AgendaItem]:
        """Get appropriate agenda based on number of talks."""
        if self.meetup.has_two_talks:
            return AGENDA_TWO_TALKS
        else:
            return AGENDA_ONE_TALK

    def _format_date(self) -> str:
        """Format date as DD.MM.YYYY."""
        return self.meetup.date.strftime("%d.%m.%Y")

    def _format_date_long(self) -> str:
        """Format date in Polish long format."""
        months = {
            1: "stycznia",
            2: "lutego",
            3: "marca",
            4: "kwietnia",
            5: "maja",
            6: "czerwca",
            7: "lipca",
            8: "sierpnia",
            9: "września",
            10: "października",
            11: "listopada",
            12: "grudnia",
        }
        month_name = months[self.meetup.date.month]
        return f"{self.meetup.date.day} {month_name} {self.meetup.date.year}"

    def _get_speaker_by_id(self, speaker_id: str) -> Speaker | None:
        """Get speaker by ID."""
        for speaker in self.speakers:
            if speaker.id == speaker_id:
                return speaker
        return None

    def _build_agenda_section(self) -> str:
        """Build agenda section."""
        lines = ["Agenda:"]
        for item in self.agenda:
            lines.append(f"{item.time} - {item.title}")
        return "\n".join(lines)

    def _build_talks_section(self) -> str:
        """Build talks section with descriptions."""
        if self.meetup.is_to_be_announced:
            return "Prezentacje będą wkrótce ogłoszone!"

        lines = []
        for i, talk in enumerate(self.meetup.talks, 1):
            speaker = self._get_speaker_by_id(talk.speaker_id)
            speaker_name = speaker.name if speaker else "Unknown"

            lines.append(f"{i}. {talk.title} - {speaker_name}")
            lines.append("")
            lines.append(talk.description)
            lines.append("")

        return "\n".join(lines)

    def _build_sponsors_section(self) -> str:
        """Build sponsors section."""
        if not self.meetup.sponsors:
            return ""

        lines = ["Sponsorzy:"]
        for sponsor_id in self.meetup.sponsors:
            sponsor = self.sponsor_repo.get_sponsor(sponsor_id)
            if sponsor:
                lines.append(f"- {sponsor.get('name', sponsor_id)}")

        return "\n".join(lines)

    def generate_meetup_com(self) -> str:
        """Generate description for meetup.com."""
        location_name = self.meetup.location_name()

        parts = [
            "Cześć!",
            "",
            f"Zapraszamy Was na spotkanie, które odbędzie się {self._format_date_long()} roku o godzinie {self.meetup.time} w {location_name}.",
            "",
            "Podczas spotkania odbędą się niezwykle ciekawe prezentacje:",
            "",
            self._build_talks_section(),
            self._build_agenda_section(),
            "",
            "Dołącz do nas na Discordzie!",
            "",
            f"Dołącz do naszej społeczności, gdzie rozmawiamy o Pythonie i nie tylko. {SocialMediaLinks.DISCORD}",
            "",
            "Zaproś innych!",
            "",
            "Powiedz znajomym o tym wydarzeniu i zaproś ich do dołączenia do naszego meetupu oraz na serwer Discord. Razem stworzymy jeszcze większą i silniejszą społeczność!",
        ]

        return "\n".join(parts)

    def generate_youtube_live(self) -> str:
        """Generate description for YouTube live stream."""
        location_name = self.meetup.location_name()

        parts = [
            f"🔴 LIVE: Python Łódź Meetup #{self.meetup.meetup_id}",
            "",
            f"📅 {self._format_date_long()}",
            f"🕕 {self.meetup.time}",
            f"📍 {location_name}",
            "",
            "Prezentacje:",
            "",
            self._build_talks_section(),
            "Agenda:",
            "",
            self._build_agenda_section(),
            "",
            "Linki do społeczności:",
            f"➡️ Oficjalna strona: {SocialMediaLinks.OFFICIAL_WEBSITE}",
            f"➡️ Meetup: {SocialMediaLinks.MEETUP}",
            f"➡️ Discord: {SocialMediaLinks.DISCORD}",
            f"➡️ Facebook: {SocialMediaLinks.FACEBOOK}",
            f"➡️ LinkedIn: {SocialMediaLinks.LINKEDIN}",
            f"➡️ Instagram: {SocialMediaLinks.INSTAGRAM}",
            f"➡️ YouTube: {SocialMediaLinks.YOUTUBE}",
        ]

        return "\n".join(parts)

    def generate_youtube_recording(self) -> str:
        """Generate description for YouTube recording."""
        location_name = self.meetup.location_name()

        parts = [
            f"Python Łódź Meetup #{self.meetup.meetup_id}",
            "",
            f"📅 {self._format_date_long()}",
            f"🕕 {self.meetup.time}",
            f"📍 {location_name}",
            "",
            "Prezentacje:",
            "",
            self._build_talks_section(),
            "Linki do społeczności:",
            f"➡️ Oficjalna strona: {SocialMediaLinks.OFFICIAL_WEBSITE}",
            f"➡️ Meetup: {SocialMediaLinks.MEETUP}",
            f"➡️ Discord: {SocialMediaLinks.DISCORD}",
            f"➡️ Facebook: {SocialMediaLinks.FACEBOOK}",
            f"➡️ LinkedIn: {SocialMediaLinks.LINKEDIN}",
            f"➡️ Instagram: {SocialMediaLinks.INSTAGRAM}",
            f"➡️ YouTube: {SocialMediaLinks.YOUTUBE}",
        ]

        return "\n".join(parts)

    def generate_youtube_recording_talks(self) -> list[YouTubeRecordingDescription]:
        """Generate descriptions for each talk recording."""
        if self.meetup.is_to_be_announced:
            return []

        descriptions = []
        for i, talk in enumerate(self.meetup.talks, 1):
            speaker = self._get_speaker_by_id(talk.speaker_id)
            speaker_name = speaker.name if speaker else "Unknown"

            title = f"Python Łódź #{self.meetup.meetup_id} - {talk.title}"

            parts = [
                self._build_agenda_section(),
                "",
                "Linki do społeczności:",
                f"➡️ Oficjalna strona: {SocialMediaLinks.OFFICIAL_WEBSITE}",
                f"➡️ Meetup: {SocialMediaLinks.MEETUP}",
                f"➡️ Discord: {SocialMediaLinks.DISCORD}",
                f"➡️ Facebook: {SocialMediaLinks.FACEBOOK}",
                f"➡️ LinkedIn: {SocialMediaLinks.LINKEDIN}",
                f"➡️ Instagram: {SocialMediaLinks.INSTAGRAM}",
                f"➡️ YouTube: {SocialMediaLinks.YOUTUBE}",
                "",
                f"Prelegent: {speaker_name}",
                "",
                talk.description,
            ]

            description = "\n".join(parts)
            descriptions.append(
                YouTubeRecordingDescription(title=title, description=description)
            )

        return descriptions

    def generate_chatgpt_prompt(self) -> str:
        """Generate super prompt for ChatGPT to create social media posts."""
        location_name = self.meetup.location_name()
        sponsors_info = self._build_sponsors_info()

        parts = [
            "# Super Prompt do Generowania Postów na Social Media",
            "",
            "## Informacje o Spotkaniu",
            "",
            f"**Numer spotkania:** Meetup #{self.meetup.meetup_id}",
            f"**Data:** {self._format_date_long()}",
            f"**Godzina:** {self.meetup.time}",
            f"**Miejsce:** {location_name}",
            "",
            "## Prezentacje",
            "",
            self._build_talks_section(),
            "## Agenda",
            "",
            self._build_agenda_section(),
            "",
            "## Sponsorzy",
            "",
            sponsors_info,
            "",
            "## Linki do Społeczności",
            "",
            f"- Oficjalna strona: {SocialMediaLinks.OFFICIAL_WEBSITE}",
            f"- Meetup: {SocialMediaLinks.MEETUP}",
            f"- Discord: {SocialMediaLinks.DISCORD}",
            f"- Facebook: {SocialMediaLinks.FACEBOOK}",
            f"- LinkedIn: {SocialMediaLinks.LINKEDIN}",
            f"- Instagram: {SocialMediaLinks.INSTAGRAM}",
            f"- YouTube: {SocialMediaLinks.YOUTUBE}",
            "",
            "## Instrukcje do Generowania Postów",
            "",
            "Na podstawie powyższych informacji przygotuj serię postów na Facebook, Discord oraz Mail które:",
            "",
            "1. **Posty o Prelegentach** - jeden post dla każdego prelegenta:",
            "   - Przedstaw prelegenta i jego prezentację",
            "   - Podkreśl najważniejsze punkty prezentacji",
            "   - Zachęć do udziału w spotkaniu",
            "   - Dodaj link do strony spotkania",
            "",
            "2. **Posty o Sponsorach** - jeden post dla każdego sponsora:",
            "   - Podziękuj sponsorowi za wsparcie",
            "   - Opisz krótko czym się zajmuje sponsor",
            "   - Dodaj link do strony sponsora",
            "   - Zachęć do śledzenia ich na social mediach",
            "",
            "3. **Posty Informacyjne** - co 2 dni od jutra do 2 tygodni przed spotkaniem:",
            "   - Przypomnienia o zbliżającym się spotkaniu",
            "   - Ciekawostki o prezentacjach",
            "   - Informacje o transmisji live",
            "   - Zaproszenia do dołączenia do społeczności",
            "",
            "4. **Post o Transmisji Live** - kilka dni przed spotkaniem:",
            "   - Informacja że spotkanie będzie transmitowane na żywo",
            "   - Link do transmisji",
            "   - Zachęta do oglądania online",
            "",
            "## Wytyczne do Formatowania Postów",
            "",
            "- **Ton:** Profesjonalny ale przyjazny, luźny, otwarty",
            "- **Grupa docelowa:** Programiści Pythona i osoby chcące się go nauczyć",
            "- **Emoji:** Używaj z umiarkowaniem do podkreślania ważnych informacji i emocji",
            "- **Każdy post powinien zawierać:** Link do strony spotkania",
            "- **Format:** Każdy post powinien być gotowy do wklejenia bezpośrednio na social media",
            "",
            "## Przykład Formatowania Posta",
            "",
            "```",
            "🎉 Już za tydzień spotkanie Python Łódź!",
            "",
            "Czekamy na Was w piątek o 18:00 w IndieBI 🚀",
            "",
            "Tym razem będziemy mówić o:",
            "✨ Czystej architekturze w Django",
            "✨ Wizualizacjach w Pythonie",
            "",
            "Zapisy: [link do meetupu]",
            "Transmisja live: [link do strony]",
            "",
            "Dołącz do nas na Discordzie: [link do Discorda]",
            "```",
            "",
            "## Dodatkowe Informacje",
            "",
            "- Spotkania mają luźną formę, preferuje się rodzinny/przyjacielski/otwarty klimat",
            "- Posty mają być zaplanowane od jutra do 2 tygodni przed spotkaniem",
            "- Każdy post powinien być unikalny i nie powtarzać się",
            "- Posty mogą zawierać pytania do społeczności",
            "- Zachęcaj do zapraszania znajomych",
            "",
            "## Przygotuj Posty w Następującym Formacie",
            "",
            "Dla każdego posta podaj:",
            "1. **Data publikacji** (od jutra do 2 tygodni przed spotkaniem)",
            "2. **Platforma** (Facebook/Discord/Mail)",
            "3. **Treść posta** (gotowa do wklejenia)",
            "4. **Prompt do obrazka** (jeśli ma być dołączony obraz):",
            "   - Górna treść (tekst na górze obrazka)",
            "   - Dolna treść (tekst na dole obrazka)",
            "",
            "Zacznij od przygotowania postów! 🚀",
        ]

        return "\n".join(parts)

    def _build_sponsors_info(self) -> str:
        """Build detailed sponsors information."""
        if not self.meetup.sponsors:
            return "Brak informacji o sponsorach."

        lines = []
        for sponsor_id in self.meetup.sponsors:
            sponsor = self.sponsor_repo.get_sponsor(sponsor_id)
            if sponsor:
                lines.append(f"**{sponsor.get('name', sponsor_id)}**")
                lines.append(f"Website: {sponsor.get('website', 'N/A')}")
                if sponsor.get("description"):
                    lines.append(f"Opis: {sponsor.get('description')}")
                lines.append("")

        return "\n".join(lines)

    def generate_all(self) -> MeetupDescriptions:
        """Generate all descriptions."""
        return MeetupDescriptions(
            meetup_id=self.meetup.meetup_id,
            meetup_com=self.generate_meetup_com(),
            youtube_live=self.generate_youtube_live(),
            youtube_recording=self.generate_youtube_recording(),
            youtube_recording_talks=self.generate_youtube_recording_talks(),
            chatgpt_prompt=self.generate_chatgpt_prompt(),
        )
