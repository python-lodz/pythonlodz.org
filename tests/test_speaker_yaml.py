from pyldz.models import File, Speaker
from pyldz.speaker_yaml import write_speaker_yaml


def test_write_speaker_yaml_uses_processed_png_avatar_path(tmp_path):
    page_dir = tmp_path / "page"
    speaker = Speaker(
        id="jarek-smietanka",
        name="Jarek Smietanka",
        bio="Bio",
        avatar=File(name="avatar.jpg", content=b"jpg-bytes"),
        social_links=[],
    )

    yaml_path = write_speaker_yaml(speaker, page_dir)

    assert yaml_path.read_text(encoding="utf-8").splitlines()[1] == (
        'avatar: "images/avatars/jarek-smietanka.png"'
    )
