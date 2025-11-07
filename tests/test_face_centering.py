import io

import pytest
from PIL import Image

from pyldz.image_generator import MeetupImageGenerator
from pyldz.models import File, Speaker


@pytest.fixture
def sample_rect_image() -> Image.Image:
    # Create a simple non-square image (200x100)
    img = Image.new("RGB", (200, 100), (120, 180, 200))
    return img


def _fake_face(area: dict[str, int]) -> dict:
    # Minimal structure similar to DeepFace.extract_faces() output
    return {"facial_area": area}


def test_detect_and_center_square_single_face(monkeypatch, sample_rect_image):
    from pyldz import face_centering

    # Patch internal extractor to return a single face in the center
    monkeypatch.setattr(
        face_centering,
        "_deepface_extract_faces",
        lambda img: [_fake_face({"x": 80, "y": 20, "w": 40, "h": 60})],
    )

    squared = face_centering.detect_and_center_square(sample_rect_image)

    assert squared.width == squared.height
    # Ensure we didn't upscale beyond image bounds
    assert squared.width <= max(sample_rect_image.size)


def test_detect_and_center_square_no_face(monkeypatch, sample_rect_image):
    from pyldz import face_centering

    monkeypatch.setattr(face_centering, "_deepface_extract_faces", lambda img: [])

    with pytest.raises(face_centering.FaceDetectionError, match="No face detected"):
        face_centering.detect_and_center_square(sample_rect_image)


def test_detect_and_center_square_multiple_faces(monkeypatch, sample_rect_image):
    from pyldz import face_centering

    monkeypatch.setattr(
        face_centering,
        "_deepface_extract_faces",
        lambda img: [
            _fake_face({"x": 10, "y": 10, "w": 20, "h": 20}),
            _fake_face({"x": 150, "y": 40, "w": 20, "h": 20}),
        ],
    )

    with pytest.raises(face_centering.FaceDetectionError, match="More than one face"):
        face_centering.detect_and_center_square(sample_rect_image)


class TestImageGeneratorFaceCentering:
    def test_get_speaker_avatar_uses_centered_square_and_caching(
        self, tmp_path, monkeypatch
    ):
        # Prepare assets dir with minimal structure
        assets_dir = tmp_path / "assets"
        (assets_dir / "images" / "avatars").mkdir(parents=True)
        (assets_dir / "images").mkdir(exist_ok=True)
        (assets_dir / "fonts").mkdir(exist_ok=True)

        # Minimal templates and fonts required by generator
        Image.new("RGBA", (1920, 1080), (255, 255, 255, 255)).save(
            assets_dir / "images" / "infographic_template.png"
        )
        Image.new("RGBA", (1920, 1080), (255, 255, 255, 255)).save(
            assets_dir / "images" / "infographic_template_duo.png"
        )
        (assets_dir / "images" / "avatars" / "mask.png").touch()
        (assets_dir / "images" / "avatars" / "tba.png").touch()
        (assets_dir / "fonts" / "OpenSans-Medium.ttf").touch()
        (assets_dir / "fonts" / "OpenSans-Bold.ttf").touch()

        generator = MeetupImageGenerator(assets_dir)

        # Create non-square avatar bytes
        avatar_img = Image.new("RGBA", (300, 150), (10, 20, 30, 255))
        buf = io.BytesIO()
        avatar_img.save(buf, format="PNG")
        avatar_bytes = buf.getvalue()

        speaker = Speaker(
            id="speaker-60",
            name="Speaker 60",
            bio="",
            avatar=File(name="avatar.png", content=avatar_bytes),
            social_links=[],
        )

        # Patch face centering to return a square image deterministically
        from pyldz import face_centering

        def fake_center(img: Image.Image) -> Image.Image:
            # Return a 150x150 square crop
            return Image.new("RGBA", (150, 150), (10, 20, 30, 255))

        monkeypatch.setattr(face_centering, "detect_and_center_square", fake_center)

        result = generator._get_speaker_avatar(speaker, (300, 300))

        assert result is not None
        assert result.size == (300, 300)

        # Processed avatar should exist with new naming
        processed_cache = generator.cache_dir / f"{speaker.id}.png"
        assert processed_cache.exists()

    def test_get_speaker_avatar_no_face_detected_uses_fallback(
        self, tmp_path, monkeypatch
    ):
        """Test that when face detection fails, avatar is used without face centering."""
        # Prepare assets dir with minimal structure
        assets_dir = tmp_path / "assets"
        (assets_dir / "images" / "avatars").mkdir(parents=True)
        (assets_dir / "images").mkdir(exist_ok=True)
        (assets_dir / "fonts").mkdir(exist_ok=True)

        # Minimal templates and fonts required by generator
        Image.new("RGBA", (1920, 1080), (255, 255, 255, 255)).save(
            assets_dir / "images" / "infographic_template.png"
        )
        Image.new("RGBA", (1920, 1080), (255, 255, 255, 255)).save(
            assets_dir / "images" / "infographic_template_duo.png"
        )
        (assets_dir / "images" / "avatars" / "mask.png").touch()
        (assets_dir / "images" / "avatars" / "tba.png").touch()
        (assets_dir / "fonts" / "OpenSans-Medium.ttf").touch()
        (assets_dir / "fonts" / "OpenSans-Bold.ttf").touch()

        generator = MeetupImageGenerator(assets_dir)

        # Create avatar bytes (simulating no_photo.png with no face)
        avatar_img = Image.new("RGBA", (300, 300), (255, 200, 0, 255))
        buf = io.BytesIO()
        avatar_img.save(buf, format="PNG")
        avatar_bytes = buf.getvalue()

        speaker = Speaker(
            id="speaker-no-face",
            name="Speaker No Face",
            bio="",
            avatar=File(name="no_photo.png", content=avatar_bytes),
            social_links=[],
        )

        # Patch face centering to raise FaceDetectionError (simulating no face detected)
        from pyldz import face_centering

        def fake_center_no_face(img: Image.Image) -> Image.Image:
            raise face_centering.FaceDetectionError("No face detected")

        monkeypatch.setattr(
            face_centering, "detect_and_center_square", fake_center_no_face
        )

        # Should not raise, should return the avatar without face centering
        result = generator._get_speaker_avatar(speaker, (300, 300))

        assert result is not None
        assert result.size == (300, 300)

        # Processed avatar should exist
        processed_cache = generator.cache_dir / f"{speaker.id}.png"
        assert processed_cache.exists()
