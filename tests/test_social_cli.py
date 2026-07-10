"""Tests for the `pyldz social` CLI."""

import json
from pathlib import Path

from typer.testing import CliRunner

import pyldz.social.cli as cli_module
from pyldz.main import app

runner = CliRunner()


class DummyAdapter:
    def publish(self, *args, **kwargs):
        return "ext-1"


def all_dummy_adapters(settings):
    from pyldz.social.models import Channel

    return {
        Channel.FACEBOOK: DummyAdapter(),
        Channel.INSTAGRAM: DummyAdapter(),
        Channel.DISCORD: DummyAdapter(),
    }


def test_dry_run_prints_due_payloads(social_content_dir: Path):
    result = runner.invoke(
        app,
        ["social", "dry-run", "--content-dir", str(social_content_dir)],
    )
    assert result.exit_code == 0
    assert "save-the-date" in result.output
    assert "facebook" in result.output
    # nic nie zostało opublikowane ani zapisane
    assert not (social_content_dir / "65" / "social" / "status.json").exists()


def test_publish_writes_status_and_is_idempotent(social_content_dir: Path, monkeypatch):
    monkeypatch.setattr(cli_module, "_build_adapters", all_dummy_adapters)
    result = runner.invoke(
        app, ["social", "publish", "--content-dir", str(social_content_dir)]
    )
    assert result.exit_code == 0
    status = json.loads(
        (social_content_dir / "65" / "social" / "status.json").read_text()
    )
    assert "save-the-date:facebook" in status["published"]

    second = runner.invoke(
        app, ["social", "publish", "--content-dir", str(social_content_dir)]
    )
    assert second.exit_code == 0
    assert "nic nie jest due" in second.output


def test_publish_exits_nonzero_on_failure(social_content_dir: Path, monkeypatch):
    monkeypatch.setattr(cli_module, "_build_adapters", lambda settings: {})
    result = runner.invoke(
        app, ["social", "publish", "--content-dir", str(social_content_dir)]
    )
    assert result.exit_code == 1
