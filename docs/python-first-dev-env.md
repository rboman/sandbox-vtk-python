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
install VTK yet, does **not** replace the PowerShell/Bash build scripts, and
does **not** migrate `sync-venv`.

The current goal is only to validate that:

- the `pmanager` tooling venv can be created or selected;
- `pmanager` can be installed editable into that tooling venv;
- the phase-1 targets are exposed from Python code;
- `pmanager fetch vtk` can fetch VTK source archives;
- `pmanager build vtk` can print a concrete CMake build plan;
- `pmanager build vtk --configure` can run the CMake configure step;
- `pmanager build vtk --build` can run the CMake build step after configuration;
- `pmanager build vtk --install` can install the native SDK after a build;
- `pmanager build vtk --wheel` can generate the local Python `vtk` wheel;
- the validation scripts are importable through `pmanager.validation`;
- the new `pmanager validate ...` command group exists;
- the unit tests pass without requiring a VTK build.

## Current scope

Implemented in this slice:

- `scripts/bootstrap-dev-env.py`
- `pmanager.paths`
- `pmanager.targets`
- `pmanager.libraries`
- `pmanager.environment`
- `pmanager.validation`
- `pmanager.fetch`
- implemented CLI commands:
  - `pmanager fetch vtk`
- build CLI commands:
  - `pmanager build vtk`
- validation CLI commands:
  - `pmanager validate audit`
  - `pmanager validate provenance`
  - `pmanager validate import-order`

Not implemented yet:

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

For normal interactive development, activate it:

```bat
.venvs\pmanager-dev\Scripts\activate.bat
```

The rest of this document assumes this venv is active. That keeps the commands
short and matches the intended day-to-day workflow.

If you do not want to activate the venv, replace commands such as:

```bat
pmanager targets
```

with:

```bat
.venvs\pmanager-dev\Scripts\python.exe -m pmanager targets
```

After activation:

```bat
python -c "import sys; print(sys.executable)"
```

Expected result: the printed executable should be under:

```text
.venvs\pmanager-dev\Scripts\python.exe
```

## 4. Check `pmanager targets`

```bat
pmanager targets
```

Expected output:

```text
win-amd64-msvc2022-py310-release
linux-x86_64-gcc-py312-release
```

This confirms that `pmanager` is reading the phase-1 targets from
`pmanager.targets`, not from hardcoded strings in the CLI command body.

## 5. Check the VTK fetch/build commands

`pmanager fetch vtk` is implemented in Python. `pmanager build vtk` now prints
a concrete build plan and can explicitly run the configure, build, install, or
wheel step.

They must exist:

```bat
pmanager fetch vtk --help
pmanager build vtk --help
```

Expected result:

- both commands show Typer help;
- `fetch vtk` has `--url`, `--sha256`, and `--force` options;
- `build vtk` has target/backend/generator/Python options;
- `build vtk` has explicit `--configure`, `--build`, `--install`, and `--wheel`
  switches.

Print the Windows build plan without configuring or compiling:

```bat
pmanager build vtk --target win-amd64-msvc2022-py310-release
```

Expected output includes:

```text
Target:      win-amd64-msvc2022-py310-release
Source:      ...\external\src\vtk-9.3.1
Build:       ...\external\build\vtk-9.3.1\win-amd64-msvc2022-py310-release
SDK install: ...\external\install\vtk-9.3.1\win-amd64-msvc2022-py310-release\sdk
Wheelhouse:  ...\external\wheelhouse\vtk-9.3.1\win-amd64-msvc2022-py310-release
Configure:
  cmake ...
```

By default, `--backend auto` prefers Ninja when `ninja.exe` is available in
`PATH`. If Ninja is not found on Windows, `pmanager` falls back to the Visual
Studio generator.

On Windows with Ninja, the current shell must be a command-line build
environment that CMake/Ninja can use. For this workflow, the supported simple
route is to start from:

```text
x64 Native Tools Command Prompt for VS 2022
```

Then go back to the repository and activate the pmanager venv:

```bat
cd /d D:\dev\VIBECODING\sandbox-vtk-python
.venvs\pmanager-dev\Scripts\activate.bat
```

If `pmanager` selects Ninja but the current `cmd.exe` does not look like an
MSVC command-line build environment, it stops before running CMake and asks you
to use the Visual Studio developer `cmd.exe` prompt.

