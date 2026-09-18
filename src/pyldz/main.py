import logging
from pathlib import Path

import typer
from typing_extensions import Annotated

from pyldz.config import AppConfig
from pyldz.hugo_generator import HugoMeetupGenerator, MeetupGenerationError
from pyldz.logging_config import setup_logging
from pyldz.models import GoogleSheetsAPI, GoogleSheetsRepository, LocationRepository
from pyldz.preflight import MeetupPreflight, build_preflight
from pyldz.social.cli import social_app

log = logging.getLogger(__name__)

app = typer.Typer(name="pyldz")
app.add_typer(social_app)

MeetupIdArgument = Annotated[str, typer.Argument(help="Numer spotkania, np. 66")]


def _build_repository(config: AppConfig) -> GoogleSheetsRepository:
    location_repo = LocationRepository(config.hugo.data_dir / "locations")
    return GoogleSheetsRepository(GoogleSheetsAPI(config.google_sheets), location_repo)


def _preflight(
    repository: GoogleSheetsRepository, meetup_id: str, data_dir: Path
) -> MeetupPreflight:
    meetup_row = next(
        (row for row in repository.fetch_meetup_rows() if row.meetup_id == meetup_id),
        None,
    )
    if meetup_row is None:
        typer.echo(f"Spotkania #{meetup_id} nie ma w arkuszu (zakładka meetups).")
        raise typer.Exit(1)

    talk_rows = [
        row for row in repository.fetch_talk_rows() if row.meetup_id == meetup_id
    ]
    return build_preflight(meetup_row, talk_rows, data_dir)


@app.command()
def show(
    meetup_id: MeetupIdArgument,
    as_json: Annotated[
        bool,
        typer.Option("--json", help="Wyjście w JSON — dla skryptów i skilli gk-sm"),
    ] = False,
) -> None:
    """Pokaż dane spotkania z arkusza i listę braków. Niczego nie zapisuje."""
    config = AppConfig()
    report = _preflight(_build_repository(config), meetup_id, config.hugo.data_dir)

    typer.echo(report.model_dump_json(indent=2) if as_json else report.to_text())


@app.command()
def generate(
    output_dir: Annotated[
        Path,
        typer.Option(
            "--output-dir",
            "-o",
            help="Output directory for Hugo site (default: page)",
        ),
    ] = Path("page"),
    meetup_id: Annotated[
        str | None,
        typer.Option(
            "--meetup-id",
            "-m",
            help="Generate Hugo files for specific meetup ID (optional)",
        ),
    ] = None,
) -> None:
    setup_logging(level="INFO")

    config = AppConfig()
    repository = _build_repository(config)

    report: MeetupPreflight | None = None
    if meetup_id:
        report = _preflight(repository, meetup_id, config.hugo.data_dir)
        if report.has_errors:
            typer.echo(report.to_text())
            typer.echo(
                f"\nNie generuję #{meetup_id} — najpierw popraw w arkuszu pozycje ✖."
            )
            raise typer.Exit(1)

    log.info("🚀 Generating Hugo meetup files...")
    log.info("=" * 50)

    generator = HugoMeetupGenerator(output_dir)

    log.info("Generating meetup markdown files...")
    try:
        if meetup_id:
            generated_files = [generator.generate_meetup(meetup_id, repository)]
        else:
            generated_files = generator.generate_all_meetups(repository)
    except MeetupGenerationError as error:
        typer.echo(str(error))
        raise typer.Exit(1) from error

    log.info(f"Generated {len(generated_files)} meetup files:")
    for file_path in generated_files:
        log.info(f"  - {file_path}")

    log.info("🎉 Hugo file generation completed successfully!")

    if report is not None:
        typer.echo("")
        typer.echo(report.to_text())


def main() -> None:
    app()


if __name__ == "__main__":
    main()
