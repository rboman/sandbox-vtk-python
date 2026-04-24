#!/usr/bin/env python
from __future__ import annotations

import argparse
import os
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


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def default_target() -> str:
    if os.name == "nt":
        return "win-amd64-msvc2022-py310-release"
    return "linux-x86_64-gcc-py312-release"


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
        description="Create/select the target development venv and install pmanager editable."
    )
    parser.add_argument(
        "--target",
        default=default_target(),
        choices=sorted(PHASE1_TARGETS),
        help="Phase-1 target venv to prepare.",
    )
    parser.add_argument(
        "--no-install",
        action="store_true",
        help="Create/select the venv without installing pmanager.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root()
    target = args.target
    venv_dir = root / ".venvs" / target

    if not path_is_within(venv_dir, root / ".venvs"):
        raise RuntimeError(f"Refusing to prepare a venv outside the repo .venvs directory: {venv_dir}")

    ensure_not_recreating_active_venv(venv_dir)
    python_path = ensure_venv(venv_dir)

    if not args.no_install:
        install_dev_tools(python_path)
        install_pmanager_editable(python_path, root)

    print(f"Target: {target}")
    print(f"Venv:   {venv_dir}")
    print(f"Python: {python_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
