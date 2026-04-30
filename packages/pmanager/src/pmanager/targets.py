from __future__ import annotations

"""Target registry for supported platform/toolchain/python combinations.

This file defines the canonical build/runtime targets exposed by pmanager.
"""

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Target:
    """Describe one build/runtime target used across workflows."""
    name: str
    os_name: str
    arch: str
    toolchain: str
    python_tag: str
    build_type: str

    @property
    def constraints_name(self) -> str:
        """Return the constraints filename associated with this target."""
        return f"{self.python_tag}.txt"


BASELINE_TARGETS: dict[str, Target] = {
    "win-amd64-msvc2022-py310-release": Target(
        name="win-amd64-msvc2022-py310-release",
        os_name="win",
        arch="amd64",
        toolchain="msvc2022",
        python_tag="py310",
        build_type="release",
    ),
    "linux-x86_64-gcc-py312-release": Target(
        name="linux-x86_64-gcc-py312-release",
        os_name="linux",
        arch="x86_64",
        toolchain="gcc",
        python_tag="py312",
        build_type="release",
    ),
}


def iter_targets() -> Iterable[Target]:
    """Yield all registered targets."""
    return BASELINE_TARGETS.values()


def target_names() -> tuple[str, ...]:
    """Return all target names in registry order."""
    return tuple(BASELINE_TARGETS)


def get_target(name: str) -> Target:
    """Return one target or raise a helpful error."""
    try:
        return BASELINE_TARGETS[name]
    except KeyError as exc:
        known = ", ".join(target_names())
        raise ValueError(f"Unknown target '{name}'. Known targets: {known}") from exc
