import logging
import math
from datetime import date as date_cls
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Literal, Optional, Tuple

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from pyldz.i18n import get_text
from pyldz.models import Language, Meetup, Speaker

log = logging.getLogger(__name__)


class ImageGenerationError(Exception):
    pass


class MeetupImageGenerator:
    """
    Generator grafik zapowiedzi (variant: dev-clean 2025-11):
    - jasne tło z mocno rozjaśnioną geometrią
    - nagłówek: "PYTHON ŁÓDŹ #<id>" wyśrodkowany
    - data (YYYY MM DD) w żółtym akcencie + poniżej "DZIEŃ, HH:MM"
    - prelegenci: okrągłe avatary z cienkim ringiem; nazwisko nad środkiem awatara,
      a pierwsza linia tytułu startuje dokładnie na wysokości środka awatara
    - stopka bez paska:
        * lewy dół: skośny blok CG (większy) z "Meetup #<id>" i "pythonlodz.org"
        * środek: sama lokalizacja (z pinem)
        * prawy dół: #PythonLodz w kolorze CG + lekki biały cień
    """

    # ---------------- init ----------------
    def __init__(self, assets_dir: Path, cache_dir: Path | None = None):
        self.assets_dir = assets_dir
        self.cache_dir = cache_dir or (assets_dir / "images" / "avatars")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # zasoby
        self.background_path = (
            assets_dir / "images" / "bacground.png"
        )  # świadoma pisownia
        self.avatar_mask = assets_dir / "images" / "avatars" / "mask.png"
        self.tba_avatar = assets_dir / "images" / "avatars" / "tba.png"
        self.logo_path = (
            assets_dir / "images" / "python_lodz_logo_transparent_border.png"
        )

        # ikony
        self.icon_link = assets_dir / "icons" / "link.png"
        self.icon_pin = assets_dir / "icons" / "pin.png"
        self.icon_flag_gb = assets_dir / "icons" / "flag_gb.png"  # NEW

        # fonty
        self.font_normal = assets_dir / "fonts" / "OpenSans-Medium.ttf"
        self.font_bold = assets_dir / "fonts" / "OpenSans-Bold.ttf"

        # paleta
        self.YA = "#FFD700"  # Żółty Akcent
        self.CG = "#001F3F"  # Ciemny Granat
        self.JS = "#F5F5F5"  # Jasny Szary
        self.CT = "#333333"  # Ciemny Tekst
        self.SS = "#666666"  # Średni Szary

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

        preset = self._aspect_preset(aspect_ratio)
        opt = {
            "safe_margin": preset["safe_margin"],
            "max_content_width": preset["max_content_width"],
            "date_block_max_width_ratio": preset["date_block_max_width_ratio"],
            "overlay_opacity": 0.04,
            "duo_mode": preset["duo_mode"],
            "single_avatar": preset["single_avatar"],
            "duo_avatar": preset["duo_avatar"],
            "date_start_px": preset["date_start_px"],
            "date_y_ratio": preset["date_y_ratio"],
            "sep_width_ratio": preset["sep_width_ratio"],
            "base_y_gap": preset["base_y_gap"],
            "footer_font": preset["footer_font"],
            "icon_link": preset["icon_link"],
            "icon_pin": preset["icon_pin"],
        }
        if options:
            opt.update(options)

        try:
            # canvas + tło
            img = self._canvas(aspect_ratio)
            self._composite_background(img, fade=0.05)
            draw = ImageDraw.Draw(img)

            # nagłówek
            meetup_id = getattr(meetup, "meetup_id", "") or getattr(meetup, "id", "")
            header = f"PYTHON ŁÓDŹ #{meetup_id}".strip()
            self._draw_header_centered(img, draw, header, opt)

            # wstęga EN w prawym górnym rogu (równoległa do trójkąta, krawędź->krawędź)
            if language == Language.EN:
                self._draw_top_right_ribbon_en(img, opt)

            # data / godzina
            day_name, date_label, time_label = self._resolve_date_parts(
                meetup, language
            )
            font_date = self._autoscale_font(
                draw,
                date_label,
                self.font_bold,
                start=opt["date_start_px"],
                max_width=int(img.width * opt["date_block_max_width_ratio"]),
            )
            date_y = int(img.height * opt["date_y_ratio"])
            self._text_center_shadowed(
                draw, date_label, img.width // 2, date_y, font_date, self.YA
            )

            if time_label or day_name:
                combo = f"{day_name}, {time_label}" if day_name else time_label
                time_font = self._load_font(
                    self.font_bold, max(40, int(font_date.size * 0.62))
                )
                combo_y = (
                    date_y + draw.textbbox((0, 0), date_label, font=font_date)[3] + 8
                )
                self._text_center_shadowed(
                    draw, combo, img.width // 2, combo_y, time_font, self.CT
                )
                block_bottom = combo_y + draw.textbbox((0, 0), combo, font=time_font)[3]
            else:
                block_bottom = (
                    date_y + draw.textbbox((0, 0), date_label, font=font_date)[3]
                )

            # separator – wyliczony stałe, NIE rysujemy już żadnego napisu pod datą
            sep_w = int(img.width * opt["sep_width_ratio"])
            sep_x = (img.width - sep_w) // 2
            sep_y = block_bottom + 12
            draw.rectangle((sep_x, sep_y, sep_x + sep_w, sep_y + 1), fill=self.JS)

            # sekcja prelegentów
            base_y = sep_y + opt["base_y_gap"]

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

            # stopka
            site_text = getattr(meetup, "website", None) or "pythonlodz.org"
            self._draw_corner_footer(
                img, draw, site_text, meetup.location_name(language), meetup_id, opt
            )

            output_path.parent.mkdir(parents=True, exist_ok=True)
            img.save(output_path, "PNG")
            return output_path

        except Exception as e:
            raise ImageGenerationError(
                f"Failed to generate image for meetup {getattr(meetup, 'meetup_id', '?')}: {e}"
            ) from e

    # ---------------- aspect presets ----------------
    def _aspect_preset(self, aspect: str) -> dict:
        if aspect == "16x9":
            return {
                "safe_margin": 80,
                "max_content_width": 1500,
                "date_block_max_width_ratio": 0.84,
                "duo_mode": "columns",
                "single_avatar": 330,
                "duo_avatar": 280,
                "date_start_px": 136,
                "date_y_ratio": 0.23,
                "sep_width_ratio": 0.66,
                "base_y_gap": 68,
                "footer_font": 30,
                "icon_link": 56,
                "icon_pin": 50,
            }
        if aspect == "4x5":
            return {
                "safe_margin": 72,
                "max_content_width": 980,
                "date_block_max_width_ratio": 0.90,
                "duo_mode": "stack",
                "single_avatar": 330,
                "duo_avatar": 288,
                "date_start_px": 122,
                "date_y_ratio": 0.21,
                "sep_width_ratio": 0.74,
                "base_y_gap": 76,
                "footer_font": 30,
                "icon_link": 52,
                "icon_pin": 48,
            }
        if aspect == "1x1":
            return {
                "safe_margin": 64,
                "max_content_width": 980,
                "date_block_max_width_ratio": 0.90,
                "duo_mode": "stack",
                "single_avatar": 330,
                "duo_avatar": 288,
                "date_start_px": 118,
                "date_y_ratio": 0.20,
                "sep_width_ratio": 0.74,
                "base_y_gap": 72,
                "footer_font": 30,
                "icon_link": 52,
                "icon_pin": 48,
            }
        return self._aspect_preset("16x9")

    # ---------------- header ----------------
    def _draw_header_centered(
        self, img: Image.Image, draw: ImageDraw.ImageDraw, title: str, opt: dict
    ):
        font_title = self._load_font(self.font_bold, 70)
        title_w = draw.textbbox((0, 0), title, font=font_title)[2]

        logo_w = 0
        logo_img = None
        if self.logo_path.exists():
            try:
                logo_img = Image.open(self.logo_path).convert("RGBA")
                target_h = 110
                ratio = target_h / logo_img.height
                logo_img = logo_img.resize(
                    (int(logo_img.width * ratio), target_h), Image.Resampling.LANCZOS
                )
                logo_w = logo_img.width + 18
            except Exception as e:
                log.warning(f"Cannot load logo: {e}")
                logo_img = None
                logo_w = 0

        group_w = logo_w + title_w
        x0 = (img.width - group_w) // 2
        top = opt["safe_margin"]

        if logo_img is not None:
            img.alpha_composite(logo_img, (x0, top))
        text_x = x0 + logo_w
        text_y = top + max(0, (110 - 70) // 2)
        self._draw_text_with_shadow(
            img,
            title,
            (text_x, text_y),
            font_title,
            self.CT,
            shadow_color=(0, 0, 0, 90),
        )

    def _draw_top_right_ribbon_en(
        self, img: Image.Image, opt: dict, label: str = "ENGLISH EDITION"
    ):
        """
        Ukośna wstęga w prawym górnym rogu:
        - równoległa do krawędzi trójkąta (atan2(0.26*H, 0.36*W)),
        - od krawędzi do krawędzi z nadmiarem (brak szczelin),
        - flaga + napis wycentrowane na osi wstęgi.
        """
        W, H = img.width, img.height

        # kąt jak krawędź trójkąta z lewego dołu
        theta = math.atan2(0.26 * H, 0.36 * W)
        cos_t, sin_t = math.cos(theta), math.sin(theta)

        # odległości punktów końcowych na krawędziach
        m = int(0.28 * W)  # po górnej krawędzi od prawej
        n = int(m * math.tan(theta))  # w dół po prawej krawędzi

        # overshoot – rysujemy nieco poza płótnem, by zniknęły szczeliny na rogach
        thickness = 72
        overshoot = thickness * 2

        # baza odcinka (z nadmiarem poza obraz)
        A = (
            W - m - int(overshoot * cos_t),
            0 - int(overshoot * sin_t),
        )  # powyżej górnej krawędzi
        B = (
            W + int(overshoot * cos_t),
            n + int(overshoot * sin_t),
        )  # za prawą krawędzią

        # wektory jednostkowe
        ux, uy = (cos_t, sin_t)
        nx, ny = (-uy, ux)  # prostopadły

        half_t = thickness / 2.0

        def add(p, dx, dy):
            return (int(p[0] + dx), int(p[1] + dy))

        # narożniki wstęgi (paralelogram)
        p1 = add(A, nx * half_t, ny * half_t)
        p2 = add(B, nx * half_t, ny * half_t)
        p3 = add(B, -nx * half_t, -ny * half_t)
        p4 = add(A, -nx * half_t, -ny * half_t)

        # cień
        shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sd = ImageDraw.Draw(shadow)
        sd.polygon([p1, p2, p3, p4], fill=(0, 0, 0, 80))
        shadow = shadow.filter(ImageFilter.GaussianBlur(6))
        img.alpha_composite(shadow)

        # wstęga
        ribbon = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        rd = ImageDraw.Draw(ribbon)
        rd.polygon([p1, p2, p3, p4], fill=self.CG)

        # treść (flaga + napis) – osobna warstwa obracana o -theta
        axis_len = math.hypot(B[0] - A[0], B[1] - A[1])
        txt_pad = 32
        box_w = int(axis_len - 2 * txt_pad)
        box_h = int(thickness - 16)
        if box_w < 120 or box_h < 30:
            img.alpha_composite(ribbon)
            return

        content = Image.new("RGBA", (box_w, box_h), (0, 0, 0, 0))
        cd = ImageDraw.Draw(content)

        # flaga
        flag_img = None
        flag_h = min(box_h - 10, 40)
        flag_w = flag_h
        if self.icon_flag_gb and self.icon_flag_gb.exists():
            try:
                flag_img = (
                    Image.open(self.icon_flag_gb)
                    .convert("RGBA")
                    .resize((flag_w, flag_h), Image.Resampling.LANCZOS)
                )
            except Exception:
                flag_img = None

        font = self._load_font(self.font_bold, 34)
        label_w = cd.textbbox((0, 0), label, font=font)[2]
        gap = 12 if flag_img else 0
        total_w = label_w + (flag_w + gap if flag_img else 0)

        x0 = max(0, (box_w - total_w) // 2)
        y0 = (box_h - cd.textbbox((0, 0), label, font=font)[3]) // 2

        if flag_img:
            content.alpha_composite(flag_img, (x0, (box_h - flag_h) // 2))
            x0 += flag_w + gap

        # lekki biały cień plus biały tekst
        cd.text((x0, y0 + 2), label, font=font, fill=(255, 255, 255, 90))
        cd.text((x0, y0), label, font=font, fill="#FFFFFF")

        content_rot = content.rotate(-math.degrees(theta), expand=True)

        # środek odcinka A–B (po overshoot nadal OK)
        mid = ((A[0] + B[0]) // 2, (A[1] + B[1]) // 2)
        cx = mid[0] - content_rot.width // 2
        cy = mid[1] - content_rot.height // 2

        img.alpha_composite(ribbon)
        img.alpha_composite(content_rot, (cx, cy))

    def _draw_corner_footer(
        self,
        img: Image.Image,
        draw: ImageDraw.ImageDraw,
        site_text: str,
        place_text: str,
        meetup_id: str | int,
        opt: dict,
    ):
        W, H = img.width, img.height
        pad = opt["safe_margin"]

        # mniejszy trójkąt (~15%)
        base_block_w = int(W * 0.36 * 0.85)
        base_block_h = int(H * 0.26 * 0.85)

        font_site = self._load_font(self.font_normal, opt["footer_font"])
        meet_text = f"Meetup #{meetup_id}"
        link_w = draw.textbbox((0, 0), site_text, font=font_site)[2]

        target_w = int(link_w)

        def fit_meet_font_for_width(target_width: int) -> ImageFont.FreeTypeFont:
            size = int(opt["footer_font"] * 1.05)
            best = self._load_font(self.font_bold, size)
            while size >= 10:
                f = self._load_font(self.font_bold, size)
                w = draw.textbbox((0, 0), meet_text, font=f)[2]
                if w <= target_width:
                    best = f
                    break
                size -= 1
            return best

        font_meet = fit_meet_font_for_width(target_w)

        meet_bbox = draw.textbbox((0, 0), meet_text, font=font_meet)
        site_bbox = draw.textbbox((0, 0), site_text, font=font_site)
        meet_w, meet_h = meet_bbox[2], meet_bbox[3]
        site_w, site_h = site_bbox[2], site_bbox[3]

        text_gap = 8
        text_margin_x = 74
        inner_pad = 30

        req_w = max(meet_w, site_w) + text_margin_x * 2
        req_h = meet_h + text_gap + site_h + inner_pad * 2

        block_w = max(base_block_w, req_w)
        block_h = max(base_block_h, req_h)

        poly = [(0, H), (0, H - block_h), (block_w, H)]
        draw.polygon(poly, fill=self.CG)

        m = block_h / float(block_w) if block_w else 0.0
        total_text_h = meet_h + text_gap + site_h
        bottom_anchor_y = H - inner_pad - total_text_h
        y_top_inside = (H - block_h) + m * text_margin_x + inner_pad
        start_y = int(max(y_top_inside, bottom_anchor_y))
        start_x = text_margin_x

        draw.text((start_x, start_y), meet_text, fill="#FFFFFF", font=font_meet)
        draw.text(
            (start_x, start_y + meet_h + text_gap),
            site_text,
            fill="#E8EEF5",
            font=font_site,
        )

        # środek – lokalizacja (pin + tekst)
        small_font = self._load_font(self.font_normal, max(22, opt["footer_font"]))
        place_w = draw.textbbox((0, 0), place_text, font=small_font)[2]
        pin_sz = min(opt["icon_pin"], 28)
        pin_x = (W // 2) - (place_w // 2) - pin_sz - 10
        pin_y = H - pad - (small_font.size // 2) - 2
        if self.icon_pin.exists():
            try:
                pin = (
                    Image.open(self.icon_pin)
                    .convert("RGBA")
                    .resize((pin_sz, pin_sz), Image.Resampling.LANCZOS)
                )
                img.alpha_composite(pin, (pin_x, pin_y))
            except Exception as e:
                log.warning(f"Cannot load pin icon: {e}")
        self._text_center(
            draw,
            place_text,
            W // 2,
            H - pad - small_font.size // 2 - 2,
            small_font,
            self.SS,
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
        name_f = self._load_font(self.font_bold, 44)
        title_f = self._load_font(self.font_bold, int(26 * 1.2))

        av = self._apply_circular_mask(self._avatar(sp, (size, size)))
        lines = self._wrap_unbounded(draw, title, title_f, int(box_w * 0.9))
        name_h = draw.textbbox((0, 0), sp.name, font=name_f)[3]

        self._overlay(
            img,
            (box_x, box_y, box_x + box_w, box_y + size + 160),
            opt["overlay_opacity"],
        )
        av_x = img.width // 2 - size // 2
        self._paste_with_ring_thin(img, av, (av_x, box_y))

        name_y = box_y + size // 2 - (name_h + 20)
        title_y = box_y + size // 2

        self._text_center(draw, sp.name, img.width // 2, name_y, name_f, self.CT)
        self._text_center_multiline(
            draw, lines, img.width // 2, title_y, title_f, self.SS
        )

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

        col_gap = 72
        col_w = (box_w - col_gap) // 2
        size = opt["duo_avatar"]
        name_f = self._load_font(self.font_bold, 42)
        title_f = self._load_font(self.font_bold, int(24 * 1.2))

        lines1 = self._wrap_unbounded(draw, t1, title_f, col_w - size - 46)
        lines2 = self._wrap_unbounded(draw, t2, title_f, col_w - size - 46)
        name_h1 = draw.textbbox((0, 0), sp1.name, font=name_f)[3]
        name_h2 = draw.textbbox((0, 0), sp2.name, font=name_f)[3]

        self._overlay(
            img,
            (box_x, box_y, box_x + box_w, box_y + size + 220),
            opt["overlay_opacity"],
        )

        left_x = box_x
        av1 = self._apply_circular_mask(self._avatar(sp1, (size, size)))
        self._paste_with_ring_thin(img, av1, (left_x, box_y))
        name1_y = box_y + size // 2 - (name_h1 + 20)
        title1_y = box_y + size // 2
        draw.text((left_x + size + 30, name1_y), sp1.name, fill=self.CT, font=name_f)
        self._text_multiline(
            draw, lines1, left_x + size + 30, title1_y, title_f, self.SS, gap=8
        )

        right_x = box_x + col_w + col_gap
        av2 = self._apply_circular_mask(self._avatar(sp2, (size, size)))
        self._paste_with_ring_thin(img, av2, (right_x + col_w - size, box_y))
        name2_y = box_y + size // 2 - (name_h2 + 20)
        title2_y = box_y + size // 2
        self._text_right(
            draw, sp2.name, right_x + col_w - size - 30, name2_y, name_f, self.CT
        )
        self._text_right_multiline(
            draw, lines2, right_x + col_w - size - 30, title2_y, title_f, self.SS, gap=8
        )

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
        name_f = self._load_font(self.font_bold, 42)
        title_f = self._load_font(self.font_bold, int(24 * 1.2))

        lines1 = self._wrap_unbounded(draw, t1, title_f, int(box_w * 0.9))
        name_h1 = draw.textbbox((0, 0), sp1.name, font=name_f)[3]
        self._overlay(
            img,
            (box_x, base_y, box_x + box_w, base_y + size + 220),
            opt["overlay_opacity"],
        )
        av1 = self._apply_circular_mask(self._avatar(sp1, (size, size)))
        av1_x = box_x + (box_w - size) // 2
        self._paste_with_ring_thin(img, av1, (av1_x, base_y))
        name1_y = base_y + size // 2 - (name_h1 + 20)
        title1_y = base_y + size // 2
        self._text_center(draw, sp1.name, box_x + box_w // 2, name1_y, name_f, self.CT)
        self._text_center_multiline(
            draw, lines1, box_x + box_w // 2, title1_y, title_f, self.SS
        )

        off_y = base_y + size + 240
        lines2 = self._wrap_unbounded(draw, t2, title_f, int(box_w * 0.9))
        name_h2 = draw.textbbox((0, 0), sp2.name, font=name_f)[3]
        self._overlay(
            img,
            (box_x, off_y, box_x + box_w, off_y + size + 220),
            opt["overlay_opacity"],
        )
        av2 = self._apply_circular_mask(self._avatar(sp2, (size, size)))
        av2_x = box_x + (box_w - size) // 2
        self._paste_with_ring_thin(img, av2, (av2_x, off_y))
        name2_y = off_y + size // 2 - (name_h2 + 20)
        title2_y = off_y + size // 2
        self._text_center(draw, sp2.name, box_x + box_w // 2, name2_y, name_f, self.CT)
        self._text_center_multiline(
            draw, lines2, box_x + box_w // 2, title2_y, title_f, self.SS
        )

    # ---------------- canvas/bg ----------------
    def _canvas(self, aspect: str) -> Image.Image:
        if aspect == "4x5":
            return Image.new("RGBA", (1080, 1350), (245, 245, 245, 255))
        if aspect == "1x1":
            return Image.new("RGBA", (1080, 1080), (245, 245, 245, 255))
        return Image.new("RGBA", (1920, 1080), (245, 245, 245, 255))

    def _composite_background(self, canvas: Image.Image, fade: float = 0.05):
        if not self.background_path.exists():
            return
        try:
            bg = Image.open(self.background_path).convert("RGBA")
            ratio = max(canvas.width / bg.width, canvas.height / bg.height)
            new_size = (int(bg.width * ratio), int(bg.height * ratio))
            bg = bg.resize(new_size, Image.Resampling.LANCZOS)
            bg = Image.blend(
                Image.new("RGBA", new_size, (255, 255, 255, 255)), bg, fade
            )
            x = (canvas.width - new_size[0]) // 2
            y = (canvas.height - new_size[1]) // 2
            canvas.alpha_composite(bg, (x, y))
        except Exception as e:
            log.warning(f"Background compose failed: {e}")

    # ---------------- date helpers ----------------
    def _resolve_date_parts(
        self, meetup: Meetup, lang: Language
    ) -> Tuple[str, str, str]:
        dt: Optional[datetime] = None
        for attr in ("starts_at", "start", "datetime", "date"):
            val = getattr(meetup, attr, None)
            if isinstance(val, datetime):
                dt = val
                break
            if isinstance(val, date_cls):
                dt = datetime(val.year, val.month, val.day, 18, 0)
                break

        day_name = ""
        date_label = ""
        time_label = ""

        try:
            lang_code = getattr(lang, "value", getattr(lang, "code", "pl")).lower()
        except Exception:
            lang_code = "pl"

        dni_pl = [
            "PONIEDZIAŁEK",
            "WTOREK",
            "ŚRODA",
            "CZWARTEK",
            "PIĄTEK",
            "SOBOTA",
            "NIEDZIELA",
        ]
        dni_en = [
            "MONDAY",
            "TUESDAY",
            "WEDNESDAY",
            "THURSDAY",
            "FRIDAY",
            "SATURDAY",
            "SUNDAY",
        ]

        if dt:
            date_label = f"{dt.year:04d} {dt.month:02d} {dt.day:02d}"
            time_label = dt.strftime("%H:%M")
            day_name = (
                dni_en[dt.weekday()]
                if lang_code.startswith("en")
                else dni_pl[dt.weekday()]
            )
            return day_name, date_label, time_label

        try:
            fd = meetup.formatted_date(lang).strip()
        except Exception:
            fd = ""

        if " " in fd:
            left, right = fd.rsplit(" ", 1)
            if ":" in right and len(right) in (4, 5):
                date_label = left.replace(".", " ").replace("-", " ").upper()
                time_label = right
            else:
                date_label = fd.replace(".", " ").replace("-", " ").upper()
        else:
            date_label = fd.upper()

        return day_name, date_label, time_label

    # ---------------- text with shadow helpers ----------------
    def _text_center_shadowed(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        cx: int,
        y: int,
        font: ImageFont.FreeTypeFont,
        color: str,
    ):
        img = getattr(draw, "_image", None)
        if img is None:
            core = getattr(draw, "im", None)
            if core is not None and hasattr(core, "size") and hasattr(core, "mode"):
                img = Image.new(core.mode, core.size)
            else:
                raise RuntimeError("Cannot access base Image from ImageDraw")
        if not hasattr(img, "alpha_composite"):
            raise RuntimeError("Expected PIL.Image.Image as drawing surface")

        w = draw.textbbox((0, 0), text, font=font)[2]
        x = cx - w // 2
        self._draw_text_with_shadow(img, text, (x, y), font, color)

    def _text_right_shadowed(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        right_x: int,
        y: int,
        font: ImageFont.FreeTypeFont,
        color: str,
    ):
        img = getattr(draw, "_image", None)
        if img is None:
            core = getattr(draw, "im", None)
            if core is not None and hasattr(core, "size") and hasattr(core, "mode"):
                img = Image.new(core.mode, core.size)
            else:
                raise RuntimeError("Cannot access base Image from ImageDraw")
        if not hasattr(img, "alpha_composite"):
            raise RuntimeError("Expected PIL.Image.Image as drawing surface")

        w = draw.textbbox((0, 0), text, font=font)[2]
        x = right_x - w
        self._draw_text_with_shadow(
            img, text, (x, y), font, color, shadow_color=(255, 255, 255, 110)
        )

    def _draw_text_with_shadow(
        self,
        base_img: Image.Image,
        text: str,
        pos: tuple[int, int],
        font: ImageFont.FreeTypeFont,
        fill: str,
        shadow_color=(0, 0, 0, 90),
        blur: int = 2,
        offset: tuple[int, int] = (0, 2),
    ):
        if not hasattr(base_img, "alpha_composite"):
            raise RuntimeError("Expected PIL.Image.Image as base_img")

        shadow_layer = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
        sd = ImageDraw.Draw(shadow_layer)
        x, y = pos
        sd.text((x + offset[0], y + offset[1]), text, font=font, fill=shadow_color)
        if blur > 0:
            shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(blur))
        base_img.alpha_composite(shadow_layer)

        text_layer = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
        td = ImageDraw.Draw(text_layer)
        td.text((x, y), text, font=font, fill=fill)
        base_img.alpha_composite(text_layer)

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

    def _text_center(self, draw, text, x_center, y, font, color):
        w = draw.textbbox((0, 0), text, font=font)[2]
        draw.text((x_center - w // 2, y), text, fill=color, font=font)

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
            log.warning("Could not load font %s, using default", path)
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
        img = Image.new("RGBA", (diameter, diameter), (255, 255, 255, 255))
        d = ImageDraw.Draw(img)
        ring = max(6, diameter // 24)
        d.ellipse((0, 0, diameter, diameter), fill=(255, 255, 255, 255))
        d.ellipse(
            (ring, ring, diameter - ring, diameter - ring), outline=self.YA, width=ring
        )
        qf = self._load_font(self.font_bold, int(diameter * 0.55))
        d.text(
            self._center_text_in_circle(d, "?", qf, diameter),
            "?",
            fill=self.CT,
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

    def _paste_with_ring_thin(
        self, img: Image.Image, avatar: Image.Image, topleft: tuple[int, int]
    ):
        size = avatar.width
        shadow = Image.new("RGBA", (size + 24, size + 24), (0, 0, 0, 0))
        d = ImageDraw.Draw(shadow)
        d.ellipse((8, 8, size + 16, size + 16), fill=(0, 0, 0, 50))
        shadow = shadow.filter(ImageFilter.GaussianBlur(6))
        img.alpha_composite(shadow, (topleft[0] - 10, topleft[1] - 10))
        ring = Image.new("RGBA", (size + 12, size + 12), (0, 0, 0, 0))
        dr = ImageDraw.Draw(ring)
        dr.ellipse((0, 0, size + 12, size + 12), outline=self.YA, width=3)
        img.alpha_composite(ring, (topleft[0] - 6, topleft[1] - 6))
        img.paste(avatar, topleft, avatar)
