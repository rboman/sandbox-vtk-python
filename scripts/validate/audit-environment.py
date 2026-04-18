#!/usr/bin/env python
from __future__ import annotations

import argparse
import importlib.metadata
import importlib.util
import json
import os
import site
import sys
from pathlib import Path
from typing import Iterable


UNSAFE_ENV_VARS = (
    "PYTHONPATH",
    "PYTHONHOME",
    "PYTHONSTARTUP",
    "VIRTUAL_ENV",
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
    "PATH",
    "LD_LIBRARY_PATH",
    "DYLD_LIBRARY_PATH",
    "CONDA_PREFIX",
    "CONDA_DEFAULT_ENV",
)

PATH_LIKE_VARS = {
    "PYTHONPATH",
    "CMAKE_PREFIX_PATH",
    "INCLUDE",
    "LIB",
    "LIBRARY_PATH",
    "CPATH",
    "PATH",
    "LD_LIBRARY_PATH",
    "DYLD_LIBRARY_PATH",
}

SUSPICIOUS_TOKENS = (
    "vtk",
    "site-packages",
    ".venv",
    ".venvs",
    "conda",
    "python",
)


def normalize_path(value: str) -> str:
    return str(Path(value).expanduser().resolve(strict=False))


def split_paths(value: str) -> list[str]:
    return [part for part in value.split(os.pathsep) if part]


def path_is_within(candidate: str | Path, root: str | Path | None) -> bool:
    if not root:
        return False
    candidate_path = Path(candidate).resolve(strict=False)
    root_path = Path(root).resolve(strict=False)
    try:
        candidate_path.relative_to(root_path)
    except ValueError:
        return False
    return True


def safe_prefixes(target_venv: str | None, repo_root: str) -> list[str]:
    prefixes = [normalize_path(repo_root)]
    if target_venv:
        prefixes.append(normalize_path(target_venv))
    prefixes.append(normalize_path(sys.base_prefix))
    prefixes.append(normalize_path(sys.prefix))

    if os.name == "nt":
        prefixes.extend(
            [
                normalize_path(os.environ.get("SystemRoot", r"C:\Windows")),
                normalize_path(os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32")),
            ]
        )
    else:
        prefixes.extend(["/usr", "/bin", "/lib", "/lib64", "/usr/local"])

    return prefixes


def classify_path_entry(
    entry: str,
    *,
    target_venv: str | None,
    repo_root: str,
) -> tuple[str, str]:
    normalized = normalize_path(entry)
    lowered = normalized.lower()
    safe_roots = safe_prefixes(target_venv, repo_root)

    if any(path_is_within(normalized, safe_root) for safe_root in safe_roots):
        return "allowed", normalized

    if any(token in lowered for token in SUSPICIOUS_TOKENS):
        return "suspicious", normalized

    return "external", normalized


def package_info(name: str) -> dict[str, str | None]:
    spec = importlib.util.find_spec(name)
    origin = None if spec is None else spec.origin
    version = None
    try:
        version = importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        pass

    return {"name": name, "version": version, "origin": origin}


def inspect_environment(target_venv: str | None, target_sdk_root: str | None) -> dict[str, object]:
    repo_root = str(Path(__file__).resolve().parents[2])
    suspicious_vars: dict[str, object] = {}

    for name in UNSAFE_ENV_VARS:
        value = os.environ.get(name)
        if not value:
            continue
        if name in PATH_LIKE_VARS:
            classified = []
            for entry in split_paths(value):
                status, normalized = classify_path_entry(
                    entry,
                    target_venv=target_venv,
                    repo_root=repo_root,
                )
                classified.append({"status": status, "path": normalized})
            suspicious_vars[name] = classified
        else:
            suspicious_vars[name] = value

    sys_path = []
    for entry in sys.path:
        status, normalized = classify_path_entry(
            entry or ".",
            target_venv=target_venv,
            repo_root=repo_root,
        )
        sys_path.append({"status": status, "path": normalized})

    report = {
        "repo_root": repo_root,
        "target_venv": target_venv,
        "target_sdk_root": target_sdk_root,
        "python": {
            "executable": sys.executable,
            "prefix": sys.prefix,
            "base_prefix": sys.base_prefix,
            "usersite": site.getusersitepackages(),
            "pythonno_usersite": os.environ.get("PYTHONNOUSERSITE"),
        },
        "packages": {
            "vtk": package_info("vtk"),
            "pyvista": package_info("pyvista"),
            "vtkmodules": package_info("vtkmodules"),
        },
        "environment": suspicious_vars,
        "sys_path": sys_path,
    }
    return report


def iter_violations(report: dict[str, object]) -> Iterable[str]:
    target_venv = report.get("target_venv")
    usersite = report["python"]["usersite"]  # type: ignore[index]
    vtk_info = report["packages"]["vtk"]  # type: ignore[index]

    if report["python"]["pythonno_usersite"] != "1":  # type: ignore[index]
        yield "PYTHONNOUSERSITE must be set to 1."

    if usersite and str(usersite) in [entry["path"] for entry in report["sys_path"]]:  # type: ignore[index]
        yield f"Python user site is active in sys.path: {usersite}"

    vtk_origin = vtk_info.get("origin")
    if vtk_origin and target_venv and not path_is_within(vtk_origin, target_venv):
        yield f"vtk is resolved outside the target venv: {vtk_origin}"

    for name, value in report["environment"].items():  # type: ignore[index]
        if name not in PATH_LIKE_VARS:
            if name in {"PYTHONPATH", "CMAKE_PREFIX_PATH", "VTK_DIR", "CONDA_PREFIX", "CONDA_DEFAULT_ENV"}:
                yield f"Unsafe environment variable is set: {name}"
            continue
        for entry in value:
            if entry["status"] == "suspicious":
                yield f"{name} contains suspicious entry: {entry['path']}"

    for entry in report["sys_path"]:  # type: ignore[index]
        if entry["status"] == "suspicious":
            yield f"sys.path contains suspicious entry: {entry['path']}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("audit", "strict"), default="audit")
    parser.add_argument("--target-venv")
    parser.add_argument("--target-sdk-root")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = inspect_environment(args.target_venv, args.target_sdk_root)
    violations = list(iter_violations(report))

    payload = {"report": report, "violations": violations}

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"Python executable: {report['python']['executable']}")
        print(f"Python prefix:     {report['python']['prefix']}")
        vtk_version = report["packages"]["vtk"]["version"]
        vtk_origin = report["packages"]["vtk"]["origin"]
        print(f"vtk version:       {vtk_version or 'not importable'}")
        print(f"vtk origin:        {vtk_origin or 'not importable'}")
        if violations:
            print("Violations:")
            for violation in violations:
                print(f"  - {violation}")
        else:
            print("No violations detected.")

    if args.mode == "strict" and violations:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
