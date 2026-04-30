from __future__ import annotations

"""CLI entrypoint with a small fallback mode when Typer is unavailable.

The fallback keeps basic help and discovery commands usable in minimal setups.
"""

import sys


BASELINE_TARGETS = (
    "win-amd64-msvc2022-py310-release",
    "linux-x86_64-gcc-py312-release",
)


def _fallback(argv: list[str]) -> int:
    """Handle a minimal subset of commands without Typer dependency."""
    if not argv or argv in (["--help"], ["-h"]):
        print("Usage: pmanager [targets|fetch vtk|build vtk|sync venv|workflow windows|workflow linux] [--help]")
        return 0

    if argv == ["targets"]:
        for target in BASELINE_TARGETS:
            print(target)
        return 0

    if argv in (["fetch", "vtk", "--help"], ["fetch", "vtk", "-h"]):
        print("Usage: pmanager fetch vtk [OPTIONS]")
        return 0

    if argv == ["fetch", "vtk"]:
        print(
            "Fetch recipe is registered for vtk 9.3.1. "
            "Install the pmanager tooling venv dependencies to run the full Typer CLI."
        )
        return 0

    if argv in (["build", "vtk", "--help"], ["build", "vtk", "-h"]):
        print("Usage: pmanager build vtk [OPTIONS]")
        print("Options include --configure, --build, --install, and --wheel when Typer is installed.")
        return 0

    if argv == ["build", "vtk"]:
        print(
            "Build recipe is registered for vtk 9.3.1. "
            "Install the pmanager tooling venv dependencies to run the full Typer CLI."
        )
        return 0

    if argv in (["sync", "venv", "--help"], ["sync", "venv", "-h"]):
        print("Usage: pmanager sync venv [OPTIONS]")
        return 0

    if argv in (["workflow", "windows", "--help"], ["workflow", "windows", "-h"]):
        print("Usage: pmanager workflow windows [OPTIONS]")
        return 0

    if argv in (["workflow", "linux", "--help"], ["workflow", "linux", "-h"]):
        print("Usage: pmanager workflow linux [OPTIONS]")
        return 0

    print(f"Unsupported fallback command: {' '.join(argv)}", file=sys.stderr)
    return 2


def main() -> int:
    """Run Typer app when possible, otherwise use fallback command handler."""
    try:
        from pmanager.cli import app
    except ModuleNotFoundError as exc:
        if exc.name != "typer":
            raise
        return _fallback(sys.argv[1:])

    app()
    return 0


raise SystemExit(main())
