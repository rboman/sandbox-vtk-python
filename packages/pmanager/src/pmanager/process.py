from __future__ import annotations

"""Small subprocess wrapper used by all build and sync routines.

This file keeps command resolution, logging, and error formatting consistent.
"""

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


class ProcessError(RuntimeError):
    """Raised when an external command cannot be executed successfully."""
    pass


@dataclass(frozen=True)
class CommandResult:
    """Minimal command execution result used by higher-level orchestration."""
    command: list[str]
    cwd: Path | None
    returncode: int


def format_command(command: list[str]) -> str:
    """Render a command list as a readable shell-like string."""
    return " ".join(f'"{part}"' if " " in part else part for part in command)


def resolve_command(command: list[str]) -> list[str]:
    """Resolve the executable path when command[0] is not absolute."""
    executable = command[0]
    if Path(executable).is_absolute() or "/" in executable or "\\" in executable:
        return command

    resolved = shutil.which(executable)
    if not resolved:
        raise ProcessError(f"Required executable was not found in PATH: {executable}")
    return [resolved, *command[1:]]


def run_command(
    command: list[str],
    *,
    cwd: Path | None = None,
    env: Mapping[str, str] | None = None,
) -> CommandResult:
    """Run one command, stream output, and raise on non-zero exit code."""
    if not command:
        raise ProcessError("Cannot run an empty command.")

    resolved_command = resolve_command(command)
    print(f"> {format_command(resolved_command)}")
    completed = subprocess.run(resolved_command, cwd=cwd, env=env, check=False)
    if completed.returncode != 0:
        location = f" in {cwd}" if cwd else ""
        raise ProcessError(
            f"Command failed with exit code {completed.returncode}{location}: "
            f"{format_command(resolved_command)}"
        )
    return CommandResult(command=resolved_command, cwd=cwd, returncode=completed.returncode)


def run_command_text(
    command: list[str],
    *,
    cwd: Path | None = None,
    env: Mapping[str, str] | None = None,
) -> str:
    """Run one command and return captured stdout as text."""
    if not command:
        raise ProcessError("Cannot run an empty command.")

    resolved_command = resolve_command(command)
    completed = subprocess.run(
        resolved_command,
        cwd=cwd,
        env=env,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode != 0:
        location = f" in {cwd}" if cwd else ""
        stderr = completed.stderr.strip()
        detail = f"\n{stderr}" if stderr else ""
        raise ProcessError(
            f"Command failed with exit code {completed.returncode}{location}: "
            f"{format_command(resolved_command)}{detail}"
        )
    return completed.stdout.strip()
