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


def test_bootstrap_defaults_to_pmanager_dev_venv(monkeypatch, tmp_path: Path) -> None:
    module = load_bootstrap_module()
    calls = []

    monkeypatch.setattr(module, "repo_root", lambda: tmp_path)
    monkeypatch.setattr(module, "ensure_not_recreating_active_venv", lambda venv_dir: None)
    monkeypatch.setattr(module, "ensure_venv", lambda venv_dir: calls.append(venv_dir) or venv_dir / "python")
    monkeypatch.setattr(module, "install_dev_tools", lambda python_path: None)
    monkeypatch.setattr(module, "install_pmanager_editable", lambda python_path, root: None)
    monkeypatch.setattr(module.sys, "argv", ["bootstrap-dev-env.py"])

    assert module.main() == 0
    assert calls == [tmp_path / ".venvs" / "pmanager-dev"]


def test_bootstrap_target_option_is_transition_alias(monkeypatch, tmp_path: Path) -> None:
    module = load_bootstrap_module()
    calls = []
    target = "win-amd64-msvc2022-py310-release"

    monkeypatch.setattr(module, "repo_root", lambda: tmp_path)
    monkeypatch.setattr(module, "ensure_not_recreating_active_venv", lambda venv_dir: None)
    monkeypatch.setattr(module, "ensure_venv", lambda venv_dir: calls.append(venv_dir) or venv_dir / "python")
    monkeypatch.setattr(module, "install_dev_tools", lambda python_path: None)
    monkeypatch.setattr(module, "install_pmanager_editable", lambda python_path, root: None)
    monkeypatch.setattr(module.sys, "argv", ["bootstrap-dev-env.py", "--target", target])

    assert module.main() == 0
    assert calls == [tmp_path / ".venvs" / target]


def test_bootstrap_recreate_removes_selected_venv_before_create(monkeypatch, tmp_path: Path) -> None:
    module = load_bootstrap_module()
    calls = []

    monkeypatch.setattr(module, "repo_root", lambda: tmp_path)
    monkeypatch.setattr(module, "ensure_not_recreating_active_venv", lambda venv_dir: None)
    monkeypatch.setattr(module, "remove_venv", lambda venv_dir, venvs_root: calls.append(("remove", venv_dir)))
    monkeypatch.setattr(module, "ensure_venv", lambda venv_dir: calls.append(("create", venv_dir)) or venv_dir / "python")
    monkeypatch.setattr(module, "install_dev_tools", lambda python_path: None)
    monkeypatch.setattr(module, "install_pmanager_editable", lambda python_path, root: None)
    monkeypatch.setattr(module.sys, "argv", ["bootstrap-dev-env.py", "--recreate"])

    assert module.main() == 0
    expected = tmp_path / ".venvs" / "pmanager-dev"
    assert calls == [("remove", expected), ("create", expected)]


def test_remove_venv_refuses_active_venv(monkeypatch, tmp_path: Path) -> None:
    module = load_bootstrap_module()
    venv_dir = tmp_path / ".venvs" / "pmanager-dev"
    monkeypatch.setenv("VIRTUAL_ENV", str(venv_dir))

    try:
        module.remove_venv(venv_dir, tmp_path / ".venvs")
    except RuntimeError as exc:
        assert "active venv" in str(exc)
    else:  # pragma: no cover - defensive
        raise AssertionError("remove_venv should refuse to remove the active venv")
