from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pmanager.build import (
    BuildPlanError,
    build_vtk,
    configure_vtk,
    install_vtk,
    make_vtk_build_plan,
    print_vtk_build_plan,
    wheel_vtk,
)
from pmanager.fetch import FetchError, fetch_vtk
from pmanager.libraries import get_library
from pmanager.paths import ProjectPaths
from pmanager.process import CommandResult, run_command
from pmanager.sync import SyncError, ensure_target_venv, make_venv_sync_plan, sync_venv


class WorkflowError(RuntimeError):
    pass


@dataclass(frozen=True)
class WindowsPhase1Workflow:
    target: str
    backend: str
    generator: str | None
    architecture: str
    parallel: int | None
    force_fetch: bool
    skip_fetch: bool
    skip_validation: bool


def _step(title: str) -> None:
    print()
    print(f"== {title} ==")


def validate_target_runtime(sync_plan) -> list[CommandResult]:
    target_venv = str(sync_plan.venv_dir)
    sdk_root = str(sync_plan.sdk_dir)
    return [
        run_command(
            [
                str(sync_plan.python_exe),
                "-m",
                "pmanager",
                "validate",
                "provenance",
                "--target-venv",
                target_venv,
                "--target-sdk-root",
                sdk_root,
            ]
        ),
        run_command(
            [
                str(sync_plan.python_exe),
                "-m",
                "pmanager",
                "validate",
                "import-order",
                "--require-extension",
            ]
        ),
    ]


def run_windows_phase1_workflow(
    workflow: WindowsPhase1Workflow,
    *,
    paths: ProjectPaths | None = None,
) -> None:
    paths = paths or ProjectPaths.discover()
    library = get_library("vtk")
    source_dir = paths.source_root / library.source_dir_name

    if workflow.skip_fetch:
        _step("Fetch VTK source: skipped")
    elif source_dir.exists() and not workflow.force_fetch:
        _step("Fetch VTK source: already present")
        print(f"Source: {source_dir}")
    else:
        _step("Fetch VTK source")
        fetch_vtk(force=workflow.force_fetch, paths=paths, verbose=True)

    _step("Prepare target venv")
    sync_plan = make_venv_sync_plan(target_name=workflow.target, paths=paths)
    ensure_target_venv(sync_plan)
    print(f"Venv:   {sync_plan.venv_dir}")
    print(f"Python: {sync_plan.python_exe}")

    _step("Prepare VTK build plan")
    build_plan = make_vtk_build_plan(
        target_name=workflow.target,
        paths=paths,
        requested_backend=workflow.backend,
        requested_generator=workflow.generator,
        architecture=workflow.architecture,
        parallel=workflow.parallel,
    )
    print_vtk_build_plan(build_plan)

    _step("Configure VTK")
    configure_vtk(build_plan)
    _step("Build VTK")
    build_vtk(build_plan)
    _step("Install VTK SDK")
    install_vtk(build_plan)
    _step("Build VTK Python wheel")
    wheel_vtk(build_plan)

    _step("Sync target venv")
    sync_venv(sync_plan)

    if workflow.skip_validation:
        _step("Validation: skipped")
        return

    _step("Validate target runtime")
    validate_target_runtime(sync_plan)


def run_windows_phase1_or_raise(workflow: WindowsPhase1Workflow) -> None:
    try:
        run_windows_phase1_workflow(workflow)
    except (BuildPlanError, FetchError, SyncError) as exc:
        raise WorkflowError(str(exc)) from exc
