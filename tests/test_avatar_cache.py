"""Cache avatarów musi reagować na nowe zdjęcie wgrane w formularzu zgłoszeniowym."""

import io

import pytest
from PIL import Image

from pyldz import face_centering
from pyldz.image_generator import MeetupImageGenerator
from pyldz.models import File, Speaker


@pytest.fixture
def assets_dir(tmp_path):
    assets = tmp_path / "assets"
    (assets / "images" / "avatars").mkdir(parents=True)
    (assets / "fonts").mkdir(parents=True)
    Image.new("RGBA", (1920, 1080), (255, 255, 255, 255)).save(
        assets / "images" / "infographic_template.png"
    )
    Image.new("L", (300, 300), 255).save(assets / "images" / "avatars" / "mask.png")
    Image.new("RGBA", (300, 300), (128, 128, 128, 255)).save(
        assets / "images" / "avatars" / "tba.png"
    )
    (assets / "fonts" / "OpenSans-Medium.ttf").touch()
    (assets / "fonts" / "OpenSans-Bold.ttf").touch()
    return assets


@pytest.fixture
def centering_calls(monkeypatch):
    calls: list[int] = []

    def centre(img: Image.Image) -> Image.Image:
        calls.append(1)
        return img.crop((0, 0, min(img.size), min(img.size)))

    monkeypatch.setattr(face_centering, "detect_and_center_square", centre)
    return calls


def photo(color: tuple[int, int, int, int]) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGBA", (400, 300), color).save(buffer, format="PNG")
    return buffer.getvalue()


def speaker_with(content: bytes, name: str = "photo.png") -> Speaker:
    return Speaker(
        id="grzegorz-kocjan",
        name="Grzegorz Kocjan",
        bio="",
        avatar=File(name=name, content=content),
        social_links=[],
    )


RED = (200, 10, 10, 255)
BLUE = (10, 10, 200, 255)


def test_new_photo_from_the_form_replaces_the_cached_avatar(
    assets_dir, centering_calls
):
    generator = MeetupImageGenerator(assets_dir)
    generator._avatar(speaker_with(photo(RED)), (100, 100))

    result = generator._avatar(speaker_with(photo(BLUE)), (100, 100))

    assert result.getpixel((50, 50)) == BLUE
    assert len(centering_calls) == 2


def test_unchanged_photo_reuses_the_cache(assets_dir, centering_calls):
    generator = MeetupImageGenerator(assets_dir)
    content = photo(RED)

    generator._avatar(speaker_with(content), (100, 100))
    result = generator._avatar(speaker_with(content), (100, 100))

    assert result.getpixel((50, 50)) == RED
    assert len(centering_calls) == 1


def test_cache_written_before_fingerprints_is_refreshed(assets_dir, centering_calls):
    generator = MeetupImageGenerator(assets_dir)
    # Avatar wgrany przed wprowadzeniem odcisku źródła — bez metadanych.
    Image.new("RGBA", (300, 300), RED).save(generator.cache_dir / "grzegorz-kocjan.png")

    result = generator._avatar(speaker_with(photo(BLUE)), (100, 100))

    assert result.getpixel((50, 50)) == BLUE


def test_submission_without_a_photo_keeps_the_avatar_from_the_repo(
    assets_dir, centering_calls
):
    generator = MeetupImageGenerator(assets_dir)
    generator._avatar(speaker_with(photo(RED)), (100, 100))

    result = generator._avatar(
        speaker_with(File.no_photo().content, name="no_photo.png"), (100, 100)
    )

    assert result.getpixel((50, 50)) == RED
    assert len(centering_calls) == 1
