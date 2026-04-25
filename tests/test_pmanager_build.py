from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from pmanager.build import (
    BuildPlanError,
    build_vtk,
    configure_vtk,
    make_vtk_build_plan,
    resolve_build_choice,
)
from pmanager.cli import app
from pmanager.cmake import read_cmake_cache_generator
from pmanager.paths import ProjectPaths
from pmanager.process import CommandResult
from pmanager.targets import get_target


def test_read_cmake_cache_generator(tmp_path: Path) -> None:
    build_dir = tmp_path / "build"
    build_dir.mkdir()
    (build_dir / "CMakeCache.txt").write_text(
        "OTHER=value\nCMAKE_GENERATOR:INTERNAL=Ninja\n",
        encoding="utf-8",
    )

    assert read_cmake_cache_generator(build_dir) == "Ninja"


def test_vtk_build_plan_uses_target_layout(tmp_path: Path) -> None:
    paths = ProjectPaths(root=tmp_path)
    target = "win-amd64-msvc2022-py310-release"

    plan = make_vtk_build_plan(
        target_name=target,
        paths=paths,
        python_exe=tmp_path / ".venvs" / target / "Scripts" / "python.exe",
        requested_backend="vs",
    )

    assert plan.source_dir == tmp_path / "external" / "src" / "vtk-9.3.1"
    assert plan.build_dir == tmp_path / "external" / "build" / "vtk-9.3.1" / target
    assert plan.install_dir == tmp_path / "external" / "install" / "vtk-9.3.1" / target / "sdk"
    assert plan.wheelhouse_dir == tmp_path / "external" / "wheelhouse" / "vtk-9.3.1" / target
    assert "-DVTK_WRAP_PYTHON=ON" in plan.configure_command
    assert "-DVTK_WHEEL_BUILD=ON" in plan.configure_command
    assert "-A" in plan.configure_command
    assert "x64" in plan.configure_command
    assert plan.build_command[-2:] == ["--config", "Release"]


def test_vtk_build_plan_linux_defaults_to_ninja(tmp_path: Path) -> None:
    paths = ProjectPaths(root=tmp_path)
    target = "linux-x86_64-gcc-py312-release"

    plan = make_vtk_build_plan(target_name=target, paths=paths)

    assert plan.build_choice.generator == "Ninja"
    assert "-A" not in plan.configure_command
    assert "--config" not in plan.build_command


def test_existing_generator_refuses_backend_switch(tmp_path: Path) -> None:
    build_dir = tmp_path / "build"
    build_dir.mkdir()
    (build_dir / "CMakeCache.txt").write_text(
        "CMAKE_GENERATOR:INTERNAL=Ninja\n",
        encoding="utf-8",
    )

    try:
        resolve_build_choice(
            target=get_target("win-amd64-msvc2022-py310-release"),
            build_dir=build_dir,
            requested_backend="vs",
        )
    except BuildPlanError as exc:
        assert "refusing backend switch" in str(exc)
    else:  # pragma: no cover - defensive
        raise AssertionError("Expected backend switch refusal")


def test_build_vtk_cli_prints_dry_run_plan(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("pmanager.build.ProjectPaths.discover", lambda: ProjectPaths(root=tmp_path))
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["build", "vtk", "--target", "win-amd64-msvc2022-py310-release", "--backend", "vs"],
    )

    assert result.exit_code == 0
    assert "Configure:" in result.stdout
    assert "cmake" in result.stdout
    assert "Visual Studio 17 2022" in result.stdout


