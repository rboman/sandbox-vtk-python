from __future__ import annotations

import os
from pathlib import Path

from pmanager.environment import clean_environment, path_is_within, unsafe_variables


def test_unsafe_variables_allows_matching_target_venv(tmp_path: Path) -> None:
    target_venv = tmp_path / ".venvs" / "target"
    env = {
        "VIRTUAL_ENV": str(target_venv),
        "PYTHONPATH": str(tmp_path / "global-site-packages"),
    }

    unsafe = unsafe_variables(env, target_venv=target_venv)

    assert "VIRTUAL_ENV" not in unsafe
    assert unsafe["PYTHONPATH"] == str(tmp_path / "global-site-packages")


def test_unsafe_variables_rejects_foreign_active_venv(tmp_path: Path) -> None:
    target_venv = tmp_path / ".venvs" / "target"
    foreign_venv = tmp_path / ".venvs" / "foreign"

    unsafe = unsafe_variables({"VIRTUAL_ENV": str(foreign_venv)}, target_venv=target_venv)

    assert unsafe["VIRTUAL_ENV"] == str(foreign_venv)


def test_clean_environment_sets_repo_contract_and_filters_path(tmp_path: Path) -> None:
    env = {
        "PATH": os.pathsep.join(
            [
                str(tmp_path / "tools"),
                str(tmp_path / "old-vtk" / "bin"),
                str(tmp_path / ".venvs" / "other" / "Scripts"),
            ]
        ),
        "PYTHONPATH": str(tmp_path / "polluted"),
        "HOME": str(tmp_path / "home"),
    }

    clean = clean_environment(
        repo_root=tmp_path,
        target="win-amd64-msvc2022-py310-release",
        target_venv=tmp_path / ".venvs" / "win-amd64-msvc2022-py310-release",
        base=env,
    )

    assert clean["PYTHONNOUSERSITE"] == "1"
    assert clean["PIP_DISABLE_PIP_VERSION_CHECK"] == "1"
    assert clean["SANDBOX_VTK_PYTHON_REPO_ROOT"] == str(tmp_path.resolve(strict=False))
    assert clean["SANDBOX_VTK_PYTHON_TARGET"] == "win-amd64-msvc2022-py310-release"
    assert "PYTHONPATH" not in clean
    assert "old-vtk" not in clean["PATH"]
    assert ".venvs" not in clean["PATH"]
    assert str(tmp_path / "tools") in clean["PATH"]


def test_path_is_within_uses_resolved_paths(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    child = root / "external" / "src"
    outside = tmp_path / "elsewhere"

    assert path_is_within(child, root)
    assert not path_is_within(outside, root)
