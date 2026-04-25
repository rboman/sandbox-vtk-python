from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from pmanager.cli import app
from pmanager.paths import ProjectPaths
from pmanager.process import CommandResult
from pmanager.workflow import WindowsPhase1Workflow, run_windows_phase1_workflow


def test_windows_phase1_workflow_runs_steps_in_order(monkeypatch, tmp_path: Path) -> None:
    calls: list[str] = []
    target = "win-amd64-msvc2022-py310-release"
    paths = ProjectPaths(root=tmp_path)

    def record(name):
        def inner(*args, **kwargs):
            calls.append(name)
        return inner

    monkeypatch.setattr("pmanager.workflow.fetch_vtk", record("fetch"))
    monkeypatch.setattr("pmanager.workflow.configure_vtk", record("configure"))
    monkeypatch.setattr("pmanager.workflow.build_vtk", record("build"))
    monkeypatch.setattr("pmanager.workflow.install_vtk", record("install"))
    monkeypatch.setattr("pmanager.workflow.wheel_vtk", record("wheel"))
    monkeypatch.setattr("pmanager.workflow.sync_venv", record("sync"))
    monkeypatch.setattr("pmanager.workflow.validate_target_runtime", record("validate"))

    run_windows_phase1_workflow(
        WindowsPhase1Workflow(
            target=target,
            backend="vs",
            generator=None,
            architecture="x64",
            parallel=None,
            force_fetch=False,
            skip_fetch=False,
            skip_validation=False,
        ),
        paths=paths,
    )

    assert calls == ["fetch", "configure", "build", "install", "wheel", "sync", "validate"]


def test_windows_phase1_workflow_skips_existing_source_and_validation(
    monkeypatch,
    tmp_path: Path,
) -> None:
    calls: list[str] = []
    target = "win-amd64-msvc2022-py310-release"
    paths = ProjectPaths(root=tmp_path)
    (paths.source_root / "vtk-9.3.1").mkdir(parents=True)

    monkeypatch.setattr("pmanager.workflow.fetch_vtk", lambda *args, **kwargs: calls.append("fetch"))
    monkeypatch.setattr("pmanager.workflow.configure_vtk", lambda *args, **kwargs: calls.append("configure"))
    monkeypatch.setattr("pmanager.workflow.build_vtk", lambda *args, **kwargs: calls.append("build"))
    monkeypatch.setattr("pmanager.workflow.install_vtk", lambda *args, **kwargs: calls.append("install"))
    monkeypatch.setattr("pmanager.workflow.wheel_vtk", lambda *args, **kwargs: calls.append("wheel"))
    monkeypatch.setattr("pmanager.workflow.sync_venv", lambda *args, **kwargs: calls.append("sync"))
    monkeypatch.setattr("pmanager.workflow.validate_target_runtime", lambda *args, **kwargs: calls.append("validate"))

    run_windows_phase1_workflow(
        WindowsPhase1Workflow(
            target=target,
            backend="vs",
            generator=None,
            architecture="x64",
            parallel=None,
            force_fetch=False,
            skip_fetch=False,
            skip_validation=True,
        ),
        paths=paths,
    )

    assert calls == ["configure", "build", "install", "wheel", "sync"]


def test_validate_target_runtime_uses_target_python(monkeypatch, tmp_path: Path) -> None:
    from pmanager.sync import make_venv_sync_plan
    from pmanager.workflow import validate_target_runtime

    calls: list[list[str]] = []
    plan = make_venv_sync_plan(
        target_name="win-amd64-msvc2022-py310-release",
        paths=ProjectPaths(root=tmp_path),
    )

    def fake_run_command(command):
        calls.append(command)
        return CommandResult(command=command, cwd=None, returncode=0)

    monkeypatch.setattr("pmanager.workflow.run_command", fake_run_command)

    validate_target_runtime(plan)

    assert calls[0][:4] == [str(plan.python_exe), "-m", "pmanager", "validate"]
    assert calls[0][4] == "provenance"
    assert calls[1][:4] == [str(plan.python_exe), "-m", "pmanager", "validate"]
    assert calls[1][4] == "import-order"


def test_workflow_windows_phase1_help_exists() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["workflow", "windows-phase1", "--help"])

    assert result.exit_code == 0
    assert "--skip-fetch" in result.stdout
    assert "--skip-validation" in result.stdout


def test_workflow_windows_phase1_cli_invokes_workflow(monkeypatch) -> None:
    calls = []

    def fake_run(workflow):
        calls.append(workflow)

    monkeypatch.setattr("pmanager.cli.run_windows_phase1_or_raise", fake_run)
    runner = CliRunner()
    result = runner.invoke(app, ["workflow", "windows-phase1", "--backend", "vs", "--skip-validation"])

    assert result.exit_code == 0
    assert calls[0].backend == "vs"
    assert calls[0].skip_validation is True
