from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class GoogleSheetsConfig(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    sheet_id: str
    credentials_path: Path = Path(".client_secret.json")
    token_cache_path: Path = Path(".client_secret.token.json")

    @field_validator("credentials_path")
    @classmethod
    def validate_credentials_file_exists(cls, v: Path) -> Path:
        if not v.exists():
            raise ValueError(
                f"Credentials file not found: {v}. "
                f"Please ensure you have the Google Sheets API credentials file. "
                f"You can get it from: https://console.cloud.google.com/"
            )
        return v


class AssetsConfig(BaseSettings):
    assets_dir: Path = Path("page/assets")
    avatars_dir: Path = Path("page/assets/images/avatars")


class HugoConfig(BaseSettings):
    content_dir: Path = Path("page/content")
    meetups_content_dir: Path = Path("page/content/spotkania")
    data_dir: Path = Path("page/data")


class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_nested_delimiter="__",
    )

    google_sheets: GoogleSheetsConfig
    assets: AssetsConfig = AssetsConfig()
    hugo: HugoConfig = HugoConfig()

    debug: bool = False
    dry_run: bool = False
