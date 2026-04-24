# Python-first development environment

This document explains how to test the current Python-first orchestration slice.

## Development philosophy

This project is for numerical simulation work in a university laboratory. The
workflow should help one main developer, students, or close collaborators work
comfortably on Windows and Linux.

The goal is not to create a large general-purpose build platform. Prefer simple
Python tooling, clear commands, and step-by-step validation. Assume network
access is available for installing ordinary Python development dependencies.

On Windows, this project uses `cmd.exe` examples by default. The project owner
is more comfortable with Linux-like shells and classic Windows command lines
than with PowerShell. New documentation should therefore avoid PowerShell syntax
unless it is documenting an existing transitional script.

Going forward, `pmanager` should live in a small tooling environment, for
example:

```text
.venvs/pmanager-dev/
```

and should manage target environments such as:

```text
.venvs/win-amd64-msvc2022-py310-release/
.venvs/linux-x86_64-gcc-py312-release/
```

The current slice was started before this simplification was fully clarified,
so it still bootstraps against the Windows target venv. Treat that as a
transitional state, not as the long-term model.

It is intentionally narrower than `docs/windows-from-scratch.md`: it does **not**
build VTK yet, does **not** replace the PowerShell/Bash build scripts, and does
**not** migrate `sync-venv`.

The current goal is only to validate that:

- a target venv can be created or selected;
- `pmanager` can be installed editable into that venv;
- the phase-1 targets are exposed from Python code;
- the future commands `pmanager fetch vtk` and `pmanager build vtk` exist;
- the unit tests pass without requiring a VTK build.

## Current scope

Implemented in this slice:

- `scripts/bootstrap-dev-env.py`
- `pmanager.paths`
- `pmanager.targets`
- `pmanager.libraries`
- `pmanager.environment`
- preparatory CLI commands:
  - `pmanager fetch vtk`
  - `pmanager build vtk`

Not implemented yet:

- Python VTK source download
- Python VTK build orchestration
- Python venv synchronization
- Python Windows DLL staging
- replacement of existing PowerShell/Bash scripts

## 1. Start from the repository root

Windows `cmd.exe`:

```bat
cd /d D:\dev\VIBECODING\sandbox-vtk-python
```

Optional sanity check:

```bat
git status --short
```

The repository may contain local development changes, but this slice should not
modify the existing build/sync/fetch scripts.

## 2. Bootstrap the target development venv

Note: this is the current transitional command. The next simplification should
move `pmanager` development to `.venvs/pmanager-dev`.

Run:

```bat
python scripts\bootstrap-dev-env.py --target win-amd64-msvc2022-py310-release
```

Expected behavior:

- creates `.venvs\win-amd64-msvc2022-py310-release` if missing;
- upgrades/installs the basic development tools: `pip`, `setuptools`, `wheel`,
  `typer`, and `pytest`;
- installs `packages\pmanager` in editable mode;
- reuses the existing editable install if it already points to this checkout;
- prints the target, venv path, and Python executable.

Typical output:

```text
pmanager is already installed editable from this checkout.
Target: win-amd64-msvc2022-py310-release
Venv:   D:\dev\VIBECODING\sandbox-vtk-python\.venvs\win-amd64-msvc2022-py310-release
Python: D:\dev\VIBECODING\sandbox-vtk-python\.venvs\win-amd64-msvc2022-py310-release\Scripts\python.exe
```

If the venv does not exist yet, the first run may take longer because Python has
to create it and install the basic Python development tools.

## 3. Enter or use the target venv

For interactive development, activate it:

```bat
.venvs\win-amd64-msvc2022-py310-release\Scripts\activate.bat
```

After activation:

```bat
python -c "import sys; print(sys.executable)"
```

Expected result: the printed executable should be under:

```text
.venvs\win-amd64-msvc2022-py310-release\Scripts\python.exe
```

You can also avoid activation and call the venv tools explicitly:

```bat
.venvs\win-amd64-msvc2022-py310-release\Scripts\python.exe -m pip --version
.venvs\win-amd64-msvc2022-py310-release\Scripts\python.exe -m pmanager targets
```

Depending on how the editable install was created, the venv may expose either a
normal `pmanager` launcher or the explicit module form. The module form is the
most reliable way to test this slice:

