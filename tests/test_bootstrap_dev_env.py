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


def test_bootstrap_installs_base_development_tools(monkeypatch, tmp_path: Path) -> None:
    module = load_bootstrap_module()
    commands = []

    monkeypatch.setattr(module, "run", commands.append)

    python_path = tmp_path / ".venvs" / "target" / "Scripts" / "python.exe"
    module.install_dev_tools(python_path)

    assert commands == [
        [
            str(python_path),
            "-m",
            "pip",
            "install",
            "--upgrade",
            "pip",
            "setuptools",
            "wheel",
            "typer>=0.12,<1.0",
            "pytest",
        ]
    ]


def test_bootstrap_installs_pmanager_editable(monkeypatch, tmp_path: Path) -> None:
    module = load_bootstrap_module()
    commands = []

    monkeypatch.setattr(module, "run", commands.append)

    python_path = tmp_path / ".venvs" / "target" / "Scripts" / "python.exe"
    module.install_pmanager_editable(python_path, tmp_path)

    assert commands == [
        [
            str(python_path),
            "-m",
            "pip",
            "install",
            "--upgrade",
            "-e",
            str(tmp_path / "packages" / "pmanager"),
        ]
    ]
