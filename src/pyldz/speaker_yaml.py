from pathlib import Path
from typing import Iterable

from ruamel.yaml import YAML

from pyldz.models import Speaker

# Platforms a speaker has exactly one of — a new submission replaces the old URL.
# Everything else (generic `link`) accumulates.
_SINGLE_ENTRY_PLATFORMS = frozenset({"facebook", "linkedin", "youtube"})


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


def _existing_social_pairs(existing: dict | None) -> list[list[str]]:
    pairs: list[list[str]] = []
    for entry in (existing or {}).get("social") or []:
        if isinstance(entry, dict):
            pairs.extend([key, str(url)] for key, url in entry.items())
    return pairs


def _merge_social_pairs(speaker: Speaker, existing: dict | None) -> list[list[str]]:
    """Keep links already curated in the repo, apply what the submission brings."""
    pairs = _existing_social_pairs(existing)

    for link in speaker.social_links:
        key = _map_platform(link.platform)
        url = str(link.url)

        if [key, url] in pairs:
            continue

        known = next((pair for pair in pairs if pair[0] == key), None)
        if known is not None and key in _SINGLE_ENTRY_PLATFORMS:
            known[1] = url
        else:
            pairs.append([key, url])

    return pairs


def _build_social_section(pairs: list[list[str]]) -> str:
    if not pairs:
        return "social: []"

    lines = ["social:"]
    lines.extend(f"  - {key}: {url}" for key, url in pairs)
    return "\n".join(lines)


def build_speaker_yaml_content(
    speaker: Speaker,
    avatar_rel_path: Path,
    existing: dict | None = None,
) -> str:
    """Build YAML content for a Speaker matching Hugo's data schema.

    avatar_rel_path must be the path relative to the Hugo `assets` root used by data files,
    e.g. Path("images/avatars/jane-doe.png").

    `existing` is the profile already stored in the repo, if any. A form submission only
    ever carries part of a speaker's data, so anything it does not bring is preserved.
    """
    existing = existing or {}

    bio = speaker.bio.strip() or str(existing.get("bio", ""))
    instagram = speaker.instagram or existing.get("instagram")

    parts = [
        f"name: {_escape_yaml_string(speaker.name)}",
        f"avatar: {_escape_yaml_string(str(avatar_rel_path))}",
        f"bio: {_escape_yaml_string(bio)}",
    ]
    if instagram:
        parts.append(f"instagram: {_escape_yaml_string(str(instagram))}")
    parts.append(_build_social_section(_merge_social_pairs(speaker, existing)))

    handled = {"name", "avatar", "bio", "instagram", "social"}
    for key, value in existing.items():
        if key not in handled:
            parts.append(f"{key}: {_escape_yaml_string(str(value))}")

    parts.append("")  # trailing newline
    return "\n".join(parts)


def _read_existing_profile(yaml_path: Path) -> dict | None:
    if not yaml_path.exists():
        return None
    data = YAML().load(yaml_path.read_text(encoding="utf-8"))
    return dict(data) if data else None


def write_speaker_yaml(speaker: Speaker, page_dir: Path = Path("page")) -> Path:
    """Write the speaker's Hugo data file, merged with the profile already in the repo.

    - Avatar: page/assets/images/avatars/{speaker.id}.png (persisted by MeetupImageGenerator)
    - YAML:   page/data/speakers/{speaker.id}.yaml

    Returns the path to the written YAML file.
    """
    data_speakers_dir = page_dir / "data" / "speakers"
    data_speakers_dir.mkdir(parents=True, exist_ok=True)

    yaml_path = data_speakers_dir / f"{speaker.id}.yaml"

    # Hugo data files point at the processed avatar asset produced by
    # MeetupImageGenerator, which always persists speaker avatars as PNG.
    avatar_rel = Path("images") / "avatars" / f"{speaker.id}.png"
    yaml_content = build_speaker_yaml_content(
        speaker, avatar_rel, _read_existing_profile(yaml_path)
    )

    yaml_path.write_text(yaml_content, encoding="utf-8")
    return yaml_path


def write_speakers_yaml(
    speakers: Iterable[Speaker], page_dir: Path = Path("page")
) -> list[Path]:
    written: list[Path] = []
    for speaker in speakers:
        written.append(write_speaker_yaml(speaker, page_dir))
    return written
