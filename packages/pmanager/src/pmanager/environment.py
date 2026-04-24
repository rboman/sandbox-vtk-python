from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Mapping


UNSAFE_ENV_VARS = (
    "PYTHONPATH",
    "PYTHONHOME",
    "PYTHONSTARTUP",
    "PIP_INDEX_URL",
    "PIP_EXTRA_INDEX_URL",
    "PIP_FIND_LINKS",
    "PIP_CONSTRAINT",
    "PIP_REQUIRE_VIRTUALENV",
    "CMAKE_PREFIX_PATH",
    "VTK_DIR",
    "CMAKE_TOOLCHAIN_FILE",
    "INCLUDE",
    "LIB",
    "LIBRARY_PATH",
    "CPATH",
    "LD_LIBRARY_PATH",
    "DYLD_LIBRARY_PATH",
    "CONDA_PREFIX",
    "CONDA_DEFAULT_ENV",
)

PATH_FILTER_TOKENS = (
    "vtk",
    "site-packages",
    ".venv",
    ".venvs",
    "conda",
)


def normalize_path(value: str | Path) -> Path:
    return Path(value).expanduser().resolve(strict=False)


def path_is_within(candidate: str | Path, root: str | Path | None) -> bool:
    if root is None:
        return False
    candidate_path = normalize_path(candidate)
    root_path = normalize_path(root)
    try:
        candidate_path.relative_to(root_path)
    except ValueError:
        return False
    return True


def active_venv_is_target(env: Mapping[str, str], target_venv: str | Path) -> bool:
    active = env.get("VIRTUAL_ENV")
    if not active:
        return False
    return normalize_path(active) == normalize_path(target_venv)


def unsafe_variables(
    env: Mapping[str, str] | None = None,
    *,
    target_venv: str | Path | None = None,
) -> dict[str, str]:
    source = os.environ if env is None else env
    unsafe = {name: value for name in UNSAFE_ENV_VARS if (value := source.get(name))}

    active_venv = source.get("VIRTUAL_ENV")
    if active_venv and (target_venv is None or not active_venv_is_target(source, target_venv)):
        unsafe["VIRTUAL_ENV"] = active_venv

    return unsafe


def sanitized_path(
    env: Mapping[str, str] | None = None,
    *,
    keep_system: bool = True,
) -> str:
    source = os.environ if env is None else env
    entries: list[str] = []

    if keep_system and os.name == "nt":
        system_root = source.get("SystemRoot", r"C:\Windows")
        for entry in (
            Path(system_root) / "System32",
            Path(system_root) / "System32" / "WindowsPowerShell" / "v1.0",
            Path(system_root),
        ):
            entries.append(str(entry))
    elif keep_system:
        entries.extend(["/usr/local/sbin", "/usr/local/bin", "/usr/sbin", "/usr/bin", "/sbin", "/bin"])

    for raw_entry in source.get("PATH", "").split(os.pathsep):
        if not raw_entry:
            continue
        entry = raw_entry.strip()
        lowered = entry.lower()
        if any(token in lowered for token in PATH_FILTER_TOKENS):
            continue
        if entry not in entries:
            entries.append(entry)

    return os.pathsep.join(entries)


def clean_environment(
    *,
    repo_root: str | Path,
    target: str | None = None,
    target_venv: str | Path | None = None,
    base: Mapping[str, str] | None = None,
) -> dict[str, str]:
    source = os.environ if base is None else base
    clean: dict[str, str] = {}

    for name in ("SystemRoot", "ComSpec", "WINDIR", "HOME", "USER", "LOGNAME", "SHELL", "TERM", "LANG"):
        if value := source.get(name):
            clean[name] = value

    clean["PATH"] = sanitized_path(source)
    clean["PYTHONNOUSERSITE"] = "1"
    clean["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
    clean["SANDBOX_VTK_PYTHON_REPO_ROOT"] = str(normalize_path(repo_root))
    if target:
        clean["SANDBOX_VTK_PYTHON_TARGET"] = target
    if target_venv is not None:
        clean["VIRTUAL_ENV"] = str(normalize_path(target_venv))

    return clean


def running_inside(target_venv: str | Path) -> bool:
    prefix_matches = normalize_path(sys.prefix) == normalize_path(target_venv)
    active_matches = active_venv_is_target(os.environ, target_venv)
    return prefix_matches or active_matches
