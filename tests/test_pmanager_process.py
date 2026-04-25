from __future__ import annotations

import subprocess

from pmanager.process import ProcessError, resolve_command, run_command


def test_resolve_command_uses_path_lookup(monkeypatch) -> None:
    monkeypatch.setattr("pmanager.process.shutil.which", lambda name: f"/tools/{name}")

    assert resolve_command(["cmake", "--version"]) == ["/tools/cmake", "--version"]


def test_resolve_command_keeps_explicit_path() -> None:
    command = [r"C:\tools\cmake.exe", "--version"]

    assert resolve_command(command) == command


def test_resolve_command_fails_when_missing(monkeypatch) -> None:
    monkeypatch.setattr("pmanager.process.shutil.which", lambda name: None)

    try:
        resolve_command(["cmake", "--version"])
    except ProcessError as exc:
        assert "not found in PATH" in str(exc)
    else:  # pragma: no cover - defensive
        raise AssertionError("Expected missing executable failure")


def test_run_command_returns_resolved_command(monkeypatch) -> None:
    monkeypatch.setattr("pmanager.process.shutil.which", lambda name: f"/tools/{name}")

    def fake_run(command, *, cwd=None, env=None, check=False):
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr("pmanager.process.subprocess.run", fake_run)

    result = run_command(["cmake", "--version"])

    assert result.command == ["/tools/cmake", "--version"]
    assert result.returncode == 0


def test_run_command_text_returns_stdout(monkeypatch) -> None:
    monkeypatch.setattr("pmanager.process.shutil.which", lambda name: f"/tools/{name}")

    def fake_run(command, *, cwd=None, env=None, check=False, text=False, stdout=None, stderr=None):
        return subprocess.CompletedProcess(command, 0, stdout="9.3.1.dev0\n", stderr="")

    monkeypatch.setattr("pmanager.process.subprocess.run", fake_run)

    from pmanager.process import run_command_text

    assert run_command_text(["python", "-c", "print('x')"]) == "9.3.1.dev0"
