#!/usr/bin/env python
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import venv
from pathlib import Path


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


def pmanager_points_to_checkout(python_path: Path, root: Path) -> bool:
    probe = (
        "import importlib.util; "
        "spec = importlib.util.find_spec('pmanager'); "
        "print(spec.origin if spec and spec.origin else '')"
    )
    completed = subprocess.run(
        [str(python_path), "-c", probe],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return False

    origin = completed.stdout.strip()
    if not origin:
        return False

    checkout_src = root / "packages" / "pmanager" / "src"
    return path_is_within(Path(origin), checkout_src)


def query_venv_path(python_path: Path, key: str) -> Path:
    probe = (
        "import sysconfig; "
        f"print(sysconfig.get_path({key!r}))"
    )
    completed = subprocess.run(
        [str(python_path), "-c", probe],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0 or not completed.stdout.strip():
        raise RuntimeError(f"Unable to determine venv sysconfig path: {key}")
    return Path(completed.stdout.strip())


def write_stdlib_editable_install(python_path: Path, root: Path) -> None:
    src_dir = root / "packages" / "pmanager" / "src"
    purelib = query_venv_path(python_path, "purelib")
    scripts = query_venv_path(python_path, "scripts")
    purelib.mkdir(parents=True, exist_ok=True)
    scripts.mkdir(parents=True, exist_ok=True)

    pth_path = purelib / "pmanager-dev.pth"
    pth_path.write_text(str(src_dir) + "\n", encoding="utf-8")

    if os.name == "nt":
        launcher = scripts / "pmanager.cmd"
        launcher.write_text(
            "@echo off\r\n"
            f"\"{python_path}\" -m pmanager %*\r\n",
            encoding="utf-8",
        )
    else:
        launcher = scripts / "pmanager"
        launcher.write_text(
            "#!/usr/bin/env sh\n"
            f"exec \"{python_path}\" -m pmanager \"$@\"\n",
            encoding="utf-8",
        )
        launcher.chmod(0o755)

    print("Installed pmanager editable through a stdlib .pth fallback.")


def wheel_command_available(python_path: Path) -> bool:
    probe = "import wheel.bdist_wheel"
    completed = subprocess.run(
        [str(python_path), "-c", probe],
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.returncode == 0


def install_pmanager_editable(python_path: Path, root: Path) -> None:
    if pmanager_points_to_checkout(python_path, root):
        write_stdlib_editable_install(python_path, root)
        print("pmanager is already installed editable from this checkout.")
        return

    if not wheel_command_available(python_path):
        print("wheel is not installed in the target venv; using stdlib editable fallback.")
        write_stdlib_editable_install(python_path, root)
        return

    package_dir = root / "packages" / "pmanager"
    command = [
        str(python_path),
        "-m",
        "pip",
        "install",
        "--no-build-isolation",
        "-e",
        str(package_dir),
    ]
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        print(
            "pip editable install failed; falling back to stdlib .pth editable install.",
            file=sys.stderr,
        )
        write_stdlib_editable_install(python_path, root)


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
        install_pmanager_editable(python_path, root)

    print(f"Target: {target}")
    print(f"Venv:   {venv_dir}")
    print(f"Python: {python_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