Do not over-interpret `where cl`: it is a useful clue for Ninja/MSVC, but it is
not a universal test for every CMake generator. A normal `cmd.exe` may still be
able to configure a Visual Studio generator even when `where cl` does not find
`cl.exe`. The current `pmanager` default prefers Ninja, so the Visual Studio
developer prompt is the least surprising path for now.

To force Ninja explicitly:

```bat
pmanager build vtk --target win-amd64-msvc2022-py310-release --backend ninja
```

To force the Visual Studio generator explicitly:

```bat
pmanager build vtk --target win-amd64-msvc2022-py310-release --backend vs
```

## 6. Test VTK fetch logic without downloading VTK

The unit tests create tiny local archives and verify safe extraction, checksum
handling, and the CLI path:

```bat
python -m pytest -q tests\test_pmanager_fetch.py
```

Expected result:

```text
7 passed
```

These tests do not require network access and do not touch `external\src`.

## 7. Test VTK build planning without compiling

The unit tests verify CMake argument construction, target paths, generator
detection, and refusal to switch generators in an existing build tree:

```bat
python -m pytest -q tests\test_pmanager_build.py
```

Expected result:

```text
17 passed
```

These tests do not configure or compile VTK. They also verify that the Python
implementation can call the configure/build command runner without actually
starting CMake during the test suite.

## 8. Optional: fetch the real VTK source archive

This downloads and extracts VTK 9.3.1 into:

```text
external\src\vtk-9.3.1
```

If that directory already exists, the command refuses to replace it:

```bat
pmanager fetch vtk
```

To deliberately replace the source tree:

```bat
pmanager fetch vtk --force
```

The Python fetch implementation:

- downloads with the standard library;
- prints a few progress messages so the user knows the command is still working;
- accepts an optional `--sha256`;
- extracts `.tar`, `.tar.gz`, `.tgz`, or `.zip`;
- rejects archive entries with absolute paths or `..`;
- rejects symlinks/hardlinks in tar archives;
- moves the extracted source tree into place only after extraction succeeds.

## 9. Optional: configure VTK with CMake

This step does not compile VTK. It only creates/configures the CMake build tree.

With Ninja preferred automatically:

```bat
pmanager build vtk --target win-amd64-msvc2022-py310-release --configure
```

Or with Ninja forced explicitly:

```bat
pmanager build vtk --target win-amd64-msvc2022-py310-release --backend ninja --configure
```

Expected behavior:

- prints the same build plan as the dry run;
- prints `Running VTK configure step...`;
- runs a `cmake -S ... -B ... -G Ninja ...` command if Ninja is selected;
- creates or updates:

```text
external\build\vtk-9.3.1\win-amd64-msvc2022-py310-release\
external\install\vtk-9.3.1\win-amd64-msvc2022-py310-release\sdk\
external\wheelhouse\vtk-9.3.1\win-amd64-msvc2022-py310-release\
```

If the build directory already contains a `CMakeCache.txt` generated with a
different backend, `pmanager` refuses to switch generator silently. Delete the
build directory deliberately if you want to reconfigure from scratch.

If CMake was interrupted or failed partway through configuration, it may leave a
partial build directory behind. The simplest recovery is:

```bat
rmdir /s /q external\build\vtk-9.3.1\win-amd64-msvc2022-py310-release
```

Then rerun the configure command from the Visual Studio developer `cmd.exe`
prompt.

## 10. Optional: compile VTK

This is the long step. Run it yourself when you are ready:

```bat
pmanager build vtk --target win-amd64-msvc2022-py310-release --build
```

Expected behavior:

- prints the build plan;
- prints `Running VTK build step...`;
- runs:

```text
cmake --build ... --parallel ...
```

If the CMake build tree has not been configured yet, the command refuses with a
message telling you to run:

```bat
pmanager build vtk --target win-amd64-msvc2022-py310-release --configure
```

This command does not install the SDK and does not build the Python wheel yet.
Those steps are explicit separate phases.

## 11. Optional: install the VTK SDK

After a successful build, install the native SDK tree:

```bat
pmanager build vtk --target win-amd64-msvc2022-py310-release --install
```

Expected behavior:

- prints the build plan;
- prints `Running VTK install step...`;
- runs:

```text
cmake --install ...
```

Expected output directory:

