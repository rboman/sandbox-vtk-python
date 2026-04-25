from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path

from pmanager.cmake import generator_backend, read_cmake_cache_generator
from pmanager.libraries import get_library
from pmanager.paths import ProjectPaths
from pmanager.process import CommandResult, format_command, run_command
from pmanager.targets import Target, get_target


class BuildPlanError(RuntimeError):
    pass


@dataclass(frozen=True)
class BuildChoice:
    backend: str
    generator: str
    ninja_path: str | None = None
    existing_generator: str | None = None


@dataclass(frozen=True)
class VtkBuildPlan:
    target: Target
    source_dir: Path
    build_dir: Path
    install_dir: Path
    wheelhouse_dir: Path
    python_exe: Path
    manifest_path: Path
    build_choice: BuildChoice
    configure_command: list[str]
    build_command: list[str]
    install_command: list[str]
    wheel_command: list[str]


VTK_CMAKE_OPTIONS = (
    "-DCMAKE_BUILD_TYPE=Release",
    "-DVTK_WRAP_PYTHON=ON",
    "-DVTK_WHEEL_BUILD=ON",
    "-DVTK_GROUP_ENABLE_Qt=WANT",
    "-DVTK_MODULE_ENABLE_VTK_GUISupportQtQuick=DONT_WANT",
    "-DVTK_GROUP_ENABLE_Rendering=WANT",
    "-DVTK_GROUP_ENABLE_Views=WANT",
    "-DVTK_GROUP_ENABLE_StandAlone=WANT",
    "-DVTK_MODULE_ENABLE_VTK_RenderingOpenGL2=WANT",
    "-DVTK_MODULE_ENABLE_VTK_InteractionStyle=WANT",
    "-DVTK_MODULE_ENABLE_VTK_RenderingMatplotlib=WANT",
)


def default_python_for_target(paths: ProjectPaths, target: Target) -> Path:
    venv_dir = paths.venv_dir(target.name)
    if target.os_name == "win":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def resolve_build_choice(
    *,
    target: Target,
    build_dir: Path,
    requested_backend: str = "auto",
    requested_generator: str | None = None,
) -> BuildChoice:
    existing_generator = read_cmake_cache_generator(build_dir)

    if requested_generator:
        backend = generator_backend(requested_generator)
        if existing_generator and existing_generator != requested_generator:
            raise BuildPlanError(
                f"Build directory is already configured for {existing_generator}; "
                f"refusing to switch to {requested_generator}."
            )
        return BuildChoice(
            backend=backend,
            generator=requested_generator,
            existing_generator=existing_generator,
        )

    if existing_generator:
        existing_backend = generator_backend(existing_generator)
        if requested_backend != "auto" and requested_backend != existing_backend:
            raise BuildPlanError(
                f"Build directory is already configured for {existing_generator}; "
                f"refusing backend switch to {requested_backend}."
            )
        return BuildChoice(
            backend=existing_backend,
            generator=existing_generator,
            existing_generator=existing_generator,
        )

    if requested_backend == "vs":
        return BuildChoice(backend="vs", generator="Visual Studio 17 2022")

    if requested_backend == "ninja":
        ninja_path = shutil.which("ninja")
        if not ninja_path:
            raise BuildPlanError("Build backend 'ninja' was requested, but ninja was not found in PATH.")
        return BuildChoice(backend="ninja", generator="Ninja", ninja_path=ninja_path)

    if target.os_name == "win":
        ninja_path = shutil.which("ninja")
        if ninja_path:
            return BuildChoice(backend="ninja", generator="Ninja", ninja_path=ninja_path)
        return BuildChoice(backend="vs", generator="Visual Studio 17 2022")

    return BuildChoice(backend="ninja", generator="Ninja", ninja_path=shutil.which("ninja"))


