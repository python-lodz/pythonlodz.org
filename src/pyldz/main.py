import logging
from pathlib import Path

import typer
from typing_extensions import Annotated

from pyldz.config import AppConfig
from pyldz.hugo_generator import HugoMeetupGenerator
from pyldz.logging_config import setup_logging
from pyldz.models import GoogleSheetsAPI, GoogleSheetsRepository, LocationRepository

log = logging.getLogger(__name__)

app = typer.Typer(name="pyldz")


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

    log.info("🚀 Generating Hugo meetup files...")
    log.info("=" * 50)

    config = AppConfig()

    location_repo = LocationRepository(config.hugo.data_dir / "locations")
    repository = GoogleSheetsRepository(
        GoogleSheetsAPI(config.google_sheets), location_repo
    )
    generator = HugoMeetupGenerator(output_dir)

    log.info("Generating meetup markdown files...")
    if meetup_id:
        generated_files = [generator.generate_meetup(meetup_id, repository)]
    else:
        generated_files = generator.generate_all_meetups(repository)

    log.info(f"Generated {len(generated_files)} meetup files:")
    for file_path in generated_files:
        log.info(f"  - {file_path}")

    log.info("🎉 Hugo file generation completed successfully!")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
