from __future__ import annotations

import importlib.util
from pathlib import Path


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_summarize_libraries_flags_sdk_and_external_paths(tmp_path: Path) -> None:
    module = load_module(Path("scripts/validate/runtime-provenance.py"), "runtime_provenance")
    target_venv = tmp_path / ".venvs" / "target"
    target_sdk = tmp_path / "external" / "install" / "vtk-9.3.1" / "target" / "sdk"
    inside_venv = target_venv / "Lib" / "site-packages" / "bin" / "vtkCommonCore-9.3.dll"
    inside_sdk = target_sdk / "bin" / "vtkCommonCore-9.3.dll"
    outside_venv = tmp_path / "global-vtk" / "vtkRenderingQt-9.3.dll"

    summary = module.summarize_libraries(
        [str(inside_venv), str(inside_sdk), str(outside_venv), str(tmp_path / "python311.dll")],
        target_venv=str(target_venv),
        target_sdk_root=str(target_sdk),
    )

    assert str(inside_venv) in summary["inside_target_venv"]
    assert str(inside_sdk) in summary["inside_target_sdk"]
    assert str(outside_venv) in summary["outside_target_venv"]
    assert summary["violations"]
    assert summary["ok"] is False


def test_summarize_libraries_is_ok_when_all_vtk_paths_are_inside_venv(tmp_path: Path) -> None:
    module = load_module(Path("scripts/validate/runtime-provenance.py"), "runtime_provenance")
    target_venv = tmp_path / ".venvs" / "target"
    libs = [
        str(target_venv / "Lib" / "site-packages" / "bin" / "vtkCommonCore-9.3.dll"),
        str(target_venv / "Lib" / "site-packages" / "codecpp" / "_codecpp.pyd"),
    ]

    summary = module.summarize_libraries(
        libs,
        target_venv=str(target_venv),
        target_sdk_root=str(tmp_path / "external" / "install"),
    )

    assert summary["violations"] == []
    assert summary["ok"] is True