```bat
.venvs\win-amd64-msvc2022-py310-release\Scripts\python.exe -m pmanager targets
```

## 4. Check `pmanager targets`

From the activated venv:

```bat
pmanager targets
```

Or without activation:

```bat
.venvs\win-amd64-msvc2022-py310-release\Scripts\python.exe -m pmanager targets
```

Expected output:

```text
win-amd64-msvc2022-py310-release
linux-x86_64-gcc-py312-release
```

This confirms that `pmanager` is reading the phase-1 targets from
`pmanager.targets`, not from hardcoded strings in the CLI command body.

## 5. Check the future VTK commands

These commands are intentionally placeholders for now.

They must exist:

```bat
pmanager fetch vtk --help
pmanager build vtk --help
```

Equivalent explicit calls:

```bat
.venvs\win-amd64-msvc2022-py310-release\Scripts\python.exe -m pmanager fetch vtk --help
.venvs\win-amd64-msvc2022-py310-release\Scripts\python.exe -m pmanager build vtk --help
```

Expected result:

- both commands show Typer help;
- neither command downloads or builds anything;
- existing scripts remain the official implementation for real VTK work.

You can also run the placeholder commands directly:

```bat
pmanager fetch vtk
pmanager build vtk
```

Expected messages:

```text
Fetch recipe is registered for vtk 9.3.1, but Python fetch execution is not implemented in this tranche.
Build recipe is registered for vtk 9.3.1, but Python build execution is not implemented in this tranche.
```

## 6. Run the unit tests

From the repository root:

```bat
python -m pytest -q
```

If you are in the activated venv, this works because the bootstrap installs
`pytest`. If it fails with `No module named pytest`, rerun:

```bat
python scripts\bootstrap-dev-env.py --target win-amd64-msvc2022-py310-release
```

Expected result for this slice:

```text
20 passed
```

These tests do not require a VTK build. They cover:

- bootstrap command construction;
- phase-1 target definitions;
- minimal library registry with VTK only;
- path layout helpers;
- environment hygiene helpers;
- CLI availability for `fetch vtk` and `build vtk`.

## 7. Optional targeted tests

Run only the new pmanager-related tests:

```bat
python -m pytest -q tests\test_bootstrap_dev_env.py tests\test_pmanager.py tests\test_pmanager_environment.py
```

Expected result:

```text
13 passed
```

The exact number may increase as the Python orchestration grows.

## 8. What not to test yet

Do not expect these commands to replace existing scripts yet:

```bat
pmanager fetch vtk
pmanager build vtk
pmanager sync venv
```

At this stage:

- `pmanager fetch vtk` only proves that the VTK recipe is registered;
- `pmanager build vtk` only proves that the future command shape exists;
- `pmanager sync venv` is not implemented yet.

For real VTK work, continue using the validated scripts documented in
`docs/windows-from-scratch.md`.

## 9. Suggested development loop

When working on the next Python-first slice:

1. Bootstrap once with the current transitional command:

   ```bat
   python scripts\bootstrap-dev-env.py --target win-amd64-msvc2022-py310-release
   ```

2. Activate the target venv:

   ```bat
   .venvs\win-amd64-msvc2022-py310-release\Scripts\activate.bat
   ```

3. Edit `packages\pmanager\src\pmanager\...`.

4. Run focused tests:

   ```bat
   python -m pytest -q tests\test_pmanager.py tests\test_pmanager_environment.py
   ```

5. Run the full unit suite:

   ```bat
   python -m pytest -q
   ```

Because `pmanager` is installed editable, code changes should be visible without
reinstalling in normal development.

The next intended improvement is to move this same simple bootstrap behavior to
`.venvs/pmanager-dev`, so `pmanager` becomes a separate tooling environment
instead of living in the VTK target venv.

## 10. Rollback for this slice

This slice is deliberately low risk.

It does not modify:

- `scripts/windows/fetch-vtk-source.ps1`
- `scripts/windows/build-vtk.ps1`
- `scripts/windows/sync-venv.ps1`
- `scripts/ubuntu/build-vtk.sh`
- `scripts/ubuntu/sync-venv.sh`
- Windows DLL staging logic

If the new Python-first helpers misbehave, the existing VTK workflow remains
available through `docs/windows-from-scratch.md`.
