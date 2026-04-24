from __future__ import annotations

import importlib.util
from pathlib import Path


def load_bootstrap_module():
    path = Path("scripts/bootstrap-dev-env.py")
    spec = importlib.util.spec_from_file_location("bootstrap_dev_env", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_bootstrap_installs_pmanager_without_build_isolation(monkeypatch, tmp_path: Path) -> None:
    module = load_bootstrap_module()
    commands = []

    def fake_run(command, check):
        commands.append(command)

        class Completed:
            returncode = 0

        return Completed()

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    monkeypatch.setattr(module, "pmanager_points_to_checkout", lambda python_path, root: False)

    module.install_pmanager_editable(tmp_path / ".venvs" / "target" / "bin" / "python", tmp_path)

    assert commands
    assert "--no-build-isolation" in commands[0]
    assert "-e" in commands[0]
    assert str(tmp_path / "packages" / "pmanager") in commands[0]


def test_bootstrap_skips_install_when_pmanager_already_points_to_checkout(
    monkeypatch, tmp_path: Path
) -> None:
    module = load_bootstrap_module()
    commands = []

    monkeypatch.setattr(module, "pmanager_points_to_checkout", lambda python_path, root: True)
    monkeypatch.setattr(module.subprocess, "run", lambda command, check: commands.append(command))

    module.install_pmanager_editable(tmp_path / ".venvs" / "target" / "bin" / "python", tmp_path)

    assert commands == []
