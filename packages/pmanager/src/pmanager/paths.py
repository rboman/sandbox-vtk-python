from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


@dataclass(frozen=True)
class ProjectPaths:
    root: Path

    @classmethod
    def discover(cls) -> "ProjectPaths":
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
        return self.venvs_root / target

    def vtk_source_dir(self, version: str = "9.3.1") -> Path:
        return self.source_root / f"vtk-{version}"

    def vtk_build_dir(self, target: str, version: str = "9.3.1") -> Path:
        return self.build_root / f"vtk-{version}" / target

    def vtk_sdk_dir(self, target: str, version: str = "9.3.1") -> Path:
        return self.install_root / f"vtk-{version}" / target / "sdk"

    def vtk_wheelhouse_dir(self, target: str, version: str = "9.3.1") -> Path:
        return self.wheelhouse_root / f"vtk-{version}" / target

    def constraints_file(self, python_tag: str) -> Path:
        return self.constraints_dir / f"{python_tag}.txt"


DEFAULT_PATHS = ProjectPaths.discover()