```text
external\install\vtk-9.3.1\win-amd64-msvc2022-py310-release\sdk\
```

This installs the native SDK used later for C++ compilation. It does not install
the Python `vtk` runtime into a venv and does not build the local wheel yet.

## 12. Optional: build the local VTK Python wheel

After configure/build/install, generate the local Python wheel:

```bat
pmanager build vtk --target win-amd64-msvc2022-py310-release --wheel
```

Expected behavior:

- prints the build plan;
- prints `Running VTK wheel step...`;
- ensures the target Python has `pip`, `setuptools`, and `wheel`;
- runs `setup.py bdist_wheel` from the VTK build directory.

Expected wheelhouse:

```text
external\wheelhouse\vtk-9.3.1\win-amd64-msvc2022-py310-release\
```

The produced wheel version may be `9.3.1.dev0`; do not expect the filename to
contain exactly `9.3.1`.

This command only builds the wheel file. It does not install that wheel into the
target venv yet. That will be handled by the later venv sync step.

## 13. Check the validation commands

The old scripts under `scripts\validate\` still exist, but their logic now lives
in importable modules under `pmanager.validation`.

Check the new command group:

```bat
pmanager validate --help
pmanager validate audit --help
pmanager validate provenance --help
pmanager validate import-order --help
```

Run a lightweight audit from the tooling venv:

```bat
pmanager validate audit --mode audit
```

This command is diagnostic. It may report environment hints depending on your
current shell. For example, if your global `PATH` still contains an old VTK
directory, the audit will report it. In `audit` mode that is useful information;
it should still run without needing a VTK build.

The legacy script path should also still work:

```bat
python scripts\validate\audit-environment.py --mode audit
```

## 14. Run the unit tests

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
56 passed
```

These tests do not require a VTK build. They cover:

- bootstrap command construction;
- phase-1 target definitions;
- minimal library registry with VTK only;
- path layout helpers;
- environment hygiene helpers;
- CLI availability for `fetch vtk` and `build vtk`.
- importable validation modules;
- CLI availability for `pmanager validate ...`.
- VTK fetch planning, checksum, safe extraction, and local-archive CLI behavior.
- VTK build planning, CMake command construction, and explicit
  configure/build/install/wheel command dispatch.

## 15. Optional targeted tests

Run only the new pmanager-related tests:

```bat
python -m pytest -q tests\test_bootstrap_dev_env.py tests\test_pmanager.py tests\test_pmanager_environment.py tests\test_pmanager_validation_modules.py tests\test_pmanager_fetch.py tests\test_pmanager_build.py tests\test_pmanager_process.py
```

Expected result:

```text
49 passed
```

The exact number may increase as the Python orchestration grows.

## 16. What not to test yet

Do not expect these commands to replace existing scripts yet:

```bat
pmanager build vtk
pmanager sync venv
```

At this stage:

- `pmanager fetch vtk` can fetch VTK sources, but does not install anything;
- `pmanager build vtk --configure` can configure the CMake build tree;
- `pmanager build vtk --build` can compile an already configured build tree;
- `pmanager build vtk --install` can install the native SDK tree;
- `pmanager build vtk --wheel` can generate the local Python wheel;
- `pmanager build vtk` without phase switches prints a dry-run plan;
- `pmanager build vtk` does not install the wheel into the target venv yet;
- `pmanager sync venv` is not implemented yet.

For real VTK work, continue using the validated scripts documented in
`docs/windows-from-scratch.md`.

## 17. Suggested development loop

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

## 18. Rollback for this slice

This slice is deliberately low risk.

It does not modify:

- `scripts/windows/fetch-vtk-source.ps1`
- `scripts/windows/build-vtk.ps1`
- `scripts/windows/sync-venv.ps1`
- `scripts/ubuntu/build-vtk.sh`
- `scripts/ubuntu/sync-venv.sh`
- Windows DLL staging logic

If you only ran `pmanager build vtk --configure`, rollback is simply deleting
the configured build tree for this target:

```bat
rmdir /s /q external\build\vtk-9.3.1\win-amd64-msvc2022-py310-release
```

The validation scripts under `scripts\validate\` are modified, but only as thin
wrappers around `pmanager.validation`. Their command-line behavior is intended
to remain compatible.

If the new Python-first helpers misbehave, the existing VTK workflow remains
available through `docs/windows-from-scratch.md`.
