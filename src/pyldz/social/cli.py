"""Typer sub-app: `pyldz social ...` — publishing engine CLI (gk-sm)."""

import datetime
import logging
from pathlib import Path

import typer
from typing_extensions import Annotated
from zoneinfo import ZoneInfo

from pyldz.logging_config import setup_logging
from pyldz.social.adapters.discord import DiscordAdapter
from pyldz.social.adapters.facebook import FacebookAdapter
from pyldz.social.adapters.instagram import InstagramAdapter
from pyldz.social.config import SocialSettings
from pyldz.social.models import Channel
from pyldz.social.publisher import Publisher
from pyldz.social.repository import SocialRepository
from pyldz.social.youtube import YouTubeLive

log = logging.getLogger(__name__)

social_app = typer.Typer(name="social", help="Social media publishing (gk-sm)")

WARSAW = ZoneInfo("Europe/Warsaw")

MeetupOption = Annotated[
    str | None, typer.Option("--meetup", "-m", help="Meetup ID (default: all)")
]
ContentDirOption = Annotated[
    Path, typer.Option("--content-dir", help="Meetups content dir")
]
DEFAULT_CONTENT_DIR = Path("page/content/spotkania")


def _build_adapters(settings: SocialSettings) -> dict[Channel, object]:
    adapters: dict[Channel, object] = {}
    if settings.meta_page_id and settings.meta_access_token:
        adapters[Channel.FACEBOOK] = FacebookAdapter(
            settings.meta_page_id, settings.meta_access_token
        )
    if settings.ig_user_id and settings.meta_access_token:
        adapters[Channel.INSTAGRAM] = InstagramAdapter(
            settings.ig_user_id, settings.meta_access_token
        )
    if settings.discord_webhook_url:
        adapters[Channel.DISCORD] = DiscordAdapter(settings.discord_webhook_url)
    return adapters


def _meetup_ids(repository: SocialRepository, meetup_id: str | None) -> list[str]:
    return [meetup_id] if meetup_id else repository.meetups_with_schedule()


@social_app.command("dry-run")
def dry_run(
    meetup_id: MeetupOption = None,
    content_dir: ContentDirOption = DEFAULT_CONTENT_DIR,
) -> None:
    """Pokaż dokładne payloady, które opublikowałby najbliższy run (bez publikacji)."""
    setup_logging(level="INFO")
    settings = SocialSettings()
    repository = SocialRepository(content_dir)
    publisher = Publisher(repository, adapters={}, site_base_url=settings.site_base_url)
    now = datetime.datetime.now(WARSAW)
    for mid in _meetup_ids(repository, meetup_id):
        planned = publisher.plan(mid, now)
        if not planned:
            typer.echo(f"[{mid}] nic nie jest due")
            continue
        for p in planned:
            typer.echo(
                f"\n=== #{mid} · {p.post_id} → {p.channel} (slot {p.scheduled}) ==="
            )
            if p.image_url:
                typer.echo(f"image_url: {p.image_url}")
            if p.ig_tagged:
                typer.echo(f"ig_tagged: {p.ig_tagged}")
            typer.echo(p.text)


@social_app.command("publish")
def publish(
    meetup_id: MeetupOption = None,
    content_dir: ContentDirOption = DEFAULT_CONTENT_DIR,
) -> None:
    """Opublikuj wszystko, co jest due (scheduled <= teraz i brak w status.json)."""
    setup_logging(level="INFO")
    settings = SocialSettings()
    repository = SocialRepository(content_dir)
    publisher = Publisher(
        repository,
        adapters=_build_adapters(settings),
        site_base_url=settings.site_base_url,
    )
    now = datetime.datetime.now(WARSAW)
    failed = 0
    published = 0
    for mid in _meetup_ids(repository, meetup_id):
        outcomes = publisher.publish_due(mid, now)
        if not outcomes:
            typer.echo(f"[{mid}] nic nie jest due")
        for outcome in outcomes:
            if outcome.ok:
                published += 1
                typer.echo(
                    f"[{mid}] OK {outcome.post_id}:{outcome.channel}"
                    f" -> {outcome.external_id}"
                )
            else:
                failed += 1
                typer.echo(
                    f"[{mid}] FAILED {outcome.post_id}:{outcome.channel}:"
                    f" {outcome.error}"
                )
    typer.echo(f"published: {published}, failed: {failed}")
    if failed:
        raise typer.Exit(code=1)


@social_app.command("yt-create-live")
def yt_create_live(
    title: Annotated[str, typer.Option("--title", help="Tytuł transmisji")],
    start: Annotated[
        str,
        typer.Option("--start", help="Start, np. '2026-07-29 17:45' (Europe/Warsaw)"),
    ],
    description_file: Annotated[
        Path | None,
        typer.Option("--description-file", help="Plik z opisem (np. youtube-live.md)"),
    ] = None,
) -> None:
    """Załóż zaplanowany live na YouTube i wypisz link do transmisji."""
    setup_logging(level="INFO")
    start_dt = datetime.datetime.strptime(start, "%Y-%m-%d %H:%M").replace(
        tzinfo=WARSAW
    )
    description = (
        description_file.read_text(encoding="utf-8") if description_file else ""
    )
    url = YouTubeLive().create_live(
        title=title, start=start_dt, description=description
    )
    typer.echo(url)
