from __future__ import annotations

from pathlib import Path

from pmanager.validation import audit_environment, import_order, runtime_provenance


def test_validation_modules_are_importable() -> None:
    assert audit_environment.classify_path_entry
    assert import_order.run_order
    assert runtime_provenance.summarize_libraries


def test_audit_environment_finds_repo_root() -> None:
    root = audit_environment.find_repo_root()
    assert (root / "README.md").exists()
    assert (root / "packages").exists()


def test_runtime_provenance_summary_from_importable_module(tmp_path: Path) -> None:
    target_venv = tmp_path / ".venvs" / "target"
    target_sdk = tmp_path / "external" / "install" / "vtk-9.3.1" / "target" / "sdk"
    inside_venv = target_venv / "Lib" / "site-packages" / "bin" / "vtkCommonCore-9.3.dll"
    inside_sdk = target_sdk / "bin" / "vtkCommonCore-9.3.dll"

    summary = runtime_provenance.summarize_libraries(
        [str(inside_venv), str(inside_sdk)],
        target_venv=str(target_venv),
        target_sdk_root=str(target_sdk),
    )

    assert str(inside_venv) in summary["inside_target_venv"]
    assert str(inside_sdk) in summary["inside_target_sdk"]
    assert summary["violations"]
