import io

from PIL import Image, ImageDraw

from pyldz.image_generator import MeetupImageGenerator
from pyldz.models import File, Speaker


def _bbox_of_dark_pixels(img: Image.Image) -> tuple[int, int, int, int]:
    gray = img.convert("L")
    dark_pixels = [
        (x, y)
        for y in range(gray.height)
        for x in range(gray.width)
        if gray.getpixel((x, y)) < 32
    ]
    xs = [x for x, _ in dark_pixels]
    ys = [y for _, y in dark_pixels]
    return min(xs), min(ys), max(xs), max(ys)


def test_avatar_fallback_resize_preserves_aspect_ratio(tmp_path, monkeypatch):
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

    original = Image.new("RGBA", (100, 200), (255, 255, 255, 255))
    ImageDraw.Draw(original).ellipse((20, 70, 80, 130), fill=(0, 0, 0, 255))
    buffer = io.BytesIO()
    original.save(buffer, format="PNG")

    speaker = Speaker(
        id="portrait-speaker",
        name="Portrait Speaker",
        bio="",
        avatar=File(name="portrait.png", content=buffer.getvalue()),
        social_links=[],
    )

    from pyldz import face_centering

    def no_face(_: Image.Image) -> Image.Image:
        raise face_centering.FaceDetectionError("No face detected")

    monkeypatch.setattr(face_centering, "detect_and_center_square", no_face)

    result = MeetupImageGenerator(assets_dir)._avatar(speaker, (200, 200))

    left, top, right, bottom = _bbox_of_dark_pixels(result)
    width = right - left
    height = bottom - top

    assert result.size == (200, 200)
    assert 0.9 <= (width / height) <= 1.1
