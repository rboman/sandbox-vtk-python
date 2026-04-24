from __future__ import annotations

import sys


PHASE1_TARGETS = (
    "win-amd64-msvc2022-py310-release",
    "linux-x86_64-gcc-py312-release",
)


def _fallback(argv: list[str]) -> int:
    if not argv or argv in (["--help"], ["-h"]):
        print("Usage: pmanager [targets|fetch vtk|build vtk] [--help]")
        return 0

    if argv == ["targets"]:
        for target in PHASE1_TARGETS:
            print(target)
        return 0

    if argv in (["fetch", "vtk", "--help"], ["fetch", "vtk", "-h"]):
        print("Usage: pmanager fetch vtk [OPTIONS]")
        return 0

    if argv == ["fetch", "vtk"]:
        print(
            "Fetch recipe is registered for vtk 9.3.1, "
            "but Python fetch execution is not implemented in this tranche."
        )
        return 0

    if argv in (["build", "vtk", "--help"], ["build", "vtk", "-h"]):
        print("Usage: pmanager build vtk [OPTIONS]")
        return 0

    if argv == ["build", "vtk"]:
        print(
            "Build recipe is registered for vtk 9.3.1, "
            "but Python build execution is not implemented in this tranche."
        )
        return 0

    print(f"Unsupported fallback command: {' '.join(argv)}", file=sys.stderr)
    return 2


def main() -> int:
    try:
        from pmanager.cli import app
    except ModuleNotFoundError as exc:
        if exc.name != "typer":
            raise
        return _fallback(sys.argv[1:])

    app()
    return 0


raise SystemExit(main())
