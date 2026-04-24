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

`pmanager` lives in a small tooling environment:

```text
.venvs/pmanager-dev/
```

and should manage target environments such as:

```text
.venvs/win-amd64-msvc2022-py310-release/
.venvs/linux-x86_64-gcc-py312-release/
```

It is intentionally narrower than `docs/windows-from-scratch.md`: it does **not**
build VTK yet, does **not** replace the PowerShell/Bash build scripts, and does
**not** migrate `sync-venv`.

The current goal is only to validate that:

- the `pmanager` tooling venv can be created or selected;
- `pmanager` can be installed editable into that tooling venv;
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

## 2. Bootstrap the pmanager development venv

Run:

```bat
python scripts\bootstrap-dev-env.py
```

Expected behavior:

- creates `.venvs\pmanager-dev` if missing;
- upgrades/installs the basic development tools: `pip`, `setuptools`, `wheel`,
  `typer`, and `pytest`;
- installs `packages\pmanager` in editable mode;
- reuses the existing editable install if it already points to this checkout;
- prints the target, venv path, and Python executable.

Typical output:

```text
Venv name: pmanager-dev
Venv:   D:\dev\VIBECODING\sandbox-vtk-python\.venvs\pmanager-dev
Python: D:\dev\VIBECODING\sandbox-vtk-python\.venvs\pmanager-dev\Scripts\python.exe
```

If the venv does not exist yet, the first run may take longer because Python has
to create it and install the basic Python development tools.

If the first creation was interrupted or Windows reports a permission problem
inside `.venvs\pmanager-dev`, recreate only the tooling venv:

```bat
python scripts\bootstrap-dev-env.py --recreate
```

Do not run `--recreate` from inside an activated `.venvs\pmanager-dev`; the
bootstrap refuses to remove the active venv.

## 3. Enter or use the pmanager development venv

For interactive development, activate it:

```bat
.venvs\pmanager-dev\Scripts\activate.bat
```

After activation:

```bat
python -c "import sys; print(sys.executable)"
```

Expected result: the printed executable should be under:

```text
.venvs\pmanager-dev\Scripts\python.exe
```

You can also avoid activation and call the venv tools explicitly:

```bat
.venvs\pmanager-dev\Scripts\python.exe -m pip --version
.venvs\pmanager-dev\Scripts\python.exe -m pmanager targets
```

Depending on how the editable install was created, the venv may expose either a
normal `pmanager` launcher or the explicit module form. The module form is the
most reliable way to test this slice:

```bat
.venvs\pmanager-dev\Scripts\python.exe -m pmanager targets
```

## 4. Check `pmanager targets`

From the activated venv:

```bat
pmanager targets
```

Or without activation:

```bat
.venvs\pmanager-dev\Scripts\python.exe -m pmanager targets
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
.venvs\pmanager-dev\Scripts\python.exe -m pmanager fetch vtk --help
.venvs\pmanager-dev\Scripts\python.exe -m pmanager build vtk --help
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
python scripts\bootstrap-dev-env.py
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

1. Bootstrap once:

   ```bat
   python scripts\bootstrap-dev-env.py
   ```

2. Activate the pmanager development venv:

   ```bat
   .venvs\pmanager-dev\Scripts\activate.bat
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

The VTK target venv remains separate. It should be managed later by `pmanager`,
not used as the default development environment for `pmanager` itself.

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
