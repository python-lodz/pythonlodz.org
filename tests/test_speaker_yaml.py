from pathlib import Path

from pyldz.models import File, Speaker
from pyldz.speaker_yaml import build_speaker_yaml_content, write_speaker_yaml


def make_speaker(**kwargs) -> Speaker:
    return Speaker(
        id="jarek-smietanka",
        name="Jarek Smietanka",
        bio="Bio",
        avatar=File(name="avatar.jpg", content=b"jpg-bytes"),
        social_links=[],
        **kwargs,
    )


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
