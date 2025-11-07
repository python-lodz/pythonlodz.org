import logging
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from pyldz.models import Meetup, Speaker

log = logging.getLogger(__name__)


class ImageGenerationError(Exception):
    """Exception raised when image generation fails."""

    pass


class MeetupImageGenerator:
    def __init__(self, assets_dir: Path, cache_dir: Path | None = None):
        """
        Initialize the image generator.

        Args:
            assets_dir: Path to Hugo assets directory containing templates and fonts
            cache_dir: Optional directory for storing avatars (defaults to assets/images/avatars)
        """
        self.assets_dir = assets_dir
        # Store avatars directly under the Hugo assets directory so Hugo can access them
        # Default to the existing assets/images/avatars directory
        self.cache_dir = cache_dir or (assets_dir / "images" / "avatars")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Template paths
        self.template = assets_dir / "images" / "infographic_template.png"
        self.avatar_mask = assets_dir / "images" / "avatars" / "mask.png"
        self.tba_avatar = assets_dir / "images" / "avatars" / "tba.png"

        # Font paths
        self.font_normal = assets_dir / "fonts" / "OpenSans-Medium.ttf"
        self.font_bold = assets_dir / "fonts" / "OpenSans-Bold.ttf"

        # Colors
        self.text_color = "#393f5f"

    def generate_featured_image(
        self, meetup: Meetup, speakers: list[Speaker], output_path: Path
    ) -> Path:
        """
        Generate a featured image for a meetup.

        Args:
            meetup: Meetup data
            speakers: List of speakers for the meetup
            output_path: Where to save the generated image

        Returns:
            Path to the generated image
        """
        try:
            if meetup.is_to_be_announced:
                image = self._generate_tba_image(meetup)
            elif meetup.has_single_talk:
                speaker = self._find_speaker_by_id(speakers, meetup.talks[0].speaker_id)
                image = self._generate_solo_image(meetup, speaker)
            elif meetup.has_two_talks:
                speaker1 = self._find_speaker_by_id(
                    speakers, meetup.talks[0].speaker_id
                )
                speaker2 = self._find_speaker_by_id(
                    speakers, meetup.talks[1].speaker_id
                )
                image = self._generate_duo_image(meetup, speaker1, speaker2)
            else:
                raise Exception("Unsupported number of talks")

            output_path.parent.mkdir(parents=True, exist_ok=True)
            image.save(output_path, "PNG")
            log.info(f"Generated featured image: {output_path}")
            return output_path

        except Exception as e:
            raise ImageGenerationError(
                f"Failed to generate image for meetup {meetup.meetup_id}: {e}"
            ) from e

    def _generate_tba_image(self, meetup: Meetup) -> Image.Image:
        return self._generate_solo_image(meetup, None)

    def _find_speaker_by_id(
        self, speakers: list[Speaker], speaker_id: str
    ) -> Speaker | None:
        return next((s for s in speakers if s.id == speaker_id), None)

    def _generate_solo_image(
        self, meetup: Meetup, speaker: Speaker | None
    ) -> Image.Image:
        # Load template
        image = Image.open(self.template).convert("RGBA")
        draw = ImageDraw.Draw(image)

        # Add "ZAPRASZA" text
        font_66 = self._load_font(self.font_normal, 66)
        draw.text((890, 132), "ZAPRASZA", fill=self.text_color, font=font_66)

        # Add date text (centered)
        date_text = meetup.formatted_date_polish
        font_80 = self._load_font(self.font_normal, 80)
        img_width = image.width
        self._draw_centered_text(
            draw, date_text, img_width // 2, 267.5, font_80, self.text_color
        )

        # Add bottom date text
        font_28 = self._load_font(self.font_normal, 28)
        draw.text((157, 1014), date_text, fill=self.text_color, font=font_28)

        # Add bottom place text
        draw.text((1156, 1014), meetup.location, fill=self.text_color, font=font_28)

        tba_bg = Image.open(self.tba_avatar).convert("RGBA")
        image.paste(tba_bg, (779, 436), tba_bg)

        if speaker and len(meetup.talks) > 0:
            # Add speaker info
            talk = meetup.talks[0]

            # Speaker name (centered)
            font_32 = self._load_font(self.font_normal, 32)
            self._draw_centered_text(
                draw, speaker.name, img_width // 2, 815, font_32, self.text_color
            )

            # Talk title (centered)
            font_32_bold = self._load_font(self.font_bold, 32)
            self._draw_centered_text(
                draw, talk.title, img_width // 2, 870, font_32_bold, self.text_color
            )

            # Add speaker avatar
            avatar = self._get_speaker_avatar(speaker, (300, 300))
            masked_avatar = self._apply_circular_mask(avatar)
            avatar_x = (img_width // 2) - 150
            avatar_y = 465
            image.paste(masked_avatar, (avatar_x, avatar_y), masked_avatar)
        else:
            # No speaker - show TBA
            font_80_bold = self._load_font(self.font_bold, 80)
            self._draw_centered_text(
                draw, "TBA", img_width // 2, 800, font_80_bold, self.text_color
            )

        return image

    def _generate_duo_image(
        self, meetup: Meetup, speaker1: Speaker, speaker2: Speaker
    ) -> Image.Image:
        """Generate a duo meetup image using the universal template."""
        # Load template
        image = Image.open(self.template).convert("RGBA")
        draw = ImageDraw.Draw(image)

        # Add main date text (centered)
        date_text = meetup.formatted_date_polish
        font_80 = self._load_font(self.font_normal, 80)
        img_width = image.width
        self._draw_centered_text(
            draw, date_text, img_width // 2, 267.5, font_80, self.text_color
        )

        # Add bottom date text
        font_32 = self._load_font(self.font_normal, 32)
        draw.text((157, 1010.3), date_text, fill=self.text_color, font=font_32)

        # Add bottom place text
        draw.text((1156, 1010.3), meetup.location, fill=self.text_color, font=font_32)

        # First speaker (left side)
        talk1 = meetup.talks[0]

        # Speaker 1 name
        draw.text((428.7, 543.8), speaker1.name, fill=self.text_color, font=font_32)

        # Talk 1 title
        font_32_bold = self._load_font(self.font_bold, 32)
        draw.text((428.7, 592.1), talk1.title, fill=self.text_color, font=font_32_bold)

        # Speaker 1 avatar with rounded corners and TBA background
        avatar1 = self._get_speaker_avatar(speaker1, (240, 240))
        masked_avatar1 = self._apply_circular_mask(avatar1)

        # TBA background sized to avatar + 15% padding
        tba_bg = Image.open(self.tba_avatar).convert("RGBA")
        tba_size = int(240 * 1.15)  # 15% larger than avatar
        tba_bg_resized = tba_bg.resize((tba_size, tba_size), Image.Resampling.LANCZOS)

        # Center TBA background behind avatar
        tba_offset = (tba_size - 240) // 2
        tba_x = 122 - tba_offset
        tba_y = 490 - tba_offset
        image.paste(tba_bg_resized, (tba_x, tba_y), tba_bg_resized)

        # Paste avatar on top
        image.paste(masked_avatar1, (122, 490), masked_avatar1)

        # Second speaker (right side)
        talk2 = meetup.talks[1]

        # Speaker 2 name (right-aligned)
        self._draw_right_aligned_text(
            draw, speaker2.name, 1495.8, 656.6, font_32, self.text_color
        )

        # Talk 2 title (right-aligned)
        font_32_bold = self._load_font(self.font_bold, 32)
        self._draw_right_aligned_text(
            draw, talk2.title, 1495.8, 704.9, font_32_bold, self.text_color
        )

        # Speaker 2 avatar with rounded corners and TBA background
        avatar2 = self._get_speaker_avatar(speaker2, (240, 240))
        masked_avatar2 = self._apply_circular_mask(avatar2)

        # TBA background sized to avatar + 15% padding
        tba_bg2 = Image.open(self.tba_avatar).convert("RGBA")
        tba_size = int(240 * 1.15)  # 15% larger than avatar
        tba_bg_resized2 = tba_bg2.resize((tba_size, tba_size), Image.Resampling.LANCZOS)

        # Center TBA background behind avatar
        tba_offset = (tba_size - 240) // 2
        tba_x2 = 1537 - tba_offset
        tba_y2 = 585 - tba_offset
        image.paste(tba_bg_resized2, (tba_x2, tba_y2), tba_bg_resized2)

        # Paste avatar on top
        image.paste(masked_avatar2, (1537, 585), masked_avatar2)

        return image

    def _load_font(self, font_path: Path, size: int) -> ImageFont.FreeTypeFont:
        """Load a font with the specified size."""
        try:
            return ImageFont.truetype(str(font_path), size)
        except OSError:
            log.warning(f"Could not load font {font_path}, using default")
            return ImageFont.load_default()

    def _draw_centered_text(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        x: float,
        y: float,
        font: ImageFont.FreeTypeFont,
        color: str,
    ) -> None:
        """Draw text centered at the given position."""
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        draw.text((x - text_width // 2, y), text, fill=color, font=font)

    def _draw_right_aligned_text(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        x: float,
        y: float,
        font: ImageFont.FreeTypeFont,
        color: str,
    ) -> None:
        """Draw text right-aligned at the given position."""
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        draw.text((x - text_width, y), text, fill=color, font=font)

    def _get_speaker_avatar(
        self, speaker: Speaker, size: tuple[int, int]
    ) -> Image.Image:
        """Load speaker avatar, center on detected face, and resize.

        Returns None for general I/O errors. For fallback photos without faces,
        uses the image without face centering.
        """
        try:
            # Save original and processed avatars directly in assets/images/avatars
            raw_cache = self.cache_dir / f"{speaker.id}_original.png"
            processed_cache = self.cache_dir / f"{speaker.id}.png"

            if processed_cache.exists():
                avatar = Image.open(processed_cache).convert("RGBA")
            else:
                # Load original (possibly from raw cache)
                if raw_cache.exists():
                    original = Image.open(raw_cache).convert("RGBA")
                else:
                    original = Image.open(BytesIO(speaker.avatar.content)).convert(
                        "RGBA"
                    )
                    original.save(raw_cache, "PNG")
                    log.info(f"Saved original avatar for {speaker.name}: {raw_cache}")

                # Try to face-center and square-crop
                from pyldz import face_centering

                try:
                    centered = face_centering.detect_and_center_square(original)
                    centered.save(processed_cache, "PNG")
                    avatar = centered
                except face_centering.FaceDetectionError:
                    # For fallback photos (no_photo.png), use as-is without face centering
                    log.warning(
                        f"No face detected for {speaker.name}, using avatar without face centering"
                    )
                    original.save(processed_cache, "PNG")
                    avatar = original

            avatar = avatar.resize(size, Image.Resampling.LANCZOS)
            return avatar

        except Exception as e:
            raise ImageGenerationError(
                f"Failed to load avatar for {speaker.name}: {e}"
            ) from e

    def _apply_circular_mask(self, image: Image.Image) -> Image.Image:
        """Apply circular mask to an image."""
        if not self.avatar_mask.exists():
            log.warning(
                f"Avatar mask not found: {self.avatar_mask}, creating circular mask"
            )
            return self._create_circular_mask(image)

        try:
            mask = Image.open(self.avatar_mask).convert("L")
            mask = mask.resize(image.size, Image.Resampling.LANCZOS)

            # Apply mask
            result = Image.new("RGBA", image.size, (0, 0, 0, 0))
            result.paste(image, (0, 0))
            result.putalpha(mask)

            return result
        except Exception as e:
            log.warning(f"Could not apply mask: {e}, creating circular mask")
            return self._create_circular_mask(image)

    def _create_circular_mask(self, image: Image.Image) -> Image.Image:
        """Create a circular mask for an image."""
        size = image.size
        mask = Image.new("L", size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0) + size, fill=255)

        result = Image.new("RGBA", size, (0, 0, 0, 0))
        result.paste(image, (0, 0))
        result.putalpha(mask)

        return result
