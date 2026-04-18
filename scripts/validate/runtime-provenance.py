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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--modules", nargs="*", default=["vtk", "pyvista", "codecpp"])
    parser.add_argument("--target-venv")
    parser.add_argument("--target-sdk-root")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    origins, errors = load_modules(args.modules)
    libraries = loaded_native_libraries()

    vtk_related = [
        lib
        for lib in libraries
        if "vtk" in lib.lower() or "codecpp" in lib.lower()
    ]

    violations = []
    if args.target_sdk_root:
        sdk_root = str(Path(args.target_sdk_root).resolve(strict=False))
        for lib in vtk_related:
            try:
                Path(lib).resolve(strict=False).relative_to(sdk_root)
            except ValueError:
                continue
            violations.append(f"Runtime library loaded from SDK tree: {lib}")

    if args.target_venv:
        venv_root = str(Path(args.target_venv).resolve(strict=False))
        for lib in vtk_related:
            try:
                Path(lib).resolve(strict=False).relative_to(venv_root)
            except ValueError:
                violations.append(f"Runtime library loaded outside target venv: {lib}")

    payload = {
        "module_origins": origins,
        "module_errors": errors,
        "vtk_related_libraries": vtk_related,
        "violations": violations,
    }

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        for name, origin in origins.items():
            error = errors.get(name)
            print(f"{name}: {origin or 'not found'}")
            if error:
                print(f"  error: {error}")
        if vtk_related:
            print("Loaded vtk-related libraries:")
            for lib in vtk_related:
                print(f"  - {lib}")
        if violations:
            print("Violations:")
            for violation in violations:
                print(f"  - {violation}")

    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
