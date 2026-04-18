from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import typer

app = typer.Typer(help="Sandbox VTK / Python workflow helper.")

REPO_ROOT = Path(__file__).resolve().parents[4]


def _run_script(script: Path, *args: str) -> None:
    completed = subprocess.run([sys.executable, str(script), *args], check=False)
    if completed.returncode != 0:
        raise typer.Exit(completed.returncode)


@app.command("targets")
def list_targets() -> None:
    for target in ("win-amd64-msvc2022-py310-release", "linux-x86_64-gcc-py312-release"):
        typer.echo(target)


@app.command("audit-env")
def audit_env(
    mode: str = typer.Option("audit", help="audit or strict"),
    target_venv: str = typer.Option("", help="Target venv path"),
    target_sdk_root: str = typer.Option("", help="Target SDK root"),
) -> None:
    script = REPO_ROOT / "scripts" / "validate" / "audit-environment.py"
    args = ["--mode", mode]
    if target_venv:
        args.extend(["--target-venv", target_venv])
    if target_sdk_root:
        args.extend(["--target-sdk-root", target_sdk_root])
    _run_script(script, *args)


@app.command("runtime-provenance")
def runtime_provenance(
    target_venv: str = typer.Option("", help="Target venv path"),
    target_sdk_root: str = typer.Option("", help="Target SDK root"),
) -> None:
    script = REPO_ROOT / "scripts" / "validate" / "runtime-provenance.py"
    args = []
    if target_venv:
        args.extend(["--target-venv", target_venv])
    if target_sdk_root:
        args.extend(["--target-sdk-root", target_sdk_root])
    _run_script(script, *args)


@app.command("import-order")
def import_order(require_extension: bool = typer.Option(False, help="Require the native extension.")) -> None:
    script = REPO_ROOT / "scripts" / "validate" / "import-order.py"
    args = ["--require-extension"] if require_extension else []
    _run_script(script, *args)
