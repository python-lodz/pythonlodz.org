import datetime
from unittest.mock import patch

import pytest
from PIL import Image

from pyldz.image_generator import ImageGenerationError, MeetupImageGenerator
from pyldz.models import File, Language, Meetup, MultiLanguage, Speaker, Talk


@pytest.fixture
def temp_assets_dir(tmp_path):
    assets_dir = tmp_path / "assets"
    assets_dir.mkdir()

    # Create directories
    (assets_dir / "images").mkdir()
    (assets_dir / "images" / "avatars").mkdir()
    (assets_dir / "fonts").mkdir()

    # Create test template image
    template = Image.new("RGBA", (1920, 1080), (255, 255, 255, 255))
    template.save(assets_dir / "images" / "infographic_template.png")

    # Create test mask
    mask = Image.new("L", (300, 300), 255)
    mask.save(assets_dir / "images" / "avatars" / "mask.png")

    # Create TBA avatar
    tba = Image.new("RGBA", (300, 300), (128, 128, 128, 255))
    tba.save(assets_dir / "images" / "avatars" / "tba.png")

    # Create test font files (empty files for testing)
    (assets_dir / "fonts" / "OpenSans-Medium.ttf").touch()
    (assets_dir / "fonts" / "OpenSans-Bold.ttf").touch()

    return assets_dir


@pytest.fixture
def sample_meetup():
    return Meetup(
        meetup_id="42",
        title="Meetup #42",
        date=datetime.date(2024, 6, 27),
        time="18:00",
        location=MultiLanguage(
            pl="Test Venue, Test Street 123", en="Test Venue, Test Street 123"
        ),
        language=Language.PL,
        talks=[
            Talk(
                speaker_id="john-doe",
                title="Introduction to Clean Architecture",
                description="Learn clean architecture principles.",
                language=Language.EN,
                title_en="Introduction to Clean Architecture",
            )
        ],
        sponsors=["sponsor1"],
    )


@pytest.fixture
def sample_duo_meetup():
    return Meetup(
        meetup_id="43",
        title="Meetup #43",
        date=datetime.date(2024, 7, 25),
        time="18:00",
        location=MultiLanguage(
            pl="Test Venue, Test Street 123", en="Test Venue, Test Street 123"
        ),
        language=Language.PL,
        talks=[
            Talk(
                speaker_id="john-doe",
                title="Introduction to Clean Architecture",
                description="Learn clean architecture principles.",
                language=Language.EN,
                title_en="Introduction to Clean Architecture",
            ),
            Talk(
                speaker_id="jane-smith",
                title="Advanced Python Patterns",
                description="Deep dive into Python patterns.",
                language=Language.PL,
                title_en="Advanced Python Patterns",
            ),
        ],
        sponsors=["sponsor1"],
    )


@pytest.fixture
def sample_speaker():
    return Speaker(
        id="john-doe",
        name="John Doe",
        bio="A developer",
        avatar=File(name="avatar.png", content=b""),
        social_links=[],
    )


@pytest.fixture
def sample_speakers():
    return [
        Speaker(
            id="john-doe",
            name="John Doe",
            bio="A developer",
            avatar=File(name="avatar1.png", content=b""),
            social_links=[],
        ),
        Speaker(
            id="jane-smith",
            name="Jane Smith",
            bio="Another developer",
            avatar=File(name="avatar2.png", content=b""),
            social_links=[],
        ),
    ]


def test_init(temp_assets_dir, tmp_path):
    cache_dir = tmp_path / "cache"
    generator = MeetupImageGenerator(temp_assets_dir, cache_dir)

    assert generator.assets_dir == temp_assets_dir
    assert generator.cache_dir == cache_dir
    assert cache_dir.exists()


def test_init_with_default_cache(temp_assets_dir):
    generator = MeetupImageGenerator(temp_assets_dir)

    expected_cache = temp_assets_dir / "images" / "avatars"
    assert generator.cache_dir == expected_cache
    assert expected_cache.exists()


def test_generate_featured_image_no_talks(temp_assets_dir, tmp_path):
    generator = MeetupImageGenerator(temp_assets_dir)

    meetup = Meetup(
        meetup_id="44",
        title="Meetup #44",
        date=datetime.date(2024, 8, 29),
        time="18:00",
        location=MultiLanguage(pl="Test Venue PL", en="Test Venue EN"),
        talks=[],
        sponsors=[],
        language=Language.PL,
    )

    output_path = tmp_path / "featured.png"

    # Use the default font loading which will fall back to default font
    result = generator.generate_featured_image(meetup, [], output_path)

    assert result == output_path
    assert output_path.exists()


def test_generate_featured_image_solo(
    temp_assets_dir, tmp_path, sample_meetup, sample_speaker
):
    generator = MeetupImageGenerator(temp_assets_dir)
    output_path = tmp_path / "featured.png"

    with patch.object(generator, "_get_speaker_avatar") as mock_get_avatar:
        mock_get_avatar.return_value = Image.new("RGBA", (300, 300), (255, 0, 0, 255))

        result = generator.generate_featured_image(
            sample_meetup, [sample_speaker], output_path
        )

    assert result == output_path
    assert output_path.exists()


