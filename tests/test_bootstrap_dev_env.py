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

    def fake_run(command, check, capture_output=False, text=False):
        commands.append(command)

        class Completed:
            returncode = 0
            stdout = ""
            stderr = ""

        return Completed()

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    monkeypatch.setattr(module, "pmanager_points_to_checkout", lambda python_path, root: False)
    monkeypatch.setattr(module, "wheel_command_available", lambda python_path: True)

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
    purelib = tmp_path / ".venvs" / "target" / "Lib" / "site-packages"
    scripts = tmp_path / ".venvs" / "target" / "Scripts"

    monkeypatch.setattr(module, "pmanager_points_to_checkout", lambda python_path, root: True)
    monkeypatch.setattr(
        module.subprocess,
        "run",
        lambda command, check, capture_output=False, text=False: commands.append(command),
    )
    monkeypatch.setattr(
        module,
        "query_venv_path",
        lambda python_path, key: purelib if key == "purelib" else scripts,
    )

    module.install_pmanager_editable(tmp_path / ".venvs" / "target" / "bin" / "python", tmp_path)

    assert commands == []
    assert (purelib / "pmanager-dev.pth").exists()


def test_bootstrap_falls_back_to_stdlib_editable_install(monkeypatch, tmp_path: Path) -> None:
    module = load_bootstrap_module()
    python_path = tmp_path / ".venvs" / "target" / "Scripts" / "python.exe"
    purelib = tmp_path / ".venvs" / "target" / "Lib" / "site-packages"
    scripts = tmp_path / ".venvs" / "target" / "Scripts"

    class Completed:
        returncode = 1

    monkeypatch.setattr(module, "pmanager_points_to_checkout", lambda python_path, root: False)
    monkeypatch.setattr(
        module.subprocess,
        "run",
        lambda command, check, capture_output=False, text=False: Completed(),
    )
    monkeypatch.setattr(
        module,
        "query_venv_path",
        lambda python_path, key: purelib if key == "purelib" else scripts,
    )

    module.install_pmanager_editable(python_path, tmp_path)

    pth = purelib / "pmanager-dev.pth"
    assert pth.read_text(encoding="utf-8").strip() == str(
        tmp_path / "packages" / "pmanager" / "src"
    )
    if module.os.name == "nt":
        assert (scripts / "pmanager.cmd").exists()
    else:
        assert (scripts / "pmanager").exists()
