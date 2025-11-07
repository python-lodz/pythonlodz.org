import logging
import shutil
from pathlib import Path

from pyldz.image_generator import MeetupImageGenerator
from pyldz.models import GoogleSheetsRepository, Meetup
from pyldz.speaker_yaml import write_speakers_yaml

log = logging.getLogger(__name__)


class HugoMeetupGenerator:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.meetups_dir = output_dir / "content" / "spotkania"

        # Initialize image generator
        assets_dir = output_dir / "assets"
        avatars_dir = assets_dir / "images" / "avatars"
        self.image_generator = MeetupImageGenerator(assets_dir, avatars_dir)

    def generate_meetup_markdown(self, meetup: Meetup) -> str:
        """Generate markdown content for a meetup."""
        content_parts = []

        # Add featured image
        content_parts.append('<img src="featured.png" alt="Infographic" />')
        content_parts.append("")

        # Add information section
        content_parts.append("## Informacje")
        content_parts.append("")
        content_parts.append(f"**📅 data:** {meetup.date}</br>")
        content_parts.append(f"**🕕 godzina:** {meetup.time}</br>")
        content_parts.append(f"**📍 miejsce:** {meetup.location_name}</br>")

        # Add meetup link if available
        if meetup.meetup_url:
            content_parts.append(f" ➡️ [**LINK DO ZAPISÓW**]({meetup.meetup_url}) ⬅️")

        # Add feedback link if available (TODO: Add feedback_url to Google Sheets)
        if meetup.feedback_url:
            content_parts.append(
                f" </br></br> 📝 [**ANKIETA** - oceń spotkanie oraz prelekcje]({meetup.feedback_url})"
            )

        content_parts.append("")

        # Add live stream if available (TODO: Add livestream_id to Google Sheets)
        if meetup.livestream_id:
            content_parts.append("## Live Stream")
            content_parts.append(
                f'{{{{< youtubeLite id="{meetup.livestream_id}" label="Label" >}}}}'
            )
            content_parts.append("")

        # Add talks section
        content_parts.append("## Prelekcje")
        content_parts.append("")

        if not meetup.talks:
            # No talks yet message
            content_parts.append(
                "Już wkrótce ogłosimy oficjalną agendę naszego najnowszego spotkania Python Łódź. "
                "Bądźcie czujni, bo szykujemy naprawdę interesujące prezentacje.\n\n"
                "Niezależnie od tematu, każde spotkanie to świetna okazja, by poszerzyć swoją wiedzę, "
                "poznać nowych ludzi i razem budować silną społeczność miłośników Pythona.\n\n"
                "Zarezerwuj swoje miejsce już teraz – nie daj się zaskoczyć, gdy ruszymy z pełną informacją o wydarzeniu."
            )
        else:
            # Add each talk
            for talk in meetup.talks:
                # Clean title (remove newlines and extra spaces)
                clean_title = " ".join(talk.title.split())
                content_parts.append(f"### {clean_title}")
                content_parts.append(
                    f'{{{{< speaker speaker_id="{talk.speaker_id}" >}}}}'
                )

                if talk.description:
                    # Convert newlines to markdown line breaks
                    description = talk.description.replace("\n", "  \n")
                    content_parts.append(description)

                if talk.youtube_id:
                    content_parts.append("#### Nagranie")
                    content_parts.append(
                        f'{{{{< youtubeLite id="{talk.youtube_id}" label="Label" >}}}}'
                    )

                content_parts.append("")

        # Add sponsors section
        content_parts.append("## Sponsorzy")
        for sponsor in meetup.sponsors:
            content_parts.append(f'{{{{< article link="/sponsorzy/{sponsor}/" >}}}}')
            content_parts.append("")

        # TODO: Add photos section (will need to check for images in resources)

        return "\n".join(content_parts)

    def generate_frontmatter(self, meetup: Meetup) -> str:
        """Generate Hugo frontmatter for a meetup."""
        frontmatter_parts = [
            "---",
            f'title: "{meetup.title}"',
            f"date: {meetup.date}T{meetup.time}:00+02:00",
            f'time: "{meetup.time}"',
            f'place: "{meetup.location_name}"',
            "---",
            "",
        ]
        return "\n".join(frontmatter_parts)

    def create_featured_image(
        self, meetup: Meetup, speakers: list, meetup_dir: Path
    ) -> Path:
        """Create a featured image for the meetup using Python image generation."""
        featured_image_path = meetup_dir / "featured.png"

        try:
            # Generate the image using the image generator
            self.image_generator.generate_featured_image(
                meetup, speakers, featured_image_path
            )
            log.info(f"Generated featured image for meetup {meetup.meetup_id}")
        except Exception as e:
            log.error(
                f"Failed to generate featured image for meetup {meetup.meetup_id}: {e}"
            )
            # Fallback to copying a template image
            template_image = (
                self.output_dir
                / "assets"
                / "images"
                / "python_lodz_logo_transparent_border.png"
            )
            if template_image.exists():
                shutil.copy2(template_image, featured_image_path)
                log.info(f"Used fallback template image for meetup {meetup.meetup_id}")
            else:
                # Create a simple text file as placeholder if no template exists
                placeholder_text = f"Featured image for {meetup.title}\nDate: {meetup.date}\nLocation: {meetup.location_name}"
                featured_image_path.with_suffix(".txt").write_text(
                    placeholder_text, encoding="utf-8"
                )
                log.warning(f"Created text placeholder for meetup {meetup.meetup_id}")

        return featured_image_path

    def create_meetup_file(self, meetup: Meetup, speakers: list) -> Path:
        """Create a markdown file for a meetup."""
        meetup_dir = self.meetups_dir / meetup.meetup_id
        meetup_dir.mkdir(parents=True, exist_ok=True)

        # Create featured image
        self.create_featured_image(meetup, speakers, meetup_dir)

        # Generate content
        frontmatter = self.generate_frontmatter(meetup)
        content = self.generate_meetup_markdown(meetup)

        # Write to file
        markdown_file = meetup_dir / "index.md"
        full_content = frontmatter + content
        markdown_file.write_text(full_content, encoding="utf-8")

        return markdown_file

    def generate_meetup(
        self, meetup_id: str, repository: GoogleSheetsRepository
    ) -> Path:
        meetup = repository.get_meetup_by_id(meetup_id)
        assert meetup is not None

        speakers = repository.get_speakers_for_meetup(
            meetup.meetup_id, repository._fetch_talks_data()
        )
        write_speakers_yaml(speakers, self.output_dir)
        return self.create_meetup_file(meetup, speakers)

    def generate_all_meetups(self, repository: GoogleSheetsRepository) -> list[Path]:
        meetups = repository.get_all_enabled_meetups()
        generated_files = []

        for meetup in meetups:
            speakers = repository.get_speakers_for_meetup(
                meetup.meetup_id, repository._fetch_talks_data()
            )
            file_path = self.create_meetup_file(meetup, speakers)
            generated_files.append(file_path)

        return generated_files
