from __future__ import annotations

"""Small helpers to map CMake cache state to pmanager backend choices.

This file keeps CMake-specific parsing isolated from build orchestration logic.
"""

from pathlib import Path


def read_cmake_cache_generator(build_dir: Path) -> str | None:
    """Return the configured CMake generator from an existing build tree."""
    cache_path = build_dir / "CMakeCache.txt"
    if not cache_path.exists():
        return None

    for line in cache_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if line.startswith("CMAKE_GENERATOR:INTERNAL="):
            return line.split("=", 1)[1].strip() or None
    return None


def generator_backend(generator: str) -> str:
    """Map a CMake generator string to a coarse backend label."""
    if generator.startswith("Ninja"):
        return "ninja"
    if generator.startswith("Visual Studio"):
        return "vs"
    return "other"
