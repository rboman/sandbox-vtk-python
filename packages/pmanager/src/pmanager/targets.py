from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Target:
    name: str
    os_name: str
    arch: str
    toolchain: str
    python_tag: str
    build_type: str

    @property
    def constraints_name(self) -> str:
        return f"{self.python_tag}.txt"


PHASE1_TARGETS: dict[str, Target] = {
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
    return PHASE1_TARGETS.values()


def target_names() -> tuple[str, ...]:
    return tuple(PHASE1_TARGETS)


def get_target(name: str) -> Target:
    try:
        return PHASE1_TARGETS[name]
    except KeyError as exc:
        known = ", ".join(target_names())
        raise ValueError(f"Unknown target '{name}'. Known targets: {known}") from exc
