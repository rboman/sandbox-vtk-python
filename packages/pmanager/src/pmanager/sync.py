from __future__ import annotations

import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from pmanager.environment import PATH_FILTER_TOKENS, UNSAFE_ENV_VARS, running_inside, strict_sanitized_path
from pmanager.libraries import get_library
from pmanager.paths import ProjectPaths
from pmanager.process import CommandResult, run_command, run_command_text
from pmanager.targets import Target, get_target


class SyncError(RuntimeError):
    pass


@dataclass(frozen=True)
class VenvSyncPlan:
    target: Target
    venv_dir: Path
    python_exe: Path
    creator_python: str
    constraints_file: Path
    wheelhouse_dir: Path
    sdk_dir: Path
    vtk_build_dir: Path
    audit_script: Path
    tmp_dir: Path
    vtk_constraint_file: Path
    codecpp_dir: Path
    codepy_dir: Path
    pmanager_dir: Path


def default_python_for_venv(venv_dir: Path, target: Target) -> Path:
    if target.os_name == "win":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def make_venv_sync_plan(
    *,
    target_name: str,
    paths: ProjectPaths | None = None,
    python_exe: str | None = None,
    constraints_file: str | Path | None = None,
) -> VenvSyncPlan:
    paths = paths or ProjectPaths.discover()
    target = get_target(target_name)
    library = get_library("vtk")
    venv_dir = paths.venv_dir(target.name)
    resolved_constraints = Path(constraints_file) if constraints_file else paths.constraints_file(target.python_tag)

    return VenvSyncPlan(
        target=target,
        venv_dir=venv_dir,
        python_exe=default_python_for_venv(venv_dir, target),
        creator_python=python_exe or sys.executable,
        constraints_file=resolved_constraints,
        wheelhouse_dir=paths.wheelhouse_root / library.source_dir_name / target.name,
        sdk_dir=paths.install_root / library.source_dir_name / target.name / "sdk",
        vtk_build_dir=paths.build_root / library.source_dir_name / target.name,
        audit_script=paths.root / "scripts" / "validate" / "audit-environment.py",
        tmp_dir=paths.root / ".tmp",
        vtk_constraint_file=paths.root / ".tmp" / f"vtk-constraint-{target.name}.txt",
        codecpp_dir=paths.packages_dir / "codecpp",
        codepy_dir=paths.packages_dir / "codepy",
        pmanager_dir=paths.packages_dir / "pmanager",
    )


