from __future__ import annotations

"""Library recipe registry for build orchestration.

This file is the single source of truth for supported third-party libraries.
"""

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class LibraryRecipe:
    """Minimal metadata required to fetch and build one library recipe."""
    name: str
    version: str
    source_dir_name: str


VTK = LibraryRecipe(
    name="vtk",
    version="9.3.1",
    source_dir_name="vtk-9.3.1",
)

LIBRARIES: dict[str, LibraryRecipe] = {
    VTK.name: VTK,
}


def iter_libraries() -> Iterable[LibraryRecipe]:
    """Yield all registered library recipes."""
    return LIBRARIES.values()


def library_names() -> tuple[str, ...]:
    """Return all library keys used by the CLI."""
    return tuple(LIBRARIES)


def get_library(name: str) -> LibraryRecipe:
    """Return one library recipe by name, case-insensitive."""
    normalized = name.lower()
    try:
        return LIBRARIES[normalized]
    except KeyError as exc:
        known = ", ".join(library_names())
        raise ValueError(f"Unknown library '{name}'. Known libraries: {known}") from exc
