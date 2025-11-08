"""Repository for saving meetup descriptions."""

import logging
from pathlib import Path

from pyldz.descriptions.models import MeetupDescriptions

log = logging.getLogger(__name__)


class DescriptionRepository:
    """Save meetup descriptions to markdown files."""

    def __init__(self, meetups_content_dir: Path):
        """
        Initialize repository.

        Args:
            meetups_content_dir: Path to page/content/spotkania directory
        """
        self.meetups_content_dir = meetups_content_dir

    def save_all(self, meetup_id: str, descriptions: MeetupDescriptions) -> list[Path]:
        """
        Save all descriptions for a meetup.

        Args:
            meetup_id: The meetup ID
            descriptions: MeetupDescriptions object with all descriptions

        Returns:
            List of created file paths
        """
        descriptions_dir = self.meetups_content_dir / meetup_id / "descriptions"
        descriptions_dir.mkdir(parents=True, exist_ok=True)

        created_files = []

        # Save meetup.com description
        meetup_com_file = descriptions_dir / "meetup-com.md"
        meetup_com_file.write_text(descriptions.meetup_com, encoding="utf-8")
        log.info(f"Saved meetup.com description: {meetup_com_file}")
        created_files.append(meetup_com_file)

        # Save YouTube live description
        youtube_live_file = descriptions_dir / "youtube-live.md"
        youtube_live_file.write_text(descriptions.youtube_live, encoding="utf-8")
        log.info(f"Saved YouTube live description: {youtube_live_file}")
        created_files.append(youtube_live_file)

        # Save YouTube recording description
        youtube_recording_file = descriptions_dir / "youtube-recording.md"
        youtube_recording_file.write_text(
            descriptions.youtube_recording, encoding="utf-8"
        )
        log.info(f"Saved YouTube recording description: {youtube_recording_file}")
        created_files.append(youtube_recording_file)

        # Save YouTube recording descriptions for each talk
        talks_dir = descriptions_dir / "youtube-talks"
        talks_dir.mkdir(parents=True, exist_ok=True)
        for i, talk_desc in enumerate(descriptions.youtube_recording_talks, 1):
            talk_file = talks_dir / f"talk-{i}.md"
            content = f"# {talk_desc.title}\n\n{talk_desc.description}"
            talk_file.write_text(content, encoding="utf-8")
            log.info(f"Saved YouTube talk {i} description: {talk_file}")
            created_files.append(talk_file)

        # Save ChatGPT prompt
        chatgpt_prompt_file = descriptions_dir / "chatgpt-prompt.md"
        chatgpt_prompt_file.write_text(descriptions.chatgpt_prompt, encoding="utf-8")
        log.info(f"Saved ChatGPT prompt: {chatgpt_prompt_file}")
        created_files.append(chatgpt_prompt_file)

        return created_files
