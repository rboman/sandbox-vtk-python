from __future__ import annotations

import os
from pathlib import Path

from pmanager.paths import ProjectPaths
from pmanager.process import CommandResult
from pmanager.sync import (
    SyncError,
    find_vtk_wheel,
    make_venv_sync_plan,
    stage_vtk_runtime_windows,
    sync_venv,
    target_command_env,
    vtk_abi_suffix,
    write_vtk_constraint,
)


def test_make_venv_sync_plan_uses_target_layout(tmp_path: Path) -> None:
    paths = ProjectPaths(root=tmp_path)
    target = "win-amd64-msvc2022-py310-release"

    plan = make_venv_sync_plan(target_name=target, paths=paths)

    assert plan.venv_dir == tmp_path / ".venvs" / target
    assert plan.python_exe == tmp_path / ".venvs" / target / "Scripts" / "python.exe"
    assert plan.constraints_file == tmp_path / "constraints" / "py310.txt"
    assert plan.wheelhouse_dir == tmp_path / "external" / "wheelhouse" / "vtk-9.3.1" / target
    assert plan.sdk_dir == tmp_path / "external" / "install" / "vtk-9.3.1" / target / "sdk"
    assert plan.audit_script == tmp_path / "scripts" / "validate" / "audit-environment.py"


def test_find_vtk_wheel_selects_newest(tmp_path: Path) -> None:
    wheelhouse = tmp_path / "wheelhouse"
    wheelhouse.mkdir()
    older = wheelhouse / "vtk-9.3.1.dev0-old.whl"
    newer = wheelhouse / "vtk-9.3.1.dev0-new.whl"
    older.write_text("", encoding="utf-8")
    newer.write_text("", encoding="utf-8")
    os.utime(older, (1, 1))
    os.utime(newer, (2, 2))

    assert find_vtk_wheel(wheelhouse) == newer


def test_find_vtk_wheel_fails_when_missing(tmp_path: Path) -> None:
    try:
        find_vtk_wheel(tmp_path / "missing")
    except SyncError as exc:
        assert "Wheelhouse does not exist" in str(exc)
    else:  # pragma: no cover - defensive
        raise AssertionError("Expected missing wheelhouse failure")


def test_vtk_abi_suffix_accepts_dev_versions() -> None:
    assert vtk_abi_suffix("9.3.1.dev0") == "9.3"


def test_write_vtk_constraint(tmp_path: Path) -> None:
    plan = make_venv_sync_plan(
        target_name="win-amd64-msvc2022-py310-release",
        paths=ProjectPaths(root=tmp_path),
    )

    path = write_vtk_constraint(plan, "9.3.1.dev0")

    assert path.read_text(encoding="utf-8") == "vtk===9.3.1.dev0\n"


def test_target_command_env_uses_target_venv(monkeypatch, tmp_path: Path) -> None:
    plan = make_venv_sync_plan(
        target_name="win-amd64-msvc2022-py310-release",
        paths=ProjectPaths(root=tmp_path),
    )
    monkeypatch.setenv(
        "PATH",
        os.pathsep.join(
            [
                str(tmp_path / ".venvs" / "pmanager-dev"),
                r"C:\local\VTK-9.3.1\bin",
                r"C:\Python310\Lib\site-packages",
                r"C:\tools",
            ]
        ),
    )
    monkeypatch.setenv("PYTHONPATH", "bad")

    env = target_command_env(plan)

    assert env["VIRTUAL_ENV"] == str(plan.venv_dir)
    assert env["PYTHONNOUSERSITE"] == "1"
    assert "PYTHONPATH" not in env
    assert str(tmp_path / ".venvs" / "pmanager-dev") not in env["PATH"]
    assert r"C:\local\VTK-9.3.1\bin" not in env["PATH"]
    assert r"C:\Python310\Lib\site-packages" not in env["PATH"]
    assert r"C:\tools" in env["PATH"]
    assert str(plan.python_exe.parent) in env["PATH"]


def test_stage_vtk_runtime_windows_copies_dlls_and_writes_build_paths(
    monkeypatch,
    tmp_path: Path,
) -> None:
    plan = make_venv_sync_plan(
        target_name="win-amd64-msvc2022-py310-release",
        paths=ProjectPaths(root=tmp_path),
    )
    sdk_bin = plan.sdk_dir / "bin"
    sdk_bin.mkdir(parents=True)
    (sdk_bin / "vtkCommonCore.dll").write_text("dll", encoding="utf-8")
    vtkmodules_dir = tmp_path / ".venvs" / plan.target.name / "Lib" / "site-packages" / "vtkmodules"
    vtkmodules_dir.mkdir(parents=True)

    monkeypatch.setattr("pmanager.sync.vtk_modules_dir", lambda plan, env: vtkmodules_dir)
    monkeypatch.setattr("pmanager.sync.find_qt_bin_dir", lambda env: None)

    stage_vtk_runtime_windows(plan, "9.3.1.dev0", {})

    runtime_bin = vtkmodules_dir.parent / "bin"
    assert (runtime_bin / "vtkCommonCore.dll").exists()
    assert (runtime_bin / "vtkCommonCore-9.3.dll").exists()
    assert (vtkmodules_dir / "_build_paths.py").exists()


def test_sync_venv_runs_expected_commands(monkeypatch, tmp_path: Path) -> None:
    paths = ProjectPaths(root=tmp_path)
    target = "win-amd64-msvc2022-py310-release"
    plan = make_venv_sync_plan(target_name=target, paths=paths)
    plan.python_exe.parent.mkdir(parents=True)
    plan.python_exe.write_text("", encoding="utf-8")
    plan.constraints_file.parent.mkdir(parents=True)
    plan.constraints_file.write_text("pyvista==0.44.2\n", encoding="utf-8")
    plan.wheelhouse_dir.mkdir(parents=True)
    wheel = plan.wheelhouse_dir / "vtk-9.3.1.dev0-cp310-cp310-win_amd64.whl"
    wheel.write_text("", encoding="utf-8")
    calls: list[tuple[list[str], Path | None, str | None]] = []

    def fake_run_command(command, *, cwd=None, env=None):
        calls.append((command, cwd, None if env is None else env.get("CMAKE_PREFIX_PATH")))
        return CommandResult(command=command, cwd=cwd, returncode=0)

    monkeypatch.setattr("pmanager.sync.run_command", fake_run_command)
    monkeypatch.setattr("pmanager.sync.run_command_text", lambda command, *, cwd=None, env=None: "9.3.1.dev0")
    monkeypatch.setattr("pmanager.sync.stage_vtk_runtime_windows", lambda plan, vtk_version, env: None)

    sync_venv(plan)

    assert calls[0][0][1] == str(plan.audit_script)
    assert calls[1][0][2:5] == ["pip", "install", "--upgrade"]
    assert calls[2][0][-1] == str(wheel)
    assert "pyvista" in calls[3][0]
    assert calls[4][0][-1] == str(plan.codecpp_dir)
    assert calls[4][2] == str(plan.sdk_dir)
    assert calls[5][0][-1] == str(plan.codepy_dir)
    assert calls[6][0][-1] == str(plan.pmanager_dir)
    assert plan.vtk_constraint_file.read_text(encoding="utf-8") == "vtk===9.3.1.dev0\n"
