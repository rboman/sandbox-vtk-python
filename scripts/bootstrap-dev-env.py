#!/usr/bin/env python
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import venv
from pathlib import Path


DEV_REQUIREMENTS = (
    "pip",
    "setuptools",
    "wheel",
    "typer>=0.12,<1.0",
    "pytest",
)

PHASE1_TARGETS = {
    "win-amd64-msvc2022-py310-release": {
        "platform": "win32",
        "python": "py310",
    },
    "linux-x86_64-gcc-py312-release": {
        "platform": "linux",
        "python": "py312",
    },
}

DEFAULT_TOOL_VENV = "pmanager-dev"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def venv_python(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def path_is_within(candidate: Path, root: Path) -> bool:
    try:
        candidate.resolve(strict=False).relative_to(root.resolve(strict=False))
    except ValueError:
        return False
    return True


def ensure_not_recreating_active_venv(venv_dir: Path) -> None:
    active_venv = os.environ.get("VIRTUAL_ENV")
    if not active_venv:
        return
    if Path(active_venv).resolve(strict=False) == venv_dir.resolve(strict=False):
        return

    # A foreign active venv is allowed to run the bootstrap, but it must be explicit.
    print(
        f"warning: bootstrap is running from a different active venv: {active_venv}",
        file=sys.stderr,
    )


def remove_venv(venv_dir: Path, venvs_root: Path) -> None:
    resolved_venv = venv_dir.resolve(strict=False)
    resolved_root = venvs_root.resolve(strict=False)
    if not path_is_within(resolved_venv, resolved_root):
        raise RuntimeError(f"Refusing to remove a venv outside {resolved_root}: {resolved_venv}")

    active_venv = os.environ.get("VIRTUAL_ENV")
    if active_venv and Path(active_venv).resolve(strict=False) == resolved_venv:
        raise RuntimeError(f"Refusing to remove the active venv: {resolved_venv}")

    if resolved_venv.exists():
        shutil.rmtree(resolved_venv)


def ensure_venv(venv_dir: Path) -> Path:
    python_path = venv_python(venv_dir)
    if not python_path.exists():
        builder = venv.EnvBuilder(with_pip=True)
        builder.create(venv_dir)

    if not python_path.exists():
        raise RuntimeError(f"Unable to locate venv Python after creation: {python_path}")
    return python_path


def run(command: list[str]) -> None:
    completed = subprocess.run(command, check=False)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def install_dev_tools(python_path: Path) -> None:
    run(
        [
            str(python_path),
            "-m",
            "pip",
            "install",
            "--upgrade",
            *DEV_REQUIREMENTS,
        ]
    )


def install_pmanager_editable(python_path: Path, root: Path) -> None:
    package_dir = root / "packages" / "pmanager"
    run([str(python_path), "-m", "pip", "install", "--upgrade", "-e", str(package_dir)])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create/select the pmanager development venv and install pmanager editable."
    )
    parser.add_argument(
        "--target",
        choices=sorted(PHASE1_TARGETS),
        help=(
            "Deprecated transition option: prepare .venvs/<target> instead of "
            f".venvs/{DEFAULT_TOOL_VENV}."
        ),
    )
    parser.add_argument(
        "--venv-name",
        default=DEFAULT_TOOL_VENV,
        help="Tooling venv name under .venvs/.",
    )
    parser.add_argument(
        "--no-install",
        action="store_true",
        help="Create/select the venv without installing pmanager.",
    )
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Delete and recreate the selected venv. Refuses to remove the active venv.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root()
    venv_name = args.target or args.venv_name
    venvs_root = root / ".venvs"
    venv_dir = venvs_root / venv_name

    if not path_is_within(venv_dir, venvs_root):
        raise RuntimeError(f"Refusing to prepare a venv outside the repo .venvs directory: {venv_dir}")

    ensure_not_recreating_active_venv(venv_dir)
    if args.recreate:
        remove_venv(venv_dir, venvs_root)

    python_path = ensure_venv(venv_dir)

    if not args.no_install:
        install_dev_tools(python_path)
        install_pmanager_editable(python_path, root)

    print(f"Venv name: {venv_name}")
    print(f"Venv:   {venv_dir}")
    print(f"Python: {python_path}")
    if args.target:
        print("Note: --target is transitional; prefer the default pmanager-dev tooling venv.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
