from __future__ import annotations

import pytest

pytest.importorskip("typer")

from typer.testing import CliRunner

from pmanager.cli import app


def test_targets_command_lists_phase1_targets() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["targets"])
    assert result.exit_code == 0
    assert "win-amd64-msvc2022-py310-release" in result.stdout
    assert "linux-x86_64-gcc-py312-release" in result.stdout
