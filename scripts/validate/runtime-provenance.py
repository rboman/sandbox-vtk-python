#!/usr/bin/env python
from __future__ import annotations

import argparse
import ctypes
import importlib
import importlib.util
import json
import os
import sys
from pathlib import Path


def module_origin(name: str) -> str | None:
    spec = importlib.util.find_spec(name)
    return None if spec is None else spec.origin


def load_modules(module_names: list[str]) -> tuple[dict[str, str | None], dict[str, str]]:
    origins: dict[str, str | None] = {}
    errors: dict[str, str] = {}

    for name in module_names:
        try:
            importlib.import_module(name)
        except Exception as exc:  # pragma: no cover - best effort diagnostic
            errors[name] = f"{type(exc).__name__}: {exc}"
        origins[name] = module_origin(name)

    return origins, errors


def loaded_native_libraries() -> list[str]:
    if sys.platform.startswith("linux"):
        libs = set()
        maps_path = Path("/proc/self/maps")
        if not maps_path.exists():
            return []
        for line in maps_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            parts = line.split()
            if len(parts) >= 6 and parts[-1].startswith("/"):
                libs.add(parts[-1])
        return sorted(libs)

    if os.name == "nt":
        psapi = ctypes.WinDLL("Psapi.dll")
        kernel32 = ctypes.WinDLL("Kernel32.dll")

        LIST_MODULES_ALL = 0x03
        HMODULE_ARRAY = ctypes.c_void_p * 2048
        modules = HMODULE_ARRAY()
        needed = ctypes.c_ulong()
        process = kernel32.GetCurrentProcess()

        if not psapi.EnumProcessModulesEx(
            process,
            ctypes.byref(modules),
            ctypes.sizeof(modules),
            ctypes.byref(needed),
            LIST_MODULES_ALL,
        ):
            return []

        count = needed.value // ctypes.sizeof(ctypes.c_void_p)
        paths = []
        buffer = ctypes.create_unicode_buffer(32768)
        for index in range(count):
            if kernel32.GetModuleFileNameW(modules[index], buffer, len(buffer)):
                paths.append(buffer.value)
        return sorted(set(paths))

    return []


def normalize_path(value: str | Path) -> str:
    return str(Path(value).resolve(strict=False))


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


def summarize_libraries(
    libraries: list[str],
    *,
    target_venv: str | None,
    target_sdk_root: str | None,
) -> dict[str, object]:
    target_venv = None if not target_venv else normalize_path(target_venv)
    target_sdk_root = None if not target_sdk_root else normalize_path(target_sdk_root)

    vtk_related = [
        normalize_path(lib)
        for lib in libraries
        if "vtk" in lib.lower() or "codecpp" in lib.lower()
    ]

    inside_venv = [lib for lib in vtk_related if path_is_within(lib, target_venv)]
    inside_sdk = [lib for lib in vtk_related if path_is_within(lib, target_sdk_root)]
    outside_venv = [lib for lib in vtk_related if target_venv and not path_is_within(lib, target_venv)]

    violations = [f"Runtime library loaded from SDK tree: {lib}" for lib in inside_sdk]
    violations.extend(f"Runtime library loaded outside target venv: {lib}" for lib in outside_venv)

    return {
        "vtk_related_libraries": vtk_related,
        "inside_target_venv": inside_venv,
        "inside_target_sdk": inside_sdk,
        "outside_target_venv": outside_venv,
        "violations": violations,
        "ok": not violations,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--modules", nargs="*", default=["vtk", "pyvista", "codecpp"])
    parser.add_argument("--target-venv")
    parser.add_argument("--target-sdk-root")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    origins, errors = load_modules(args.modules)
    libraries = loaded_native_libraries()
    summary = summarize_libraries(
        libraries,
        target_venv=args.target_venv,
        target_sdk_root=args.target_sdk_root,
    )

    payload = {
        "module_origins": origins,
        "module_errors": errors,
        **summary,
    }

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        for name, origin in origins.items():
            error = errors.get(name)
            print(f"{name}: {origin or 'not found'}")
            if error:
                print(f"  error: {error}")
        if summary["vtk_related_libraries"]:
            print("Loaded vtk-related libraries:")
            for lib in summary["vtk_related_libraries"]:
                print(f"  - {lib}")
            print(f"Summary: {len(summary['inside_target_venv'])} inside target venv, {len(summary['outside_target_venv'])} outside target venv.")
        if summary["ok"]:
            print("Runtime provenance OK: vtk/codecpp native libraries are resolved from the target venv and not from the SDK tree.")
        if summary["violations"]:
            print("Violations:")
            for violation in summary["violations"]:
                print(f"  - {violation}")

    return 1 if summary["violations"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