def test_configure_vtk_runs_configure_command(monkeypatch, tmp_path: Path) -> None:
    paths = ProjectPaths(root=tmp_path)
    target = "win-amd64-msvc2022-py310-release"
    plan = make_vtk_build_plan(
        target_name=target,
        paths=paths,
        python_exe=tmp_path / ".venvs" / target / "Scripts" / "python.exe",
        requested_backend="vs",
    )
    plan.source_dir.mkdir(parents=True)
    calls: list[tuple[list[str], Path | None]] = []

    def fake_run_command(command: list[str], *, cwd: Path | None = None) -> CommandResult:
        calls.append((command, cwd))
        return CommandResult(command=command, cwd=cwd, returncode=0)

    monkeypatch.setattr("pmanager.build.run_command", fake_run_command)

    result = configure_vtk(plan)

    assert result.command == plan.configure_command
    assert calls == [(plan.configure_command, None)]
    assert plan.build_dir.exists()
    assert plan.install_dir.exists()
    assert plan.wheelhouse_dir.exists()


def test_configure_vtk_refuses_windows_ninja_without_compiler(monkeypatch, tmp_path: Path) -> None:
    paths = ProjectPaths(root=tmp_path)
    target = "win-amd64-msvc2022-py310-release"
    plan = make_vtk_build_plan(
        target_name=target,
        paths=paths,
        python_exe=tmp_path / ".venvs" / target / "Scripts" / "python.exe",
        requested_backend="ninja",
    )
    plan.source_dir.mkdir(parents=True)
    monkeypatch.setattr("pmanager.build.shutil.which", lambda name: None)
    monkeypatch.delenv("CC", raising=False)
    monkeypatch.delenv("CXX", raising=False)

    try:
        configure_vtk(plan)
    except BuildPlanError as exc:
        assert "Ninja was selected" in str(exc)
        assert "x64 Native Tools Command Prompt" in str(exc)
    else:  # pragma: no cover - defensive
        raise AssertionError("Expected missing compiler refusal")


def test_build_vtk_runs_build_command(monkeypatch, tmp_path: Path) -> None:
    paths = ProjectPaths(root=tmp_path)
    target = "win-amd64-msvc2022-py310-release"
    plan = make_vtk_build_plan(
        target_name=target,
        paths=paths,
        python_exe=tmp_path / ".venvs" / target / "Scripts" / "python.exe",
        requested_backend="vs",
    )
    plan.build_dir.mkdir(parents=True)
    (plan.build_dir / "CMakeCache.txt").write_text(
        "CMAKE_GENERATOR:INTERNAL=Visual Studio 17 2022\n",
        encoding="utf-8",
    )
    calls: list[tuple[list[str], Path | None]] = []

    def fake_run_command(command: list[str], *, cwd: Path | None = None) -> CommandResult:
        calls.append((command, cwd))
        return CommandResult(command=command, cwd=cwd, returncode=0)

    monkeypatch.setattr("pmanager.build.run_command", fake_run_command)

    result = build_vtk(plan)

    assert result.command == plan.build_command
    assert calls == [(plan.build_command, None)]


def test_build_vtk_refuses_missing_cmake_cache(tmp_path: Path) -> None:
    paths = ProjectPaths(root=tmp_path)
    target = "win-amd64-msvc2022-py310-release"
    plan = make_vtk_build_plan(
        target_name=target,
        paths=paths,
        python_exe=tmp_path / ".venvs" / target / "Scripts" / "python.exe",
        requested_backend="vs",
    )

    try:
        build_vtk(plan)
    except BuildPlanError as exc:
        assert "CMake cache does not exist" in str(exc)
    else:  # pragma: no cover - defensive
        raise AssertionError("Expected missing CMake cache refusal")


def test_build_vtk_cli_runs_build_step(monkeypatch, tmp_path: Path) -> None:
    calls = []
    monkeypatch.setattr("pmanager.build.ProjectPaths.discover", lambda: ProjectPaths(root=tmp_path))

    def fake_run_vtk_build(plan):
        calls.append(plan)
        return CommandResult(command=plan.build_command, cwd=None, returncode=0)

    monkeypatch.setattr("pmanager.cli.run_vtk_build", fake_run_vtk_build)

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "build",
            "vtk",
            "--target",
            "win-amd64-msvc2022-py310-release",
            "--backend",
            "vs",
            "--build",
        ],
    )

    assert result.exit_code == 0
    assert "Running VTK build step" in result.stdout
    assert len(calls) == 1
