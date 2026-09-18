from pathlib import Path

from pyldz.models import File, SocialLink, Speaker
from pyldz.speaker_yaml import build_speaker_yaml_content, write_speaker_yaml


def make_speaker(**overrides) -> Speaker:
    defaults = {
        "id": "jarek-smietanka",
        "name": "Jarek Smietanka",
        "bio": "Bio",
        "avatar": File(name="avatar.jpg", content=b"jpg-bytes"),
        "social_links": [],
    }
    return Speaker(**{**defaults, **overrides})


def test_write_speaker_yaml_uses_processed_png_avatar_path(tmp_path):
    page_dir = tmp_path / "page"
    speaker = make_speaker()

    yaml_path = write_speaker_yaml(speaker, page_dir)

    assert yaml_path.read_text(encoding="utf-8").splitlines()[1] == (
        'avatar: "images/avatars/jarek-smietanka.png"'
    )


def test_speaker_yaml_includes_instagram_handle_when_set():
    speaker = make_speaker(instagram="pythonlodz")
    content = build_speaker_yaml_content(speaker, Path("images/avatars/x.png"))
    assert 'instagram: "pythonlodz"' in content


def test_speaker_yaml_omits_instagram_when_unset():
    speaker = make_speaker()
    content = build_speaker_yaml_content(speaker, Path("images/avatars/x.png"))
    assert "instagram" not in content


def _existing_profile(page_dir: Path, speaker_id: str, content: str) -> Path:
    speakers_dir = page_dir / "data" / "speakers"
    speakers_dir.mkdir(parents=True, exist_ok=True)
    path = speakers_dir / f"{speaker_id}.yaml"
    path.write_text(content, encoding="utf-8")
    return path


def test_regeneration_keeps_links_absent_from_the_new_submission(tmp_path):
    # Zgłoszenie z formularza zna tylko część linków — reszta jest dopisywana
    # ręcznie w repo i nie może zniknąć przy dodaniu kolejnego spotkania.
    page_dir = tmp_path / "page"
    _existing_profile(
        page_dir,
        "jarek-smietanka",
        'name: "Jarek Smietanka"\n'
        'avatar: "images/avatars/jarek-smietanka.png"\n'
        'bio: "Stare bio"\n'
        'instagram: "jarek"\n'
        "social:\n"
        "  - youtube: https://www.youtube.com/@jarek\n"
        "  - link: https://jarek.dev/\n",
    )
    speaker = make_speaker(
        bio="Nowe bio",
        social_links=[
            SocialLink(platform="linkedin", url="https://linkedin.com/in/jarek"),
        ],
    )

    content = write_speaker_yaml(speaker, page_dir).read_text(encoding="utf-8")

    assert "https://www.youtube.com/@jarek" in content
    assert "https://jarek.dev/" in content
    assert "https://linkedin.com/in/jarek" in content
    assert 'instagram: "jarek"' in content
    assert 'bio: "Nowe bio"' in content


def test_regeneration_updates_url_of_a_known_platform(tmp_path):
    page_dir = tmp_path / "page"
    _existing_profile(
        page_dir,
        "jarek-smietanka",
        'name: "Jarek Smietanka"\n'
        'avatar: "images/avatars/jarek-smietanka.png"\n'
        'bio: "Bio"\n'
        "social:\n"
        "  - linkedin: https://linkedin.com/in/old\n",
    )
    speaker = make_speaker(
        social_links=[
            SocialLink(platform="linkedin", url="https://linkedin.com/in/new"),
        ],
    )

    content = write_speaker_yaml(speaker, page_dir).read_text(encoding="utf-8")

    assert "https://linkedin.com/in/new" in content
    assert "old" not in content


def test_regeneration_does_not_blank_bio_when_submission_is_empty(tmp_path):
    page_dir = tmp_path / "page"
    _existing_profile(
        page_dir,
        "jarek-smietanka",
        'name: "Jarek Smietanka"\n'
        'avatar: "images/avatars/jarek-smietanka.png"\n'
        'bio: "Stare bio"\n'
        "social: []\n",
    )
    speaker = make_speaker(bio="")

    content = write_speaker_yaml(speaker, page_dir).read_text(encoding="utf-8")

    assert 'bio: "Stare bio"' in content


def test_first_write_keeps_todays_layout(tmp_path):
    page_dir = tmp_path / "page"
    speaker = make_speaker(
        social_links=[SocialLink(platform="website", url="https://jarek.dev/")]
    )

    content = write_speaker_yaml(speaker, page_dir).read_text(encoding="utf-8")

    assert content == (
        'name: "Jarek Smietanka"\n'
        'avatar: "images/avatars/jarek-smietanka.png"\n'
        'bio: "Bio"\n'
        "social:\n"
        "  - link: https://jarek.dev/\n"
    )