def make_vtk_build_plan(
    *,
    target_name: str,
    paths: ProjectPaths | None = None,
    python_exe: str | Path | None = None,
    requested_backend: str = "auto",
    requested_generator: str | None = None,
    architecture: str = "x64",
    parallel: int | None = None,
) -> VtkBuildPlan:
    paths = paths or ProjectPaths.discover()
    target = get_target(target_name)
    library = get_library("vtk")

    source_dir = paths.source_root / library.source_dir_name
    build_dir = paths.build_root / library.source_dir_name / target.name
    install_dir = paths.install_root / library.source_dir_name / target.name / "sdk"
    wheelhouse_dir = paths.wheelhouse_root / library.source_dir_name / target.name
    manifest_path = build_dir / "build-manifest.json"
    resolved_python = Path(python_exe) if python_exe else default_python_for_target(paths, target)
    build_choice = resolve_build_choice(
        target=target,
        build_dir=build_dir,
        requested_backend=requested_backend,
        requested_generator=requested_generator,
    )
    parallel_jobs = parallel if parallel and parallel > 0 else os.cpu_count() or 1

    configure_command = [
        "cmake",
        "-S",
        str(source_dir),
        "-B",
        str(build_dir),
        "-G",
        build_choice.generator,
        f"-DCMAKE_INSTALL_PREFIX={install_dir}",
        f"-DPython3_EXECUTABLE={resolved_python}",
        *VTK_CMAKE_OPTIONS,
    ]

    if build_choice.backend == "vs":
        configure_command.extend(["-A", architecture])
    if build_choice.backend == "ninja" and build_choice.ninja_path:
        configure_command.append(f"-DCMAKE_MAKE_PROGRAM={build_choice.ninja_path}")

    build_command = ["cmake", "--build", str(build_dir), "--parallel", str(parallel_jobs)]
    install_command = ["cmake", "--install", str(build_dir)]
    if build_choice.backend == "vs":
        build_command.extend(["--config", "Release"])
        install_command.extend(["--config", "Release"])

    wheel_command = [
        str(resolved_python),
        "setup.py",
        "bdist_wheel",
        "--dist-dir",
        str(wheelhouse_dir),
    ]

    return VtkBuildPlan(
        target=target,
        source_dir=source_dir,
        build_dir=build_dir,
        install_dir=install_dir,
        wheelhouse_dir=wheelhouse_dir,
        python_exe=resolved_python,
        manifest_path=manifest_path,
        build_choice=build_choice,
        configure_command=configure_command,
        build_command=build_command,
        install_command=install_command,
        wheel_command=wheel_command,
    )


def print_vtk_build_plan(plan: VtkBuildPlan) -> None:
    print(f"Target:      {plan.target.name}")
    print(f"Source:      {plan.source_dir}")
    print(f"Build:       {plan.build_dir}")
    print(f"SDK install: {plan.install_dir}")
    print(f"Wheelhouse:  {plan.wheelhouse_dir}")
    print(f"Python:      {plan.python_exe}")
    print(f"Generator:   {plan.build_choice.generator}")
    print(f"Backend:     {plan.build_choice.backend}")
    if plan.build_choice.existing_generator:
        print(f"Existing:    {plan.build_choice.existing_generator}")
    if plan.build_choice.ninja_path:
        print(f"Ninja:       {plan.build_choice.ninja_path}")
    print()
    print("Configure:")
    print(f"  {format_command(plan.configure_command)}")
    print("Build:")
    print(f"  {format_command(plan.build_command)}")
    print("Install:")
    print(f"  {format_command(plan.install_command)}")
    print("Wheel:")
    print(f"  cd {plan.build_dir}")
    print(f"  {format_command(plan.wheel_command)}")


def _ensure_vtk_source_exists(plan: VtkBuildPlan) -> None:
    if not plan.source_dir.exists():
        raise BuildPlanError(
            f"VTK source directory does not exist: {plan.source_dir}. "
            "Run 'pmanager fetch vtk' first."
        )


def _ensure_compiler_environment(plan: VtkBuildPlan) -> None:
    if plan.target.os_name != "win" or plan.build_choice.backend != "ninja":
        return

    if shutil.which("cl") or os.environ.get("CC") or os.environ.get("CXX"):
        return

    raise BuildPlanError(
        "Ninja was selected, but this cmd.exe session does not look like an MSVC command-line "
        "build environment. For the current Python-first workflow, open an 'x64 Native Tools "
        "Command Prompt for VS 2022', activate .venvs\\pmanager-dev\\Scripts\\activate.bat, "
        "then rerun the same pmanager command. Alternatively, force the Visual Studio "
        "generator with '--backend vs'."
    )


def configure_vtk(plan: VtkBuildPlan) -> CommandResult:
    _ensure_vtk_source_exists(plan)
    _ensure_compiler_environment(plan)
    plan.build_dir.mkdir(parents=True, exist_ok=True)
    plan.install_dir.mkdir(parents=True, exist_ok=True)
    plan.wheelhouse_dir.mkdir(parents=True, exist_ok=True)
    return run_command(plan.configure_command)


def build_vtk(plan: VtkBuildPlan) -> CommandResult:
    cache_path = plan.build_dir / "CMakeCache.txt"
    if not cache_path.exists():
        raise BuildPlanError(
            f"CMake cache does not exist: {cache_path}. "
            "Run 'pmanager build vtk --configure' before '--build'."
        )
    return run_command(plan.build_command)
