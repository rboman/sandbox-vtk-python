from __future__ import annotations

"""Project path model used by all pmanager workflows.

This file centralizes repository layout conventions to avoid hardcoded paths.
"""

from dataclasses import dataclass
from pathlib import Path


def repo_root() -> Path:
    """Return the repository root from this module location."""
    return Path(__file__).resolve().parents[4]


@dataclass(frozen=True)
class ProjectPaths:
    """Convenience accessors for all important workspace directories."""
    root: Path

    @classmethod
    def discover(cls) -> "ProjectPaths":
        """Build a path model using automatic repository discovery."""
        return cls(root=repo_root())

    @property
    def constraints_dir(self) -> Path:
        return self.root / "constraints"

    @property
    def external_dir(self) -> Path:
        return self.root / "external"

    @property
    def source_root(self) -> Path:
        return self.external_dir / "src"

    @property
    def build_root(self) -> Path:
        return self.external_dir / "build"

    @property
    def install_root(self) -> Path:
        return self.external_dir / "install"

    @property
    def wheelhouse_root(self) -> Path:
        return self.external_dir / "wheelhouse"

    @property
    def venvs_root(self) -> Path:
        return self.root / ".venvs"

    @property
    def packages_dir(self) -> Path:
        return self.root / "packages"

    def venv_dir(self, target: str) -> Path:
        """Return the target virtual environment directory."""
        return self.venvs_root / target

    def vtk_source_dir(self, version: str = "9.3.1") -> Path:
        """Return the VTK source directory for a given version."""
        return self.source_root / f"vtk-{version}"

    def vtk_build_dir(self, target: str, version: str = "9.3.1") -> Path:
        """Return the VTK build directory for a given target."""
        return self.build_root / f"vtk-{version}" / target

    def vtk_sdk_dir(self, target: str, version: str = "9.3.1") -> Path:
        """Return the VTK SDK install directory for a given target."""
        return self.install_root / f"vtk-{version}" / target / "sdk"

    def vtk_wheelhouse_dir(self, target: str, version: str = "9.3.1") -> Path:
        """Return the wheelhouse directory for VTK wheel outputs."""
        return self.wheelhouse_root / f"vtk-{version}" / target

    def constraints_file(self, python_tag: str) -> Path:
        """Return the constraints file path for one Python tag."""
        return self.constraints_dir / f"{python_tag}.txt"


DEFAULT_PATHS = ProjectPaths.discover()
