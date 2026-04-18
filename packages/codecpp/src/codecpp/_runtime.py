from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

_DLL_HANDLES = []
_UNSAFE_ENV_VARS = (
    "PYTHONPATH",
    "PYTHONHOME",
    "CMAKE_PREFIX_PATH",
    "VTK_DIR",
    "LD_LIBRARY_PATH",
    "DYLD_LIBRARY_PATH",
    "CONDA_PREFIX",
    "CONDA_DEFAULT_ENV",
)


def _inside_virtual_environment() -> bool:
    return sys.prefix != sys.base_prefix or bool(os.environ.get("VIRTUAL_ENV"))


def _vtkmodules_dir() -> Path | None:
    spec = importlib.util.find_spec("vtkmodules")
    if spec is None:
        return None
    if spec.submodule_search_locations:
        return Path(next(iter(spec.submodule_search_locations))).resolve(strict=False)
    if spec.origin:
        return Path(spec.origin).resolve(strict=False).parent
    return None


def _iter_runtime_candidates(package_dir: Path) -> list[Path]:
    site_packages = package_dir.parent
    candidates = [
        package_dir,
        site_packages,
        site_packages / "vtk.libs",
        site_packages / "vtkmodules",
        package_dir / ".libs",
    ]
    candidates.extend(sorted(site_packages.glob("*.libs")))

    unique: list[Path] = []
    for candidate in candidates:
        resolved = candidate.resolve(strict=False)
        if resolved.exists() and resolved not in unique:
            unique.append(resolved)
    return unique


def _environment_hints() -> dict[str, str]:
    hints = {}
    for name in _UNSAFE_ENV_VARS:
        value = os.environ.get(name)
        if value:
            hints[name] = value
    return hints


def describe_runtime() -> dict[str, object]:
    package_dir = _vtkmodules_dir()
    candidates = []
    dlls = []
    if package_dir is not None:
        candidates = [str(path) for path in _iter_runtime_candidates(package_dir)]
        dlls = [
            str(path)
            for directory in _iter_runtime_candidates(package_dir)
            for path in sorted(directory.glob("vtk*.dll"))
        ]

    return {
        "python_executable": sys.executable,
        "prefix": sys.prefix,
        "base_prefix": sys.base_prefix,
        "inside_virtual_environment": _inside_virtual_environment(),
        "vtkmodules_dir": None if package_dir is None else str(package_dir),
        "runtime_candidates": candidates,
        "vtk_dlls": dlls,
        "environment_hints": _environment_hints(),
    }


def prepare_runtime(*, strict: bool = False) -> dict[str, object]:
    details = describe_runtime()

    if os.name != "nt":
        return details

    if not details["inside_virtual_environment"]:
        if strict:
            raise RuntimeError(
                "codecpp must run inside the target venv. "
                "Importing from a global Python installation is unsupported."
            )
        return details

    package_dir = _vtkmodules_dir()
    if package_dir is None:
        if strict:
            raise RuntimeError(
                "Unable to locate 'vtkmodules' in the active interpreter. "
                "Install the repo-managed vtk wheel into the target venv first."
            )
        return details

    for candidate in _iter_runtime_candidates(package_dir):
        handle = os.add_dll_directory(str(candidate))
        _DLL_HANDLES.append(handle)

    return details
