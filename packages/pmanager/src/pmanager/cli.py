from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import typer

from pmanager.libraries import get_library
from pmanager.targets import iter_targets

app = typer.Typer(help="Sandbox VTK / Python workflow helper.")
fetch_app = typer.Typer(help="Fetch external library sources.")
build_app = typer.Typer(help="Build external libraries.")

REPO_ROOT = Path(__file__).resolve().parents[4]


def _run_script(script: Path, *args: str) -> None:
    completed = subprocess.run([sys.executable, str(script), *args], check=False)
    if completed.returncode != 0:
        raise typer.Exit(completed.returncode)


@app.command("targets")
def list_targets() -> None:
    for target in iter_targets():
        typer.echo(target.name)


@fetch_app.command("vtk")
def fetch_vtk() -> None:
    library = get_library("vtk")
    typer.echo(
        f"Fetch recipe is registered for {library.name} {library.version}, "
        "but Python fetch execution is not implemented in this tranche."
    )


@build_app.command("vtk")
def build_vtk() -> None:
    library = get_library("vtk")
    typer.echo(
        f"Build recipe is registered for {library.name} {library.version}, "
        "but Python build execution is not implemented in this tranche."
    )


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


app.add_typer(fetch_app, name="fetch")
app.add_typer(build_app, name="build")
