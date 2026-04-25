from __future__ import annotations

import subprocess
import shutil
from dataclasses import dataclass
from pathlib import Path


class ProcessError(RuntimeError):
    pass


@dataclass(frozen=True)
class CommandResult:
    command: list[str]
    cwd: Path | None
    returncode: int


def format_command(command: list[str]) -> str:
    return " ".join(f'"{part}"' if " " in part else part for part in command)


def resolve_command(command: list[str]) -> list[str]:
    executable = command[0]
    if Path(executable).is_absolute() or "/" in executable or "\\" in executable:
        return command

    resolved = shutil.which(executable)
    if not resolved:
        raise ProcessError(f"Required executable was not found in PATH: {executable}")
    return [resolved, *command[1:]]


def run_command(command: list[str], *, cwd: Path | None = None) -> CommandResult:
    if not command:
        raise ProcessError("Cannot run an empty command.")

    resolved_command = resolve_command(command)
    print(f"> {format_command(resolved_command)}")
    completed = subprocess.run(resolved_command, cwd=cwd, check=False)
    if completed.returncode != 0:
        location = f" in {cwd}" if cwd else ""
        raise ProcessError(
            f"Command failed with exit code {completed.returncode}{location}: "
            f"{format_command(resolved_command)}"
        )
    return CommandResult(command=resolved_command, cwd=cwd, returncode=completed.returncode)
