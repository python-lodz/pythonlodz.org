import logging
from io import BytesIO
from pathlib import Path
from typing import Literal, Optional

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from pyldz.i18n import get_text
from pyldz.models import Language, Meetup, Speaker

log = logging.getLogger(__name__)


class ImageGenerationError(Exception):
    pass


class MeetupImageGenerator:
    """
    Generator grafik zapowiedzi:
    - tło: assets/images/bacground.png
    - ikony: assets/icons/calendar.png, assets/icons/pin.png
    - pełne tytuły (bez ucinania), dynamiczne karty
    - aspect presets: 16x9 (columns), 4x5/1x1 (stack)
    """

    def __init__(self, assets_dir: Path, cache_dir: Path | None = None):
        self.assets_dir = assets_dir
        self.cache_dir = cache_dir or (assets_dir / "images" / "avatars")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # zasoby
        self.background_path = (
            assets_dir / "images" / "bacground.png"
        )  # świadoma pisownia pliku
        self.avatar_mask = assets_dir / "images" / "avatars" / "mask.png"
        self.tba_avatar = assets_dir / "images" / "avatars" / "tba.png"
        self.logo_path = (
            assets_dir / "images" / "python_lodz_logo_transparent_border.png"
        )
        self.icon_calendar = assets_dir / "icons" / "calendar.png"
        self.icon_pin = assets_dir / "icons" / "pin.png"

        # fonty
        self.font_normal = assets_dir / "fonts" / "OpenSans-Medium.ttf"
        self.font_bold = assets_dir / "fonts" / "OpenSans-Bold.ttf"

        # kolory
        self.text = "#273C5A"
        self.text_muted = "#3E4A5A"
        self.accent = "#F7C51E"
        self.bg = (255, 255, 255, 255)

    # ---------------- public ----------------
    def generate_featured_image(
        self,
        meetup: Meetup,
        speakers: list[Speaker],
        output_path: Path,
        language: Language | None = None,
        *,
        aspect_ratio: Literal["16x9", "4x5", "1x1"] = "16x9",
        options: Optional[dict] = None,
    ) -> Path:
        language = language or meetup.language

        # presety zależne od proporcji
        preset = self._aspect_preset(aspect_ratio)
        opt = {
            "safe_margin": preset["safe_margin"],
            "max_content_width": preset["max_content_width"],
            "date_block_max_width_ratio": preset["date_block_max_width_ratio"],
            "overlay_opacity": 0.06,
            "duo_mode": preset["duo_mode"],  # "columns" albo "stack"
            "single_avatar": preset["single_avatar"],
            "duo_avatar": preset["duo_avatar"],
            "date_start_px": preset["date_start_px"],
            "date_y_ratio": preset["date_y_ratio"],
            "sep_width_ratio": preset["sep_width_ratio"],
            "base_y_gap": preset["base_y_gap"],
            "footer_font": preset["footer_font"],
            "icon_calendar": preset["icon_calendar"],
            "icon_pin": preset["icon_pin"],
        }
        if options:
            opt.update(options)

        try:
            # canvas + tło
            img = self._canvas(aspect_ratio)
            self._composite_background(img)
            draw = ImageDraw.Draw(img)

            # header
            self._draw_header(img, draw, language, opt)

            # centralna data - autoskala i realny dół pola
            date_text = meetup.formatted_date(language)
            font_date = self._autoscale_font(
                draw,
                date_text,
                self.font_bold,
                start=opt["date_start_px"],
                max_width=int(img.width * opt["date_block_max_width_ratio"]),
            )
            date_y = int(img.height * opt["date_y_ratio"])
            self._text_center(
                draw, date_text, img.width // 2, date_y, font_date, self.text
            )

            bbox = draw.textbbox((0, 0), date_text, font=font_date)
            date_bottom = date_y + (bbox[3] - bbox[1])

            # separator pod datą — visually separated from date text
            sep_w = int(img.width * opt["sep_width_ratio"])
            sep_x = (img.width - sep_w) // 2

            # use dynamic spacing relative to font size for proper balance
            font_height = bbox[3] - bbox[1]
            sep_gap = int(font_height * 0.45)  # more breathing space under the date
            sep_thickness = max(6, font_height // 14)
            sep_y = date_bottom + sep_gap

            draw.rectangle(
                (sep_x, sep_y, sep_x + sep_w, sep_y + sep_thickness), fill=self.accent
            )

            # punkt startowy sekcji prelegentów
            base_y = sep_y + opt["base_y_gap"]

            # prelegenci
            if meetup.is_to_be_announced:
                self._layout_tba(img, base_y, opt)
            elif meetup.has_single_talk:
                sp = self._find_speaker(speakers, meetup.talks[0].speaker_id)
                self._layout_single(img, sp, meetup.talks[0].title, opt, base_y)
            elif meetup.has_two_talks:
                sp1 = self._find_speaker(speakers, meetup.talks[0].speaker_id)
                sp2 = self._find_speaker(speakers, meetup.talks[1].speaker_id)
                if opt["duo_mode"] == "columns":
                    self._layout_duo_columns(
                        img,
                        sp1,
                        meetup.talks[0].title,
                        sp2,
                        meetup.talks[1].title,
                        opt,
                        base_y,
                    )
                else:
                    self._layout_duo_stack(
                        img,
                        sp1,
                        meetup.talks[0].title,
                        sp2,
                        meetup.talks[1].title,
                        opt,
                        base_y,
                    )
            else:
                raise Exception("Unsupported number of talks")

            # dolny pasek
            self._draw_bottom_bar(
                img, draw, date_text, meetup.location_name(language), opt
            )

            output_path.parent.mkdir(parents=True, exist_ok=True)
            img.save(output_path, "PNG")
            return output_path

        except Exception as e:
            raise ImageGenerationError(
                f"Failed to generate image for meetup {meetup.meetup_id}: {e}"
            ) from e

    # ---------------- aspect presets ----------------
    def _aspect_preset(self, aspect: str) -> dict:
        if aspect == "16x9":
            return {
                "safe_margin": 80,
                "max_content_width": 1440,
                "date_block_max_width_ratio": 0.75,
                "duo_mode": "columns",
                "single_avatar": 300,
                "duo_avatar": 240,
                "date_start_px": 120,
                "date_y_ratio": 0.24,
                "sep_width_ratio": 0.70,
                "base_y_gap": 36,
                "footer_font": 32,
                "icon_calendar": 64,
                "icon_pin": 56,
            }
        if aspect == "4x5":
            return {
                "safe_margin": 64,
                "max_content_width": 920,
                "date_block_max_width_ratio": 0.85,
                "duo_mode": "stack",
                "single_avatar": 300,
                "duo_avatar": 260,
                "date_start_px": 108,
                "date_y_ratio": 0.21,
                "sep_width_ratio": 0.80,
                "base_y_gap": 36,
                "footer_font": 28,
                "icon_calendar": 56,
                "icon_pin": 50,
            }
        if aspect == "1x1":
            return {
                "safe_margin": 56,
                "max_content_width": 920,
                "date_block_max_width_ratio": 0.85,
                "duo_mode": "stack",
                "single_avatar": 300,
                "duo_avatar": 260,
                "date_start_px": 104,
                "date_y_ratio": 0.20,
                "sep_width_ratio": 0.80,
                "base_y_gap": 34,
                "footer_font": 28,
                "icon_calendar": 56,
                "icon_pin": 50,
            }
        # fallback
        return self._aspect_preset("16x9")

    # ---------------- header & footer ----------------
    def _draw_header(
        self, img: Image.Image, draw: ImageDraw.ImageDraw, lang: Language, opt: dict
    ):
        top = opt["safe_margin"]
        x = opt["safe_margin"]

        if self.logo_path.exists():
            try:
                logo = Image.open(self.logo_path).convert("RGBA")
                ratio = 84 / logo.height
                logo = logo.resize(
                    (int(logo.width * ratio), 84), Image.Resampling.LANCZOS
                )
                img.alpha_composite(logo, (x, top))
                x += logo.width + 20
            except Exception as e:
                log.warning(f"Cannot load logo: {e}")

        invites = get_text(lang, "invites")
        font_brand = self._load_font(self.font_bold, 54)
        draw.text(
            (x, top + 6), "PYTHON ŁÓDŹ - PUG", fill=self.text_muted, font=font_brand
        )
        font_inv = self._load_font(self.font_bold, 66)
        draw.text((x, top + 60), invites, fill=self.text, font=font_inv)

    def _draw_bottom_bar(
        self,
        img: Image.Image,
        draw: ImageDraw.ImageDraw,
        date_text: str,
        place_text: str,
        opt: dict,
    ):
        h = 110
        y0 = img.height - h
        draw.rectangle((0, y0, img.width, img.height), fill=self.accent)
        font = self._load_font(self.font_bold, opt["footer_font"])

        # ikona kalendarza
        if self.icon_calendar.exists():
            try:
                icon_cal = Image.open(self.icon_calendar).convert("RGBA")
                icon_cal = icon_cal.resize(
                    (opt["icon_calendar"], opt["icon_calendar"]),
                    Image.Resampling.LANCZOS,
                )
                img.alpha_composite(
                    icon_cal, (opt["safe_margin"], y0 + (h - opt["icon_calendar"]) // 2)
                )
            except Exception as e:
                log.warning(f"Cannot load calendar icon: {e}")

        # data
        draw.text(
            (
                opt["safe_margin"] + opt["icon_calendar"] + 16,
                y0 + (h - opt["footer_font"]) // 2 + 6,
            ),
            date_text,
            fill=self.text,
            font=font,
        )

        # ikona pinezki i miejsce
        if self.icon_pin.exists():
            try:
                icon_pin = Image.open(self.icon_pin).convert("RGBA")
                icon_pin = icon_pin.resize(
                    (opt["icon_pin"], opt["icon_pin"]), Image.Resampling.LANCZOS
                )
                w_place = draw.textbbox((0, 0), place_text, font=font)[2]
                x_pin = (
                    img.width - opt["safe_margin"] - w_place - (opt["icon_pin"] + 16)
                )
                img.alpha_composite(icon_pin, (x_pin, y0 + (h - opt["icon_pin"]) // 2))
            except Exception as e:
                log.warning(f"Cannot load pin icon: {e}")

        self._text_right(
            draw,
            place_text,
            img.width - opt["safe_margin"],
            y0 + (h - opt["footer_font"]) // 2 + 6,
            font,
            self.text,
        )

    # ---------------- layouts ----------------
    def _layout_tba(self, img: Image.Image, base_y: int, opt: dict):
        cx = img.width // 2
        d = 300
        badge = self._tba_badge(d)
        y = base_y + 10
        img.paste(badge, (cx - d // 2, y), badge)

    def _layout_single(
        self, img: Image.Image, sp: Speaker, title: str, opt: dict, base_y: int
    ):
        draw = ImageDraw.Draw(img)
        box_w = min(opt["max_content_width"], img.width - 2 * opt["safe_margin"])
        box_x = (img.width - box_w) // 2
        box_y = base_y

        size = opt["single_avatar"]
        name_f = self._load_font(self.font_normal, 36)
        title_f = self._load_font(self.font_bold, 32)

        av = self._apply_circular_mask(self._avatar(sp, (size, size)))
        lines = self._wrap_unbounded(draw, title, title_f, int(box_w * 0.9))
        title_h = self._multiline_height(draw, lines, title_f, gap=6)
        name_h = draw.textbbox((0, 0), sp.name, font=name_f)[3]
        gap1, gap2 = 16, 44
        box_h = size + gap1 + name_h + gap2 + title_h + 20

        self._overlay(
            img, (box_x, box_y, box_x + box_w, box_y + box_h), opt["overlay_opacity"]
        )
        av_x = img.width // 2 - size // 2
        self._paste_with_ring(img, av, (av_x, box_y))
        name_y = box_y + size + gap1
        self._text_center(
            draw, sp.name, img.width // 2, name_y, name_f, self.text_muted
        )
        title_y = name_y + name_h + gap2
        self._text_center_multiline(
            draw, lines, img.width // 2, title_y, title_f, self.text
        )

    # --- duo: wariant kolumnowy (16x9) ---
    def _layout_duo_columns(
        self,
        img: Image.Image,
        sp1: Speaker,
        t1: str,
        sp2: Speaker,
        t2: str,
        opt: dict,
        base_y: int,
    ):
        draw = ImageDraw.Draw(img)
        box_w = min(opt["max_content_width"], img.width - 2 * opt["safe_margin"])
        box_x = (img.width - box_w) // 2
        box_y = base_y

        col_gap = 60
        col_w = (box_w - col_gap) // 2
        size = opt["duo_avatar"]
        name_f = self._load_font(self.font_normal, 36)
        title_f = self._load_font(self.font_bold, 32)

        lines1 = self._wrap_unbounded(draw, t1, title_f, col_w - size - 40)
        lines2 = self._wrap_unbounded(draw, t2, title_f, col_w - size - 40)
        title_h1 = self._multiline_height(draw, lines1, title_f, gap=6)
        title_h2 = self._multiline_height(draw, lines2, title_f, gap=6)
        name_h = draw.textbbox((0, 0), sp1.name, font=name_f)[3]

        left_block_h = max(size, 10 + name_h + 40 + title_h1)
        right_block_h = max(size + 60, 80 + name_h + 40 + title_h2)
        box_h = max(left_block_h, right_block_h) + 24

        self._overlay(
            img, (box_x, box_y, box_x + box_w, box_y + box_h), opt["overlay_opacity"]
        )

        # left
        left_x = box_x
        av1 = self._apply_circular_mask(self._avatar(sp1, (size, size)))
        self._paste_with_ring(img, av1, (left_x, box_y))
        draw.text(
            (left_x + size + 26, box_y + 10),
            sp1.name,
            fill=self.text_muted,
            font=name_f,
        )
        self._text_multiline(
            draw,
            lines1,
            left_x + size + 26,
            box_y + 10 + name_h + 30,
            title_f,
            self.text,
        )

        # right
        right_x = box_x + col_w + col_gap
        av2 = self._apply_circular_mask(self._avatar(sp2, (size, size)))
        self._paste_with_ring(img, av2, (right_x + col_w - size, box_y + 60))
        self._text_right(
            draw,
            sp2.name,
            right_x + col_w - size - 26,
            box_y + 60 + 10,
            name_f,
            self.text_muted,
        )
        self._text_right_multiline(
            draw,
            lines2,
            right_x + col_w - size - 26,
            box_y + 60 + 10 + name_h + 30,
            title_f,
            self.text,
        )

    # --- duo: wariant "stack" (4x5, 1x1) ---
    def _layout_duo_stack(
        self,
        img: Image.Image,
        sp1: Speaker,
        t1: str,
        sp2: Speaker,
        t2: str,
        opt: dict,
        base_y: int,
    ):
        draw = ImageDraw.Draw(img)
        box_w = min(opt["max_content_width"], img.width - 2 * opt["safe_margin"])
        box_x = (img.width - box_w) // 2
        size = opt["duo_avatar"]
        name_f = self._load_font(self.font_normal, 36)
        title_f = self._load_font(self.font_bold, 32)

        # kolumna A (pełna szerokość)
        lines1 = self._wrap_unbounded(draw, t1, title_f, int(box_w * 0.9))
        title_h1 = self._multiline_height(draw, lines1, title_f, gap=6)
        name_h1 = draw.textbbox((0, 0), sp1.name, font=name_f)[3]
        block_h1 = size + 16 + name_h1 + 40 + title_h1 + 12

        # kolumna B (pełna szerokość)
        lines2 = self._wrap_unbounded(draw, t2, title_f, int(box_w * 0.9))
        title_h2 = self._multiline_height(draw, lines2, title_f, gap=6)
        name_h2 = draw.textbbox((0, 0), sp2.name, font=name_f)[3]
        block_h2 = size + 16 + name_h2 + 40 + title_h2 + 12

        box_h = block_h1 + 36 + block_h2
        box_y = base_y
        self._overlay(
            img, (box_x, box_y, box_x + box_w, box_y + box_h), opt["overlay_opacity"]
        )

        # A
        av1 = self._apply_circular_mask(self._avatar(sp1, (size, size)))
        av1_x = box_x + (box_w - size) // 2
        self._paste_with_ring(img, av1, (av1_x, box_y))
        self._text_center(
            draw,
            sp1.name,
            box_x + box_w // 2,
            box_y + size + 16,
            name_f,
            self.text_muted,
        )
        self._text_center_multiline(
            draw,
            lines1,
            box_x + box_w // 2,
            box_y + size + 16 + name_h1 + 40,
            title_f,
            self.text,
        )

        # B
        off_y = box_y + block_h1 + 36
        av2 = self._apply_circular_mask(self._avatar(sp2, (size, size)))
        av2_x = box_x + (box_w - size) // 2
        self._paste_with_ring(img, av2, (av2_x, off_y))
        self._text_center(
            draw,
            sp2.name,
            box_x + box_w // 2,
            off_y + size + 16,
            name_f,
            self.text_muted,
        )
        self._text_center_multiline(
            draw,
            lines2,
            box_x + box_w // 2,
            off_y + size + 16 + name_h2 + 40,
            title_f,
            self.text,
        )

    # ---------------- helpers - canvas ----------------
    def _canvas(self, aspect: str) -> Image.Image:
        if aspect == "4x5":
            return Image.new("RGBA", (1080, 1350), self.bg)
        if aspect == "1x1":
            return Image.new("RGBA", (1080, 1080), self.bg)
        return Image.new("RGBA", (1920, 1080), self.bg)

    def _composite_background(self, canvas: Image.Image):
        if not self.background_path.exists():
            log.warning(f"Background not found: {self.background_path}")
            return
        bg = Image.open(self.background_path).convert("RGBA")
        ratio = max(canvas.width / bg.width, canvas.height / bg.height)
        new_size = (int(bg.width * ratio), int(bg.height * ratio))
        bg = bg.resize(new_size, Image.Resampling.LANCZOS)
        x = (canvas.width - new_size[0]) // 2
        y = (canvas.height - new_size[1]) // 2
        canvas.alpha_composite(bg, (x, y))

    # ---------------- helpers - text & drawing ----------------
    def _overlay(self, img: Image.Image, box, opacity: float):
        alpha = max(0, min(255, int(opacity * 255)))
        overlay = Image.new(
            "RGBA", (box[2] - box[0], box[3] - box[1]), (255, 255, 255, alpha)
        )
        img.alpha_composite(overlay, (box[0], box[1]))

    def _autoscale_font(self, draw, text, font_path: Path, start: int, max_width: int):
        size = start
        while size >= 40:
            f = self._load_font(font_path, size)
            w = draw.textbbox((0, 0), text, font=f)[2]
            if w <= max_width:
                return f
            size -= 2
        return self._load_font(font_path, 40)

    def _wrap_unbounded(self, draw, text, font, max_w):
        words, lines, cur = text.split(), [], []
        for w in words:
            test = " ".join(cur + [w])
            if draw.textbbox((0, 0), test, font=font)[2] <= max_w:
                cur.append(w)
            else:
                if cur:
                    lines.append(" ".join(cur))
                cur = [w]
        if cur:
            lines.append(" ".join(cur))
        return lines

    def _multiline_height(self, draw, lines, font, gap=6):
        if not lines:
            return 0
        h = 0
        for ln in lines:
            h += draw.textbbox((0, 0), ln, font=font)[3] + gap
        return h - gap

    def _text_center(self, draw, text, x, y, font, color):
        w = draw.textbbox((0, 0), text, font=font)[2]
        draw.text((x - w // 2, y), text, fill=color, font=font)

    def _text_right(self, draw, text, right_x, y, font, color):
        w = draw.textbbox((0, 0), text, font=font)[2]
        draw.text((right_x - w, y), text, fill=color, font=font)

    def _text_center_multiline(self, draw, lines, cx, top_y, font, color, gap=6):
        y = top_y
        for ln in lines:
            w = draw.textbbox((0, 0), ln, font=font)[2]
            draw.text((cx - w // 2, y), ln, fill=color, font=font)
            y += draw.textbbox((0, 0), ln, font=font)[3] + gap

    def _text_multiline(self, draw, lines, x, top_y, font, color, gap=6):
        y = top_y
        for ln in lines:
            draw.text((x, y), ln, fill=color, font=font)
            y += draw.textbbox((0, 0), ln, font=font)[3] + gap

    def _text_right_multiline(self, draw, lines, right_x, top_y, font, color, gap=6):
        y = top_y
        for ln in lines:
            w = draw.textbbox((0, 0), ln, font=font)[2]
            draw.text((right_x - w, y), ln, fill=color, font=font)
            y += draw.textbbox((0, 0), ln, font=font)[3] + gap

    # ---------------- helpers - assets ----------------
    def _find_speaker(self, speakers: list[Speaker], speaker_id: str) -> Speaker:
        return next(s for s in speakers if s.id == speaker_id)

    def _load_font(self, path: Path, size: int):
        try:
            return ImageFont.truetype(str(path), size)
        except OSError:
            log.warning(f"Could not load font {path}, using default")
            return ImageFont.load_default()

    def _avatar(self, speaker: Speaker, size: tuple[int, int]) -> Image.Image:
        try:
            raw = self.cache_dir / f"{speaker.id}_original.png"
            processed = self.cache_dir / f"{speaker.id}.png"
            if processed.exists():
                img = Image.open(processed).convert("RGBA")
            else:
                if raw.exists():
                    original = Image.open(raw).convert("RGBA")
                else:
                    original = Image.open(BytesIO(speaker.avatar.content)).convert(
                        "RGBA"
                    )
                    original.save(raw, "PNG")
                from pyldz import face_centering

                try:
                    centered = face_centering.detect_and_center_square(original)
                    centered.save(processed, "PNG")
                    img = centered
                except face_centering.FaceDetectionError:
                    original.save(processed, "PNG")
                    img = original
            return img.resize(size, Image.Resampling.LANCZOS)
        except Exception as e:
            raise ImageGenerationError(
                f"Failed to load avatar for {speaker.name}: {e}"
            ) from e

    def _apply_circular_mask(self, img: Image.Image) -> Image.Image:
        if not self.avatar_mask.exists():
            return self._circle_mask(img)
        try:
            m = (
                Image.open(self.avatar_mask)
                .convert("L")
                .resize(img.size, Image.Resampling.LANCZOS)
            )
            out = Image.new("RGBA", img.size, (0, 0, 0, 0))
            out.paste(img, (0, 0))
            out.putalpha(m)
            return out
        except Exception:
            return self._circle_mask(img)

    def _circle_mask(self, img: Image.Image) -> Image.Image:
        size = img.size
        m = Image.new("L", size, 0)
        d = ImageDraw.Draw(m)
        d.ellipse((0, 0) + size, fill=255)
        out = Image.new("RGBA", size, (0, 0, 0, 0))
        out.paste(img, (0, 0))
        out.putalpha(m)
        return out

    def _tba_badge(self, diameter: int) -> Image.Image:
        if self.tba_avatar.exists():
            return (
                Image.open(self.tba_avatar)
                .convert("RGBA")
                .resize((diameter, diameter), Image.Resampling.LANCZOS)
            )
        img = Image.new("RGBA", (diameter, diameter), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.ellipse((0, 0, diameter, diameter), fill=(255, 255, 255, 255))
        ring = max(8, diameter // 18)
        d.ellipse(
            (ring, ring, diameter - ring, diameter - ring),
            outline=self.accent,
            width=ring,
        )
        qf = self._load_font(self.font_bold, int(diameter * 0.55))
        d.text(
            self._center_text_in_circle(d, "?", qf, diameter),
            "?",
            fill=(0, 0, 0, 255),
            font=qf,
        )
        return img

    @staticmethod
    def _center_text_in_circle(
        draw: ImageDraw.ImageDraw,
        text: str,
        font: ImageFont.FreeTypeFont,
        diameter: int,
    ):
        bbox = draw.textbbox((0, 0), text, font=font)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        return ((diameter - w) // 2, (diameter - h) // 2)

    def _paste_with_ring(
        self, img: Image.Image, avatar: Image.Image, topleft: tuple[int, int]
    ):
        size = avatar.width
        # cień
        shadow = Image.new("RGBA", (size + 34, size + 34), (0, 0, 0, 0))
        d = ImageDraw.Draw(shadow)
        d.ellipse((10, 10, size + 24, size + 24), fill=(0, 0, 0, 60))
        shadow = shadow.filter(ImageFilter.GaussianBlur(8))
        img.alpha_composite(shadow, (topleft[0] - 12, topleft[1] - 12))
        # żółty ring
        ring = Image.new("RGBA", (size + 16, size + 16), (0, 0, 0, 0))
        dr = ImageDraw.Draw(ring)
        dr.ellipse((0, 0, size + 16, size + 16), outline=self.accent, width=12)
        img.alpha_composite(ring, (topleft[0] - 8, topleft[1] - 8))
        # avatar
        img.paste(avatar, topleft, avatar)
