"""Tests for SocialSettings env mapping."""

from pyldz.social.config import SocialSettings


def test_defaults_do_not_require_any_env(monkeypatch):
    for name in (
        "META_PAGE_ID",
        "META_ACCESS_TOKEN",
        "IG_USER_ID",
        "DISCORD_WEBHOOK_URL",
    ):
        monkeypatch.delenv(name, raising=False)
    settings = SocialSettings(_env_file=None)
    assert settings.meta_page_id is None
    assert settings.site_base_url == "https://pythonlodz.org"


def test_reads_github_secrets_names_from_env(monkeypatch):
    monkeypatch.setenv("META_PAGE_ID", "111")
    monkeypatch.setenv("META_ACCESS_TOKEN", "tok")
    monkeypatch.setenv("IG_USER_ID", "222")
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.example/hook")
    settings = SocialSettings(_env_file=None)
    assert settings.meta_page_id == "111"
    assert settings.meta_access_token == "tok"
    assert settings.ig_user_id == "222"
    assert settings.discord_webhook_url == "https://discord.example/hook"
