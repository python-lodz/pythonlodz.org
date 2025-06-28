from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class GoogleSheetsConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="GOOGLE_SHEETS__",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    sheet_id: str = Field(...)
    credentials_path: Path = Field(default=Path(".client_secret.json"))
    token_cache_path: Path = Field(default=Path(".client_secret.token.json"))
    meetups_sheet_name: str = Field(default="meetups")
    talks_sheet_name: str = Field(default="Sheet1")


class AssetsConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ASSETS__",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    assets_dir: Path = Field(default=Path("page/assets"))
    avatars_dir: Path = Field(default=Path("page/assets/images/avatars"))


class HugoConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="HUGO__", env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    content_dir: Path = Field(default=Path("page/content"))
    meetups_content_dir: Path = Field(default=Path("page/content/spotkania"))
    data_dir: Path = Field(default=Path("page/data"))


class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    google_sheets: GoogleSheetsConfig
    assets: AssetsConfig = Field(default_factory=AssetsConfig)
    hugo: HugoConfig = Field(default_factory=HugoConfig)

    debug: bool = Field(default=False)
    dry_run: bool = Field(default=False)

    def __init__(self, **data):
        if "google_sheets" not in data:
            try:
                data["google_sheets"] = GoogleSheetsConfig()
            except Exception:
                pass
        super().__init__(**data)
