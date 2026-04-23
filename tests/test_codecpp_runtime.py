from __future__ import annotations

from pathlib import Path

from codecpp import _runtime


def test_iter_runtime_candidates_includes_vtk_libs(tmp_path: Path) -> None:
    vtkmodules = tmp_path / "site-packages" / "vtkmodules"
    vtkmodules.mkdir(parents=True)
    (vtkmodules.parent / "vtk.libs").mkdir()
    (vtkmodules.parent / "custom.libs").mkdir()

    candidates = _runtime._iter_runtime_candidates(vtkmodules)  # noqa: SLF001
    candidate_strings = {str(path) for path in candidates}

    assert str(vtkmodules) in candidate_strings
    assert str(vtkmodules.parent / "vtk.libs") in candidate_strings


def test_describe_runtime_reports_environment_hints(monkeypatch) -> None:
    monkeypatch.setenv("VTK_DIR", "/tmp/global-vtk")
    details = _runtime.describe_runtime()
    assert "VTK_DIR" in details["environment_hints"]
    assert "vtk_dlls" not in details


def test_describe_runtime_verbose_reports_vtk_dlls(monkeypatch) -> None:
    monkeypatch.setenv("VTK_DIR", "/tmp/global-vtk")
    details = _runtime.describe_runtime(verbose=True)
    assert "VTK_DIR" in details["environment_hints"]
    assert "vtk_dlls" in details