def target_command_env(plan: VenvSyncPlan) -> dict[str, str]:
    env = dict(os.environ)
    # Remove all unsafe variables that may point to system or user-installed libraries
    for name in UNSAFE_ENV_VARS:
        env.pop(name, None)

    # Use strict whitelist PATH for venv sync to ensure clean audit
    scripts_dir = plan.python_exe.parent
    env["PATH"] = strict_sanitized_path(venv_bin_dir=scripts_dir)
    env["VIRTUAL_ENV"] = str(plan.venv_dir)
    env["PYTHONNOUSERSITE"] = "1"
    env["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
    return env


def codecpp_build_env(plan: VenvSyncPlan) -> dict[str, str]:
    env = target_command_env(plan)
    vtk_cmake_dir = resolve_vtk_cmake_dir(plan)
    env["PATH"] = build_tool_path(env)
    env["VTK_DIR"] = str(vtk_cmake_dir)
    env["CMAKE_PREFIX_PATH"] = os.pathsep.join([str(vtk_cmake_dir), str(plan.sdk_dir), str(plan.vtk_build_dir)])
    return env


def build_tool_path(env: Mapping[str, str]) -> str:
    """Extend a sanitized PATH with externally installed build tools when required."""
    entries = [entry for entry in env.get("PATH", "").split(os.pathsep) if entry]
    existing = set(entries)

    # Some systems install SWIG outside standard system PATH entries (for example /opt/swig/bin).
    # Add only the executable parent directory, not broad runtime/library locations.
    for executable in ("swig",):
        resolved = shutil.which(executable)
        if not resolved:
            continue
        parent = str(Path(resolved).parent)
        if parent not in existing:
            entries.append(parent)
            existing.add(parent)

    return os.pathsep.join(entries)


def resolve_vtk_cmake_dir(plan: VenvSyncPlan) -> Path:
    candidates: list[Path] = [
        plan.sdk_dir / "lib" / "cmake" / "vtk-9.3",
        plan.sdk_dir,
        plan.vtk_build_dir,
    ]

    for base in candidates:
        if not base.exists():
            continue
        if (base / "VTKConfig.cmake").exists() or (base / "vtk-config.cmake").exists():
            return base

    for base in candidates:
        if not base.exists():
            continue
        for pattern in ("VTKConfig.cmake", "vtk-config.cmake"):
            matches = sorted(base.rglob(pattern))
            if matches:
                return matches[0].parent

    raise SyncError(
        "Unable to find VTK CMake package files (VTKConfig.cmake or vtk-config.cmake) "
        f"under SDK '{plan.sdk_dir}' or build tree '{plan.vtk_build_dir}'. "
        "Run 'pmanager workflow windows-phase1 --backend vs --parallel <N>' or rerun install after configure/build."
    )


def ensure_target_venv(plan: VenvSyncPlan) -> None:
    if plan.python_exe.exists():
        return
    if running_inside(plan.venv_dir):
        raise SyncError(f"Refusing to create active target venv in-place: {plan.venv_dir}")
    plan.venv_dir.parent.mkdir(parents=True, exist_ok=True)
    run_command([plan.creator_python, "-m", "venv", str(plan.venv_dir)])


def find_vtk_wheel(wheelhouse_dir: Path) -> Path:
    if not wheelhouse_dir.exists():
        raise SyncError(f"Wheelhouse does not exist: {wheelhouse_dir}")
    wheels = sorted(
        wheelhouse_dir.glob("vtk-*.whl"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not wheels:
        raise SyncError(f"No vtk wheel was found in {wheelhouse_dir}. Build VTK and generate the wheel first.")
    return wheels[0]


def installed_vtk_version(plan: VenvSyncPlan, env: Mapping[str, str]) -> str:
    version = run_command_text(
        [
            str(plan.python_exe),
            "-c",
            "import importlib.metadata; print(importlib.metadata.version('vtk'))",
        ],
        env=env,
    )
    if not version:
        raise SyncError("Unable to determine installed vtk version in the target venv.")
    return version.strip()


def vtk_modules_dir(plan: VenvSyncPlan, env: Mapping[str, str]) -> Path:
    location = run_command_text(
        [
            str(plan.python_exe),
            "-c",
            "import importlib.util; "
            "spec = importlib.util.find_spec('vtkmodules'); "
            "print(next(iter(spec.submodule_search_locations)) if spec and spec.submodule_search_locations else '')",
        ],
        env=env,
    )
    if not location:
        raise SyncError("Unable to determine the vtkmodules package location in the target venv.")
    modules_dir = Path(location)
    if not modules_dir.exists():
        raise SyncError(f"The vtk wheel does not appear to be installed correctly: missing {modules_dir}")
    return modules_dir


def vtk_abi_suffix(vtk_version: str) -> str:
    parts = vtk_version.split(".")
    if len(parts) < 2 or not parts[0].isdigit() or not parts[1].isdigit():
        raise SyncError(f"Unable to derive the VTK ABI suffix from version '{vtk_version}'.")
    return f"{parts[0]}.{parts[1]}"


def find_qt_bin_dir(env: Mapping[str, str] | None = None) -> Path | None:
    source = os.environ if env is None else env
    candidates: list[Path] = []
    for name in ("QTDIR", "QT_DIR", "Qt5_DIR", "Qt6_DIR"):
        if value := source.get(name):
            candidates.extend([Path(value) / "bin", Path(value)])

    if qmake := shutil.which("qmake", path=source.get("PATH")):
        candidates.append(Path(qmake).parent)
    candidates.append(Path(r"C:\local\qt\bin"))

    for candidate in candidates:
        if candidate.exists() and any(candidate.glob("Qt*Core*.dll")):
            return candidate.resolve()
    return None


def write_vtk_build_paths(vtkmodules_dir: Path, additional_paths: list[Path]) -> Path:
    existing = []
    for path in additional_paths:
        if path.exists():
            resolved = path.resolve()
            if resolved not in existing:
                existing.append(resolved)

    lines = [
        "# Auto-generated by pmanager sync venv",
        "paths=[",
        *(f"    r'{str(path)}'," for path in existing),
        "]",
    ]
    build_paths = vtkmodules_dir / "_build_paths.py"
    build_paths.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return build_paths


def stage_vtk_runtime_windows(plan: VenvSyncPlan, vtk_version: str, env: Mapping[str, str]) -> None:
    if plan.target.os_name != "win":
        return

    sdk_bin_dir = plan.sdk_dir / "bin"
    if not sdk_bin_dir.exists():
        raise SyncError(f"Expected VTK SDK runtime directory was not found: {sdk_bin_dir}")

    dlls = sorted(sdk_bin_dir.glob("*.dll"))
    if not dlls:
        raise SyncError(f"No VTK DLLs were found in {sdk_bin_dir}")

    modules_dir = vtk_modules_dir(plan, env)
    runtime_bin_dir = modules_dir.parent / "bin"
    runtime_bin_dir.mkdir(parents=True, exist_ok=True)
    for dll in dlls:
        shutil.copy2(dll, runtime_bin_dir / dll.name)

    suffix = vtk_abi_suffix(vtk_version)
    for dll in dlls:
        if dll.stem.endswith(f"-{suffix}"):
            continue
        alias = runtime_bin_dir / f"{dll.stem}-{suffix}{dll.suffix}"
        if not alias.exists():
            shutil.copy2(runtime_bin_dir / dll.name, alias)

    qt_bin = find_qt_bin_dir(env)
    write_vtk_build_paths(modules_dir, [qt_bin] if qt_bin else [])


def write_vtk_constraint(plan: VenvSyncPlan, vtk_version: str) -> Path:
    plan.tmp_dir.mkdir(parents=True, exist_ok=True)
    plan.vtk_constraint_file.write_text(f"vtk==={vtk_version}\n", encoding="utf-8")
    return plan.vtk_constraint_file


def sync_venv(plan: VenvSyncPlan, *, no_index: bool = False, install_local_packages: bool = True) -> None:
    ensure_target_venv(plan)
    if not plan.constraints_file.exists():
        raise SyncError(f"Constraints file does not exist: {plan.constraints_file}")

    env = target_command_env(plan)
    vtk_wheel = find_vtk_wheel(plan.wheelhouse_dir)

    run_command(
        [
            str(plan.python_exe),
            str(plan.audit_script),
            "--mode",
            "strict",
            "--target-venv",
            str(plan.venv_dir),
        ],
        env=env,
    )
    run_command([str(plan.python_exe), "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"], env=env)
    run_command([str(plan.python_exe), "-m", "pip", "install", "--no-deps", "--force-reinstall", str(vtk_wheel)], env=env)

    vtk_version = installed_vtk_version(plan, env)
    stage_vtk_runtime_windows(plan, vtk_version, env)
    vtk_constraint = write_vtk_constraint(plan, vtk_version)

    pyvista_command = [
        str(plan.python_exe),
        "-m",
        "pip",
        "install",
        "--constraint",
        str(plan.constraints_file),
        "--constraint",
        str(vtk_constraint),
        "pyvista",
    ]
    if no_index:
        pyvista_command[4:4] = ["--no-index", "--find-links", str(plan.wheelhouse_dir)]
    run_command(pyvista_command, env=env)

    if not install_local_packages:
        return

    run_command([str(plan.python_exe), "-m", "pip", "install", str(plan.codecpp_dir)], env=codecpp_build_env(plan))
    run_command([str(plan.python_exe), "-m", "pip", "install", "-e", str(plan.codepy_dir)], env=env)
    run_command([str(plan.python_exe), "-m", "pip", "install", "-e", str(plan.pmanager_dir)], env=env)
