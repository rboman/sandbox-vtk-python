from __future__ import annotations

import typer

from pmanager.fetch import FetchError, fetch_vtk as fetch_vtk_source
from pmanager.libraries import get_library
from pmanager.targets import iter_targets
from pmanager.validation import audit_environment, import_order as import_order_validation
from pmanager.validation import runtime_provenance as runtime_provenance_validation

app = typer.Typer(help="Sandbox VTK / Python workflow helper.")
fetch_app = typer.Typer(help="Fetch external library sources.")
build_app = typer.Typer(help="Build external libraries.")
validate_app = typer.Typer(help="Run validation checks.")

@app.command("targets")
def list_targets() -> None:
    for target in iter_targets():
        typer.echo(target.name)


@fetch_app.command("vtk")
def fetch_vtk(
    url: str = typer.Option("", help="Override the VTK source archive URL."),
    sha256: str = typer.Option("", help="Expected SHA256 for the downloaded archive."),
    force: bool = typer.Option(False, help="Replace an existing VTK source tree."),
) -> None:
    library = get_library("vtk")
    try:
        source_dir = fetch_vtk_source(
            url=url or None,
            sha256=sha256 or None,
            force=force,
            verbose=True,
        )
    except FetchError as exc:
        typer.echo(f"fetch {library.name} failed: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo(f"Fetched {library.name} {library.version} source into {source_dir}")


@build_app.command("vtk")
def build_vtk() -> None:
    library = get_library("vtk")
    typer.echo(
        f"Build recipe is registered for {library.name} {library.version}, "
        "but Python build execution is not implemented in this tranche."
    )


@validate_app.command("audit")
def validate_audit(
    mode: str = typer.Option("audit", help="audit or strict"),
    target_venv: str = typer.Option("", help="Target venv path"),
    target_sdk_root: str = typer.Option("", help="Target SDK root"),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    args = ["--mode", mode]
    if target_venv:
        args.extend(["--target-venv", target_venv])
    if target_sdk_root:
        args.extend(["--target-sdk-root", target_sdk_root])
    if json_output:
        args.append("--json")
    raise typer.Exit(audit_environment.main(args))


@validate_app.command("provenance")
def validate_provenance(
    modules: list[str] = typer.Option(None, "--module", help="Module to import before inspection."),
    target_venv: str = typer.Option("", help="Target venv path"),
    target_sdk_root: str = typer.Option("", help="Target SDK root"),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    args: list[str] = []
    if modules:
        args.append("--modules")
        args.extend(modules)
    if target_venv:
        args.extend(["--target-venv", target_venv])
    if target_sdk_root:
        args.extend(["--target-sdk-root", target_sdk_root])
    if json_output:
        args.append("--json")
    raise typer.Exit(runtime_provenance_validation.main(args))


@validate_app.command("import-order")
def validate_import_order(
    order: list[str] = typer.Option(None, "--order", help="Comma-separated import order."),
    require_extension: bool = typer.Option(False, help="Require the native extension."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    args: list[str] = []
    for item in order or []:
        args.extend(["--order", item])
    if require_extension:
        args.append("--require-extension")
    if json_output:
        args.append("--json")
    raise typer.Exit(import_order_validation.main(args))


@app.command("audit-env")
def audit_env(
    mode: str = typer.Option("audit", help="audit or strict"),
    target_venv: str = typer.Option("", help="Target venv path"),
    target_sdk_root: str = typer.Option("", help="Target SDK root"),
) -> None:
    args = ["--mode", mode]
    if target_venv:
        args.extend(["--target-venv", target_venv])
    if target_sdk_root:
        args.extend(["--target-sdk-root", target_sdk_root])
    raise typer.Exit(audit_environment.main(args))


@app.command("runtime-provenance")
def runtime_provenance(
    target_venv: str = typer.Option("", help="Target venv path"),
    target_sdk_root: str = typer.Option("", help="Target SDK root"),
) -> None:
    args = []
    if target_venv:
        args.extend(["--target-venv", target_venv])
    if target_sdk_root:
        args.extend(["--target-sdk-root", target_sdk_root])
    raise typer.Exit(runtime_provenance_validation.main(args))


@app.command("import-order")
def import_order(require_extension: bool = typer.Option(False, help="Require the native extension.")) -> None:
    args = ["--require-extension"] if require_extension else []
    raise typer.Exit(import_order_validation.main(args))


app.add_typer(fetch_app, name="fetch")
app.add_typer(build_app, name="build")
app.add_typer(validate_app, name="validate")
