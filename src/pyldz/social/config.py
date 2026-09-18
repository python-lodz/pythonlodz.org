"""Settings for the social publisher — env var names match GitHub Secrets."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class SocialSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    meta_page_id: str | None = None
    meta_access_token: str | None = None
    ig_user_id: str | None = None
    discord_webhook_url: str | None = None
    site_base_url: str = "https://pythonlodz.org"
