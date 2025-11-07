from pathlib import Path
from typing import Iterable

from pyldz.models import Speaker


def _escape_yaml_string(value: str) -> str:
    """Escape a value for use in a double-quoted YAML string.

    Keep output as a single line to match existing speaker files.
    """
    single_line = " ".join(value.splitlines()).strip()
    # Escape backslashes first, then quotes
    escaped = single_line.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _map_platform(platform: str) -> str:
    """Map internal SocialLink.platform to YAML key.

    Existing YAML uses `link` for generic websites.
    """
    if platform.lower() == "website":
        return "link"
    return platform.lower()


def _build_social_section(speaker: Speaker) -> str:
    if not speaker.social_links:
        return "social: []\n"

    lines: list[str] = ["social:"]
    for link in speaker.social_links:
        key = _map_platform(link.platform)
        lines.append(f"  - {key}: {link.url}")
    return "\n".join(lines) + "\n"


def build_speaker_yaml_content(speaker: Speaker, avatar_rel_path: Path) -> str:
    """Build YAML content for a Speaker matching Hugo's data schema.

    avatar_rel_path must be the path relative to the Hugo `assets` root used by data files,
    e.g. Path("images/avatars/jane-doe.png").
    """
    parts: list[str] = []
    parts.append(f"name: {_escape_yaml_string(speaker.name)}")
    parts.append(f"avatar: {_escape_yaml_string(str(avatar_rel_path))}")
    parts.append(f"bio: {_escape_yaml_string(speaker.bio)}")
    parts.append(_build_social_section(speaker).rstrip())
    parts.append("")  # trailing newline
    return "\n".join(parts)


def write_speaker_yaml(speaker: Speaker, page_dir: Path = Path("page")) -> Path:
    """Write speaker avatar and YAML file under the Hugo page directory.

    - Avatar: page/assets/images/avatars/{speaker.id}{ext}
    - YAML:   page/data/speakers/{speaker.id}.yaml

    Returns the path to the written YAML file.
    """
    data_speakers_dir = page_dir / "data" / "speakers"
    data_speakers_dir.mkdir(parents=True, exist_ok=True)

    ext = speaker.avatar.extension.lower() if speaker.avatar.extension else ""
    avatar_filename = f"{speaker.id}{ext}"

    # TODO: should I generate images here or only when meetup page is generated?
    # avatars_dir = page_dir / "assets" / "images" / "avatars"
    # avatars_dir.mkdir(parents=True, exist_ok=True)
    # avatar_path = avatars_dir / avatar_filename
    # avatar_path.write_bytes(speaker.avatar.content)

    # Build YAML content and write
    avatar_rel = Path("images") / "avatars" / avatar_filename
    yaml_content = build_speaker_yaml_content(speaker, avatar_rel)

    yaml_path = data_speakers_dir / f"{speaker.id}.yaml"
    yaml_path.write_text(yaml_content, encoding="utf-8")
    return yaml_path


def write_speakers_yaml(
    speakers: Iterable[Speaker], page_dir: Path = Path("page")
) -> list[Path]:
    written: list[Path] = []
    for speaker in speakers:
        written.append(write_speaker_yaml(speaker, page_dir))
    return written
