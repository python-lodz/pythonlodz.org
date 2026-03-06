import datetime
import io

import pytest
from PIL import Image

from pyldz.image_generator import MeetupImageGenerator
from pyldz.models import File, Language, Meetup, MultiLanguage, Speaker, Talk


def _prepare_assets_dir(tmp_path):
    assets_dir = tmp_path / "assets"
    (assets_dir / "images" / "avatars").mkdir(parents=True)
    (assets_dir / "images").mkdir(exist_ok=True)
    (assets_dir / "fonts").mkdir(exist_ok=True)

    Image.new("RGBA", (1920, 1080), (255, 255, 255, 255)).save(
        assets_dir / "images" / "infographic_template.png"
    )
    Image.new("L", (300, 300), 255).save(assets_dir / "images" / "avatars" / "mask.png")
    Image.new("RGBA", (300, 300), (128, 128, 128, 255)).save(
        assets_dir / "images" / "avatars" / "tba.png"
    )
    (assets_dir / "fonts" / "OpenSans-Medium.ttf").touch()
    (assets_dir / "fonts" / "OpenSans-Bold.ttf").touch()
    return assets_dir


def _make_avatar(color: tuple[int, int, int, int]) -> bytes:
    img = Image.new("RGBA", (300, 300), color)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


def _bbox_for_color(
    img: Image.Image, rgb: tuple[int, int, int], tolerance: int = 20
) -> tuple[int, int, int, int]:
    points = []
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = img.getpixel((x, y))
            if (
                a > 0
                and abs(r - rgb[0]) <= tolerance
                and abs(g - rgb[1]) <= tolerance
                and abs(b - rgb[2]) <= tolerance
            ):
                points.append((x, y))

    assert points, f"No pixels found for color {rgb}"

    xs = [x for x, _ in points]
    ys = [y for _, y in points]
    return min(xs), min(ys), max(xs), max(ys)


@pytest.mark.parametrize("aspect_ratio", ["4x5", "1x1"])
def test_duo_square_variants_place_speakers_side_by_side(
    tmp_path, monkeypatch, aspect_ratio
):
    assets_dir = _prepare_assets_dir(tmp_path)
    generator = MeetupImageGenerator(assets_dir)

    meetup = Meetup(
        meetup_id="63",
        title="Meetup #63",
        date=datetime.date(2024, 6, 27),
        time="18:00",
        location=MultiLanguage(pl="Test Venue", en="Test Venue"),
        language=Language.PL,
        talks=[
            Talk(
                speaker_id="speaker-a",
                title="First Talk Title",
                description="",
                language=Language.PL,
                title_en="First Talk Title",
            ),
            Talk(
                speaker_id="speaker-b",
                title="Second Talk Title",
                description="",
                language=Language.EN,
                title_en="Second Talk Title",
            ),
        ],
        sponsors=[],
    )
    speakers = [
        Speaker(
            id="speaker-a",
            name="Alice Speaker",
            bio="",
            avatar=File(name="speaker-a.png", content=_make_avatar((255, 0, 0, 255))),
            social_links=[],
        ),
        Speaker(
            id="speaker-b",
            name="Bob Speaker",
            bio="",
            avatar=File(name="speaker-b.png", content=_make_avatar((0, 0, 255, 255))),
            social_links=[],
        ),
    ]

    from pyldz import face_centering

    monkeypatch.setattr(face_centering, "detect_and_center_square", lambda img: img)

    output_path = tmp_path / f"featured-{aspect_ratio}.png"
    generator.generate_featured_image(
        meetup,
        speakers,
        output_path,
        Language.PL,
        aspect_ratio=aspect_ratio,
    )

    rendered = Image.open(output_path).convert("RGBA")
    red = _bbox_for_color(rendered, (255, 0, 0))
    blue = _bbox_for_color(rendered, (0, 0, 255))

    red_center_x = (red[0] + red[2]) / 2
    blue_center_x = (blue[0] + blue[2]) / 2
    red_center_y = (red[1] + red[3]) / 2
    blue_center_y = (blue[1] + blue[3]) / 2

    assert red_center_x < rendered.width / 2
    assert blue_center_x > rendered.width / 2
    assert abs(red_center_y - blue_center_y) <= 60