def test_generate_featured_image_duo(
    temp_assets_dir, tmp_path, sample_duo_meetup, sample_speakers
):
    generator = MeetupImageGenerator(temp_assets_dir)
    output_path = tmp_path / "featured.png"

    with patch.object(generator, "_get_speaker_avatar") as mock_get_avatar:
        mock_get_avatar.return_value = Image.new("RGBA", (240, 240), (255, 0, 0, 255))

        result = generator.generate_featured_image(
            sample_duo_meetup, sample_speakers, output_path
        )

    assert result == output_path
    assert output_path.exists()


def test_find_speaker_by_id(temp_assets_dir, sample_speakers):
    """Test finding speaker by ID."""
    generator = MeetupImageGenerator(temp_assets_dir)

    speaker = generator._find_speaker_by_id(sample_speakers, "john-doe")
    assert speaker is not None
    assert speaker.name == "John Doe"

    speaker = generator._find_speaker_by_id(sample_speakers, "nonexistent")
    assert speaker is None


def test_get_speaker_avatar_download(temp_assets_dir):
    generator = MeetupImageGenerator(temp_assets_dir)

    # Create a test image in memory
    test_image = Image.new("RGB", (100, 100), (255, 0, 0))
    from io import BytesIO

    img_bytes = BytesIO()
    test_image.save(img_bytes, format="PNG")
    img_bytes.seek(0)

    speaker = Speaker(
        id="john-doe",
        name="John Doe",
        bio="A developer",
        avatar=File(name="avatar.png", content=img_bytes.getvalue()),
        social_links=[],
    )

    avatar = generator._get_speaker_avatar(speaker, (50, 50))

    assert avatar is not None
    assert avatar.size == (50, 50)

    # Check that avatar was cached
    cache_file = generator.cache_dir / f"{speaker.id}.png"
    assert cache_file.exists()


def test_get_speaker_avatar_from_cache(temp_assets_dir, sample_speaker):
    generator = MeetupImageGenerator(temp_assets_dir)

    # Create cached avatar
    cache_file = generator.cache_dir / f"{sample_speaker.id}.png"
    test_image = Image.new("RGBA", (100, 100), (0, 255, 0, 255))
    test_image.save(cache_file)

    avatar = generator._get_speaker_avatar(sample_speaker, (50, 50))

    assert avatar is not None
    assert avatar.size == (50, 50)


def test_apply_circular_mask(temp_assets_dir):
    generator = MeetupImageGenerator(temp_assets_dir)

    test_image = Image.new("RGBA", (100, 100), (255, 0, 0, 255))
    masked = generator._apply_circular_mask(test_image)

    assert masked.size == test_image.size
    assert masked.mode == "RGBA"


def test_apply_circular_mask_missing_mask_file(temp_assets_dir):
    (temp_assets_dir / "images" / "avatars" / "mask.png").unlink()

    generator = MeetupImageGenerator(temp_assets_dir)

    test_image = Image.new("RGBA", (100, 100), (255, 0, 0, 255))
    masked = generator._apply_circular_mask(test_image)

    assert masked.size == test_image.size
    assert masked.mode == "RGBA"


def test_create_circular_mask(temp_assets_dir):
    generator = MeetupImageGenerator(temp_assets_dir)

    test_image = Image.new("RGBA", (100, 100), (255, 0, 0, 255))
    masked = generator._create_circular_mask(test_image)

    assert masked.size == test_image.size
    assert masked.mode == "RGBA"


def test_generate_featured_image_polish_language(temp_assets_dir, sample_meetup):
    """Test generating featured image in Polish language."""
    generator = MeetupImageGenerator(temp_assets_dir)
    output_path = temp_assets_dir / "featured-pl.png"

    # Generate image in Polish
    result = generator.generate_featured_image(
        sample_meetup, [], output_path, Language.PL
    )

    assert result == output_path
    assert output_path.exists()
    assert output_path.suffix == ".png"


def test_generate_featured_image_english_language(temp_assets_dir, sample_meetup):
    """Test generating featured image in English language."""
    generator = MeetupImageGenerator(temp_assets_dir)
    output_path = temp_assets_dir / "featured-en.png"

    # Generate image in English
    result = generator.generate_featured_image(
        sample_meetup, [], output_path, Language.EN
    )

    assert result == output_path
    assert output_path.exists()
    assert output_path.suffix == ".png"


def test_generate_featured_image_both_languages(temp_assets_dir, sample_meetup):
    """Test generating featured images in both languages."""
    generator = MeetupImageGenerator(temp_assets_dir)
    pl_path = temp_assets_dir / "featured-pl.png"
    en_path = temp_assets_dir / "featured-en.png"

    # Generate both versions
    pl_result = generator.generate_featured_image(
        sample_meetup, [], pl_path, Language.PL
    )
    en_result = generator.generate_featured_image(
        sample_meetup, [], en_path, Language.EN
    )

    assert pl_result.exists()
    assert en_result.exists()

    # Both should be valid PNG files
    pl_image = Image.open(pl_result)
    en_image = Image.open(en_result)

    assert pl_image.format == "PNG"
    assert en_image.format == "PNG"
    assert pl_image.size == en_image.size
