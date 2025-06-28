"""Configuration models using pydantic-settings."""

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class GoogleSheetsConfig(BaseSettings):
    """Configuration for Google Sheets API."""
    
    model_config = SettingsConfigDict(
        env_prefix="GOOGLE_SHEETS__",
        env_file=".env",
        env_file_encoding="utf-8"
    )
    
    sheet_id: str = Field(..., description="Google Sheets ID")
    credentials_path: Path = Field(
        default=Path(".client_secret.json"),
        description="Path to Google API credentials file"
    )
    token_cache_path: Path = Field(
        default=Path(".client_secret.token.json"),
        description="Path to cached token file"
    )
    meetups_sheet_name: str = Field(
        default="meetups",
        description="Name of the meetups sheet tab"
    )
    talks_sheet_name: str = Field(
        default="Sheet1",
        description="Name of the talks/main sheet tab"
    )


class AssetsConfig(BaseSettings):
    """Configuration for assets handling."""
    
    model_config = SettingsConfigDict(
        env_prefix="ASSETS__",
        env_file=".env",
        env_file_encoding="utf-8"
    )
    
    assets_dir: Path = Field(
        default=Path("page/assets"),
        description="Directory for storing assets"
    )
    avatars_dir: Path = Field(
        default=Path("page/assets/images/avatars"),
        description="Directory for speaker avatars"
    )


class HugoConfig(BaseSettings):
    """Configuration for Hugo site generation."""
    
    model_config = SettingsConfigDict(
        env_prefix="HUGO__",
        env_file=".env",
        env_file_encoding="utf-8"
    )
    
    content_dir: Path = Field(
        default=Path("page/content"),
        description="Hugo content directory"
    )
    meetups_content_dir: Path = Field(
        default=Path("page/content/spotkania"),
        description="Directory for meetup pages"
    )
    data_dir: Path = Field(
        default=Path("page/data"),
        description="Hugo data directory"
    )


class AppConfig(BaseSettings):
    """Main application configuration."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )
    
    # Nested configurations
    google_sheets: GoogleSheetsConfig = Field(default_factory=GoogleSheetsConfig)
    assets: AssetsConfig = Field(default_factory=AssetsConfig)
    hugo: HugoConfig = Field(default_factory=HugoConfig)
    
    # General settings
    debug: bool = Field(default=False, description="Enable debug mode")
    dry_run: bool = Field(default=False, description="Enable dry run mode")
