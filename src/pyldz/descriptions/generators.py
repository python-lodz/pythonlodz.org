"""Generators for meetup descriptions."""

import logging
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

AGENDA_TWO_TALKS_EN = [
    AgendaItem(time="18:00", title="Opening and organizational matters"),
    AgendaItem(time="18:15", title="Presentation 1"),
    AgendaItem(time="19:00", title="Break"),
    AgendaItem(time="19:30", title="Presentation 2"),
    AgendaItem(time="20:15", title="Networking"),
]

AGENDA_ONE_TALK_EN = [
    AgendaItem(time="18:00", title="Opening and organizational matters"),
    AgendaItem(time="18:15", title="Presentation"),
    AgendaItem(time="19:00", title="Break and networking"),
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

    def _get_agenda(self, language: Language | None = None) -> list[AgendaItem]:
        """Get appropriate agenda based on number of talks and language."""
        lang = language or self.meetup.language
        if self.meetup.has_two_talks:
            return AGENDA_TWO_TALKS_EN if lang == Language.EN else AGENDA_TWO_TALKS
        else:
            return AGENDA_ONE_TALK_EN if lang == Language.EN else AGENDA_ONE_TALK

    def _get_text(self, pl: str, en: str, language: Language | None = None) -> str:
        """Get text in the specified language."""
        lang = language or self.meetup.language
        return en if lang == Language.EN else pl

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

    def _build_agenda_section(self, language: Language | None = None) -> str:
        """Build agenda section."""
        lang = language or self.meetup.language
        agenda_label = "Agenda:" if lang == Language.PL else "Agenda:"
        agenda = self._get_agenda(lang)
        lines = [agenda_label]
        for item in agenda:
            lines.append(f"{item.time} - {item.title}")
        return "\n".join(lines)

    def _build_talks_section(self, language: Language | None = None) -> str:
        """Build talks section with descriptions."""
        lang = language or self.meetup.language
        if self.meetup.is_to_be_announced:
            return self._get_text(
                "Prezentacje będą wkrótce ogłoszone!",
                "Presentations will be announced soon!",
                lang,
            )

        lines = []
        for i, talk in enumerate(self.meetup.talks, 1):
            speaker = self._get_speaker_by_id(talk.speaker_id)
            speaker_name = speaker.name if speaker else "Unknown"

            lines.append(f"{i}. {talk.title} - {speaker_name}")
            lines.append("")
            lines.append(talk.description)
            lines.append("")

        return "\n".join(lines)

    def _build_sponsors_section(self, language: Language | None = None) -> str:
        """Build sponsors section."""
        if not self.meetup.sponsors:
            return ""

        lang = language or self.meetup.language
        sponsors_label = self._get_text("Sponsorzy:", "Sponsors:", lang)
        lines = [sponsors_label]
        for sponsor_id in self.meetup.sponsors:
            sponsor = self.sponsor_repo.get_sponsor(sponsor_id)
            if sponsor:
                lines.append(f"- {sponsor.get('name', sponsor_id)}")

        return "\n".join(lines)

    def generate_meetup_com(self) -> str:
        """Generate description for meetup.com."""
        lang = self.meetup.language
        location_name = self.meetup.location_name(lang)

        if lang == Language.EN:
            parts = [
                "Hello!",
                "",
                f"We invite you to a meetup that will take place on {self._format_date_long()} at {self.meetup.time} in {location_name}.",
                "",
                "During the meetup, there will be interesting presentations:",
                "",
                self._build_talks_section(lang),
                self._build_agenda_section(lang),
                "",
                "Join us on Discord!",
                "",
                f"Join our community where we talk about Python and more. {SocialMediaLinks.DISCORD}",
                "",
                "Invite others!",
                "",
                "Tell your friends about this event and invite them to join our meetup and Discord server. Together we will create an even bigger and stronger community!",
                "",
                "Follow us on social media:",
                f"➡️ Official website: {SocialMediaLinks.OFFICIAL_WEBSITE}",
                f"➡️ Meetup: {SocialMediaLinks.MEETUP}",
                f"➡️ Discord: {SocialMediaLinks.DISCORD}",
                f"➡️ Facebook: {SocialMediaLinks.FACEBOOK}",
                f"➡️ LinkedIn: {SocialMediaLinks.LINKEDIN}",
                f"➡️ Instagram: {SocialMediaLinks.INSTAGRAM}",
                f"➡️ YouTube: {SocialMediaLinks.YOUTUBE}",
            ]
        else:
            parts = [
                "Cześć!",
                "",
                f"Zapraszamy Was na spotkanie, które odbędzie się {self._format_date_long()} roku o godzinie {self.meetup.time} w {location_name}.",
                "",
                "Podczas spotkania odbędą się niezwykle ciekawe prezentacje:",
                "",
                self._build_talks_section(lang),
                self._build_agenda_section(lang),
                "",
                "Dołącz do nas na Discordzie!",
                "",
                f"Dołącz do naszej społeczności, gdzie rozmawiamy o Pythonie i nie tylko. {SocialMediaLinks.DISCORD}",
                "",
                "Zaproś innych!",
                "",
                "Powiedz znajomym o tym wydarzeniu i zaproś ich do dołączenia do naszego meetupu oraz na serwer Discord. Razem stworzymy jeszcze większą i silniejszą społeczność!",
                "",
                "Śledź nas w mediach społecznych:",
                f"➡️ Oficjalna strona: {SocialMediaLinks.OFFICIAL_WEBSITE}",
                f"➡️ Meetup: {SocialMediaLinks.MEETUP}",
                f"➡️ Discord: {SocialMediaLinks.DISCORD}",
                f"➡️ Facebook: {SocialMediaLinks.FACEBOOK}",
                f"➡️ LinkedIn: {SocialMediaLinks.LINKEDIN}",
                f"➡️ Instagram: {SocialMediaLinks.INSTAGRAM}",
                f"➡️ YouTube: {SocialMediaLinks.YOUTUBE}",
            ]

        return "\n".join(parts)

    def generate_youtube_live(self) -> str:
        """Generate description for YouTube live stream."""
        lang = self.meetup.language
        location_name = self.meetup.location_name(lang)

        if lang == Language.EN:
            parts = [
                f"🔴 LIVE: Python Łódź Meetup #{self.meetup.meetup_id}",
                "",
                f"📅 {self._format_date_long()}",
                f"🕕 {self.meetup.time}",
                f"📍 {location_name}",
                "",
                "Agenda:",
                "",
                self._build_agenda_section(lang),
                "",
                "Links to our community:",
                f"➡️ Official website: {SocialMediaLinks.OFFICIAL_WEBSITE}",
                f"➡️ Meetup: {SocialMediaLinks.MEETUP}",
                f"➡️ Discord: {SocialMediaLinks.DISCORD}",
                f"➡️ Facebook: {SocialMediaLinks.FACEBOOK}",
                f"➡️ LinkedIn: {SocialMediaLinks.LINKEDIN}",
                f"➡️ Instagram: {SocialMediaLinks.INSTAGRAM}",
                f"➡️ YouTube: {SocialMediaLinks.YOUTUBE}",
                "",
                "Presentations:",
                "",
                self._build_talks_section(lang),
            ]
        else:
            parts = [
                f"🔴 LIVE: Python Łódź Meetup #{self.meetup.meetup_id}",
                "",
                f"📅 {self._format_date_long()}",
                f"🕕 {self.meetup.time}",
                f"📍 {location_name}",
                "",
                "Agenda:",
                "",
                self._build_agenda_section(lang),
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
                "Prezentacje:",
                "",
                self._build_talks_section(lang),
            ]

        return "\n".join(parts)

    def generate_youtube_recording(self) -> str:
        """Generate description for YouTube recording."""
        lang = self.meetup.language
        location_name = self.meetup.location_name(lang)

        if lang == Language.EN:
            parts = [
                f"Python Łódź Meetup #{self.meetup.meetup_id}",
                "",
                f"📅 {self._format_date_long()}",
                f"🕕 {self.meetup.time}",
                f"📍 {location_name}",
                "",
                "Agenda:",
                "",
                self._build_agenda_section(lang),
                "",
                "Links to our community:",
                f"➡️ Official website: {SocialMediaLinks.OFFICIAL_WEBSITE}",
                f"➡️ Meetup: {SocialMediaLinks.MEETUP}",
                f"➡️ Discord: {SocialMediaLinks.DISCORD}",
                f"➡️ Facebook: {SocialMediaLinks.FACEBOOK}",
                f"➡️ LinkedIn: {SocialMediaLinks.LINKEDIN}",
                f"➡️ Instagram: {SocialMediaLinks.INSTAGRAM}",
                f"➡️ YouTube: {SocialMediaLinks.YOUTUBE}",
                "",
                "Presentations:",
                "",
                self._build_talks_section(lang),
            ]
        else:
            parts = [
                f"Python Łódź Meetup #{self.meetup.meetup_id}",
                "",
                f"📅 {self._format_date_long()}",
                f"🕕 {self.meetup.time}",
                f"📍 {location_name}",
                "",
                "Agenda:",
                "",
                self._build_agenda_section(lang),
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
                "Prezentacje:",
                "",
                self._build_talks_section(lang),
            ]

        return "\n".join(parts)

    def generate_youtube_recording_talks(self) -> list[YouTubeRecordingDescription]:
        """Generate descriptions for each talk recording."""
        if self.meetup.is_to_be_announced:
            return []

        lang = self.meetup.language
        descriptions = []
        for talk in self.meetup.talks:
            speaker = self._get_speaker_by_id(talk.speaker_id)
            speaker_name = speaker.name if speaker else "Unknown"

            title = f"Python Łódź #{self.meetup.meetup_id} - {talk.title}"

            if lang == Language.EN:
                parts = [
                    self._build_agenda_section(lang),
                    "",
                    "Links to our community:",
                    f"➡️ Official website: {SocialMediaLinks.OFFICIAL_WEBSITE}",
                    f"➡️ Meetup: {SocialMediaLinks.MEETUP}",
                    f"➡️ Discord: {SocialMediaLinks.DISCORD}",
                    f"➡️ Facebook: {SocialMediaLinks.FACEBOOK}",
                    f"➡️ LinkedIn: {SocialMediaLinks.LINKEDIN}",
                    f"➡️ Instagram: {SocialMediaLinks.INSTAGRAM}",
                    f"➡️ YouTube: {SocialMediaLinks.YOUTUBE}",
                    "",
                    f"Speaker: {speaker_name}",
                    "",
                    talk.description,
                ]
            else:
                parts = [
                    self._build_agenda_section(lang),
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
        lang = self.meetup.language
        location_name = self.meetup.location_name(lang)
        sponsors_info = self._build_sponsors_info(lang)

        if lang == Language.EN:
            parts = [
                "# Super Prompt for Generating Social Media Posts",
                "",
                "## Meeting Information",
                "",
                f"**Meeting number:** Meetup #{self.meetup.meetup_id}",
                f"**Date:** {self._format_date_long()}",
                f"**Time:** {self.meetup.time}",
                f"**Location:** {location_name}",
                "",
                "## Presentations",
                "",
                self._build_talks_section(lang),
                "## Agenda",
                "",
                self._build_agenda_section(lang),
                "",
                "## Sponsors",
                "",
                sponsors_info,
                "",
                "## Links to Our Community",
                "",
                f"- Official website: {SocialMediaLinks.OFFICIAL_WEBSITE}",
                f"- Meetup: {SocialMediaLinks.MEETUP}",
                f"- Discord: {SocialMediaLinks.DISCORD}",
                f"- Facebook: {SocialMediaLinks.FACEBOOK}",
                f"- LinkedIn: {SocialMediaLinks.LINKEDIN}",
                f"- Instagram: {SocialMediaLinks.INSTAGRAM}",
                f"- YouTube: {SocialMediaLinks.YOUTUBE}",
                "",
                "## Instructions for Generating Posts",
                "",
                "Based on the above information, prepare a series of posts for Facebook, Discord and Email that:",
                "",
                "1. **Speaker Posts** - one post for each speaker:",
                "   - Introduce the speaker and their presentation",
                "   - Highlight the key points of the presentation",
                "   - Encourage participation in the meeting",
                "   - Add link to the meeting page",
                "",
                "2. **Sponsor Posts** - one post for each sponsor:",
                "   - Thank the sponsor for their support",
                "   - Briefly describe what the sponsor does",
                "   - Add link to the sponsor's website",
                "   - Encourage following them on social media",
                "",
                f"3. **Informative Posts** - 2 weeks before the meeting which will be {self._format_date_long()}:",
                "   - Reminders about the upcoming meeting",
                "   - Interesting facts about presentations",
                "   - Information about live streaming",
                "   - Invitations to join the community",
                "",
                "4. **Live Stream Post** - a few days before the meeting:",
                "   - Information that the meeting will be streamed live",
                "   - Link to the stream",
                "   - Encouragement to watch online",
                "",
                "## Post Formatting Guidelines",
                "",
                "- **Tone:** Professional but friendly, casual, open",
                "- **Target audience:** Python programmers and people who want to learn it",
                "- **Emoji:** Use sparingly to highlight important information and emotions",
                "- **Each post should include:** Link to the meeting page",
                "- **Format:** Each post should be ready to paste directly on social media",
                '- **Dash:** Use the "-" character as a dash in descriptions',
                "",
                "## Example Post Formatting",
                "",
                "```",
                "🎉 Python Łódź meetup in a week!",
                "",
                "We're waiting for you on Friday at 18:00 at IndieBI 🚀",
                "",
                "This time we'll be talking about:",
                "✨ Clean architecture in Django",
                "✨ Visualizations in Python",
                "",
                "Sign up: [link to meetup]",
                "Live stream: [link to page]",
                "",
                "Join us on Discord: [link to Discord]",
                "```",
                "",
                "## Additional Information",
                "",
                "- Meetings have a casual format, preferring a family/friendly/open atmosphere",
                f"- Posts should be scheduled 2 weeks before the meeting which will be {self._format_date_long()}",
                "- Each post should be unique and not repeat itself",
                "- Posts can contain questions for the community",
                "- Encourage inviting friends",
                "",
                "## Prepare Posts in the Following Format",
                "",
                "For each post provide:",
                f"1. **Publication date** (2 weeks before the meeting which will be {self._format_date_long()})",
                "2. **Platform** (Facebook/Discord/Email)",
                "3. **Post content** (ready to paste)",
                "4. **Image prompt** (if an image should be included):",
                "   - Top content (text at the top of the image)",
                "   - Bottom content (text at the bottom of the image)",
                "",
                "Start preparing posts! 🚀",
            ]
        else:
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
                self._build_talks_section(lang),
                "## Agenda",
                "",
                self._build_agenda_section(lang),
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
                f"3. **Posty Informacyjne** - na 2 tygodni przed spotkaniem które będzie {self._format_date_long()}:",
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
                '- **Myślnik:** Używaj znaku "-" jako myślnika w opisach',
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
                f"- Posty mają być zaplanowane na 2 tygodni przed spotkaniem które będzie {self._format_date_long()}",
                "- Każdy post powinien być unikalny i nie powtarzać się",
                "- Posty mogą zawierać pytania do społeczności",
                "- Zachęcaj do zapraszania znajomych",
                "",
                "## Przygotuj Posty w Następującym Formacie",
                "",
                "Dla każdego posta podaj:",
                f"1. **Data publikacji** (na 2 tygodni przed spotkaniem które będzie {self._format_date_long()})",
                "2. **Platforma** (Facebook/Discord/Mail)",
                "3. **Treść posta** (gotowa do wklejenia)",
                "4. **Prompt do obrazka** (jeśli ma być dołączony obraz):",
                "   - Górna treść (tekst na górze obrazka)",
                "   - Dolna treść (tekst na dole obrazka)",
                "",
                "Zacznij od przygotowania postów! 🚀",
            ]

        return "\n".join(parts)

    def _build_sponsors_info(self, language: Language | None = None) -> str:
        """Build detailed sponsors information."""
        lang = language or self.meetup.language
        if not self.meetup.sponsors:
            return (
                "No sponsor information."
                if lang == Language.EN
                else "Brak informacji o sponsorach."
            )

        lines = []
        for sponsor_id in self.meetup.sponsors:
            sponsor = self.sponsor_repo.get_sponsor(sponsor_id)
            if sponsor:
                lines.append(f"**{sponsor.get('name', sponsor_id)}**")
                lines.append(f"Website: {sponsor.get('website', 'N/A')}")
                if sponsor.get("description"):
                    desc_label = "Description:" if lang == Language.EN else "Opis:"
                    lines.append(f"{desc_label} {sponsor.get('description')}")
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
