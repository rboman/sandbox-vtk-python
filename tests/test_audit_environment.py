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


def test_classify_path_marks_global_vtk_as_suspicious(tmp_path: Path) -> None:
    module = load_module(Path("scripts/validate/audit-environment.py"), "audit_environment")
    repo_root = tmp_path / "repo"
    target_venv = repo_root / ".venvs" / "target"
    global_vtk = tmp_path / "old-vtk" / "site-packages"
    status, normalized = module.classify_path_entry(
        str(global_vtk),
        target_venv=str(target_venv),
        repo_root=str(repo_root),
    )
    assert status == "suspicious"
    assert "site-packages" in normalized


def test_classify_path_allows_target_venv(tmp_path: Path) -> None:
    module = load_module(Path("scripts/validate/audit-environment.py"), "audit_environment")
    repo_root = tmp_path / "repo"
    target_venv = repo_root / ".venvs" / "target"
    venv_site_packages = target_venv / "lib" / "site-packages"
    status, _ = module.classify_path_entry(
        str(venv_site_packages),
        target_venv=str(target_venv),
        repo_root=str(repo_root),
    )
    assert status == "allowed"
