from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class LibraryRecipe:
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
    return LIBRARIES.values()


def library_names() -> tuple[str, ...]:
    return tuple(LIBRARIES)


def get_library(name: str) -> LibraryRecipe:
    normalized = name.lower()
    try:
        return LIBRARIES[normalized]
    except KeyError as exc:
        known = ", ".join(library_names())
        raise ValueError(f"Unknown library '{name}'. Known libraries: {known}") from exc
