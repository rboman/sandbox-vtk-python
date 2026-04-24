from __future__ import annotations

import pytest

pytest.importorskip("typer")

from typer.testing import CliRunner

from pmanager.cli import app
from pmanager.libraries import get_library, library_names
from pmanager.paths import ProjectPaths
from pmanager.targets import get_target, target_names


def test_targets_command_lists_phase1_targets() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["targets"])
    assert result.exit_code == 0
    assert "win-amd64-msvc2022-py310-release" in result.stdout
    assert "linux-x86_64-gcc-py312-release" in result.stdout


def test_fetch_vtk_help_exists() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["fetch", "vtk", "--help"])
    assert result.exit_code == 0
    assert "vtk" in result.stdout


def test_build_vtk_help_exists() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["build", "vtk", "--help"])
    assert result.exit_code == 0
    assert "vtk" in result.stdout


def test_validate_command_group_exists() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["validate", "--help"])
    assert result.exit_code == 0
    assert "audit" in result.stdout
    assert "provenance" in result.stdout
    assert "import-order" in result.stdout


def test_validate_subcommand_help_exists() -> None:
    runner = CliRunner()
    for command in ("audit", "provenance", "import-order"):
        result = runner.invoke(app, ["validate", command, "--help"])
        assert result.exit_code == 0


def test_phase1_targets_are_explicit() -> None:
    assert target_names() == (
        "win-amd64-msvc2022-py310-release",
        "linux-x86_64-gcc-py312-release",
    )
    windows = get_target("win-amd64-msvc2022-py310-release")
    linux = get_target("linux-x86_64-gcc-py312-release")
    assert windows.python_tag == "py310"
    assert windows.toolchain == "msvc2022"
    assert linux.python_tag == "py312"
    assert linux.toolchain == "gcc"


def test_vtk_is_the_only_registered_library_for_now() -> None:
    assert library_names() == ("vtk",)
    vtk = get_library("VTK")
    assert vtk.name == "vtk"
    assert vtk.version == "9.3.1"
    assert vtk.source_dir_name == "vtk-9.3.1"


def test_project_paths_classify_target_layout(tmp_path) -> None:
    paths = ProjectPaths(root=tmp_path)
    target = "win-amd64-msvc2022-py310-release"
    assert paths.venv_dir(target) == tmp_path / ".venvs" / target
    assert paths.vtk_source_dir() == tmp_path / "external" / "src" / "vtk-9.3.1"
    assert paths.vtk_build_dir(target) == tmp_path / "external" / "build" / "vtk-9.3.1" / target
    assert paths.vtk_sdk_dir(target) == (
        tmp_path / "external" / "install" / "vtk-9.3.1" / target / "sdk"
    )
    assert paths.vtk_wheelhouse_dir(target) == (
        tmp_path / "external" / "wheelhouse" / "vtk-9.3.1" / target
    )
    assert paths.constraints_file("py310") == tmp_path / "constraints" / "py310.txt"
