from __future__ import annotations

from pathlib import Path


def read_cmake_cache_generator(build_dir: Path) -> str | None:
    cache_path = build_dir / "CMakeCache.txt"
    if not cache_path.exists():
        return None

    for line in cache_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if line.startswith("CMAKE_GENERATOR:INTERNAL="):
            return line.split("=", 1)[1].strip() or None
    return None


def generator_backend(generator: str) -> str:
    if generator.startswith("Ninja"):
        return "ninja"
    if generator.startswith("Visual Studio"):
        return "vs"
    return "other"
