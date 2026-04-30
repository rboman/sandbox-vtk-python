# AI handoff

Last updated: 2026-04-30

This file is a compact handoff for continuing the project in a new AI/session.

## Project intent

This repository is a cross-platform sandbox for a mixed C++ / Python numerical
simulation workflow using a custom-built VTK 9.3.1.

The project is not an application. Its purpose is to validate a robust,
understandable architecture for:

- building VTK from source;
- installing a native VTK SDK for C++ compilation;
- building a matching local Python `vtk` wheel;
- installing that wheel into a target venv;
- installing `pyvista` without allowing pip to pull another VTK;
- building and installing a native SWIG package, `codecpp`;
- validating that `vtk`, `pyvista`, and `codecpp` coexist in one Python process
  while resolving VTK runtime libraries from the target venv.

The development context is a university numerical simulation lab. Keep the
tooling practical, explicit, and easy to teach to one student or collaborator.
Avoid enterprise-style abstraction or heavy fallback machinery unless the user
explicitly asks for it.

## User preferences

- Answer the user in French.
- Prefer `cmd.exe` commands in Windows documentation.
- Avoid asking the user to learn PowerShell.
- Use Python-first orchestration through `pmanager`.
- Keep PowerShell/Bash only as temporary wrappers or shell-specific entrypoints.
- Avoid large compatibility workarounds without asking.
- Assume normal network access for Python package installation.
- Keep the multi-library design possible, but do not over-abstract beyond the
  concrete VTK recipe yet.

## Core architecture rule

Compile-time and runtime VTK authority must stay separate.

Compile-time VTK authority:

```text
external/install/vtk-9.3.1/<target>/sdk/
```

Runtime Python VTK authority:

```text
.venvs/<target>/.../site-packages/
```

At Python runtime, `vtk`, `pyvista`, and `codecpp` must resolve to one coherent
VTK runtime rooted in the target venv, not the SDK install tree and not a global
VTK installation.

## Phase-1 targets

- `win-amd64-msvc2022-py310-release`
- `linux-x86_64-gcc-py312-release`

Windows phase 1 is validated. Ubuntu remains to be validated end-to-end.

## Current validated Windows workflow

Run from a Visual Studio developer `cmd.exe` prompt:

```bat
cd /d D:\dev\VIBECODING\sandbox-vtk-python
python scripts\bootstrap-dev-env.py
.venvs\pmanager-dev\Scripts\activate.bat
pmanager workflow windows-phase1
```

This has been tested by the user from a clean repository state where `.venvs`,
`external/src`, `external/build`, `external/install`, and `external/wheelhouse`
were absent.

The workflow performs:

```text
fetch VTK source if missing
prepare target venv
configure VTK
build VTK
install native SDK
build local Python vtk wheel
sync target venv
validate runtime provenance
validate import order
```

Successful user-observed validation:

```text
Runtime provenance OK: vtk/codecpp native libraries are resolved from the target venv and not from the SDK tree.
Order ['codecpp', 'pyvista']: returncode=0
Order ['pyvista', 'codecpp']: returncode=0
```

Manual sanity check also succeeded:

```bat
python -c "import vtk, pyvista, codecpp; codecpp.require_extension(); print(vtk.vtkVersion.GetVTKVersion()); print(codecpp.describe_runtime())"
```

Observed result included:

- `vtk.vtkVersion.GetVTKVersion()` prints `9.3.1`;
- installed wheel version is `vtk 9.3.1.dev0`;
- `vtkmodules_dir` is inside `.venvs/win-amd64-msvc2022-py310-release`;
- `runtime_bin_dir` is inside the same venv;
- no environment hints were required.

## Important commands

Bootstrap tooling env:

```bat
python scripts\bootstrap-dev-env.py
.venvs\pmanager-dev\Scripts\activate.bat
```

Step-by-step VTK workflow:

```bat
pmanager fetch vtk
pmanager build vtk --target win-amd64-msvc2022-py310-release --configure
pmanager build vtk --target win-amd64-msvc2022-py310-release --build
pmanager build vtk --target win-amd64-msvc2022-py310-release --install
pmanager build vtk --target win-amd64-msvc2022-py310-release --wheel
pmanager sync venv --target win-amd64-msvc2022-py310-release
```

Validation from the target venv:

```bat
.venvs\win-amd64-msvc2022-py310-release\Scripts\activate.bat
pmanager validate provenance --target-venv .venvs\win-amd64-msvc2022-py310-release --target-sdk-root external\install\vtk-9.3.1\win-amd64-msvc2022-py310-release\sdk
pmanager validate import-order --require-extension
```

Unit tests:

```bat
python -m pytest -q
```

Current expected count after the latest changes:

```text
71 passed
```

## Implemented Python modules

Main package:

```text
packages/pmanager/src/pmanager/
```

Important modules:

- `paths.py`: repository and artifact paths.
- `targets.py`: phase-1 target definitions.
- `libraries.py`: minimal VTK library recipe registry.
- `environment.py`: environment hygiene helpers.
- `process.py`: subprocess execution without `shell=True`, command resolution,
  optional env passing, captured text output.
- `fetch.py`: VTK source download and safe extraction.
- `cmake.py`: CMake cache generator detection.
- `build.py`: VTK configure/build/install/wheel planning and execution.
- `sync.py`: target venv synchronization, local VTK wheel install, dynamic VTK
  constraint generation, Windows DLL staging, local package installation.
- `workflow.py`: `windows-phase1` orchestration.
- `validation/`: importable audit, runtime provenance, and import-order logic.
- `cli.py`: Typer CLI wiring.

Legacy validation scripts in `scripts/validate/*.py` are now thin wrappers around
`pmanager.validation`.

## Current documentation state

Key docs:

- `README.md`: updated project overview and Python-first workflow summary.
- `docs/python-first-dev-env.md`: detailed step-by-step test guide.
- `docs/windows-from-scratch.md`: now points to the Python-first workflow as the
  preferred Windows path; keeps older script-based steps as transition docs.
- `docs/architecture.md`
- `docs/build-flow.md`
- `docs/runtime-model.md`
- `docs/environment-hygiene.md`
- `docs/validation-matrix.md`
- `docs/decisions/0001-vtk-sdk-vs-python-runtime.md`

## Known behaviors and nuances

- `pmanager build vtk` defaults to backend `auto`.
- On Windows, `auto` prefers Ninja if `ninja.exe` is found.
- Ninja/MSVC builds should be launched from a Visual Studio developer `cmd.exe`
  prompt.
- Do not over-interpret `where cl`: it is useful for Ninja/MSVC, but not a
  universal CMake/Visual Studio capability test.
- The produced Python package version may be `vtk 9.3.1.dev0`, while
  `vtk.vtkVersion.GetVTKVersion()` prints `9.3.1`.
- `pmanager sync venv` sanitizes PATH for its subprocesses only. It removes
  suspicious old VTK, `site-packages`, `.venv/.venvs`, and Conda entries before
  running strict audit and pip commands.
- `codecpp` is installed non-editable; `codepy` and `pmanager` are currently
  installed editable in the target venv.

## Important risks

- Windows DLL staging remains critical. Do not remove it without replacing the
  runtime provenance strategy.
- `pyvista` must remain constrained against the actually installed local VTK
  version. Do not assume exact version `9.3.1`; use detected installed version.
- Avoid global `PYTHONPATH`, `VTK_DIR`, `CMAKE_PREFIX_PATH`, or SDK `bin` paths
  as hidden dependencies.
- Do not remove legacy scripts until Python parity has been accepted and a
  fallback/rollback path is documented.
- Ubuntu has not yet been revalidated with the Python-first workflow.

## Recommended next steps

1. Commit the current validated Windows Python-first state.
2. Decide how to retire old Windows PowerShell scripts:
   - first mark as deprecated in docs;
   - then replace with thin `.cmd` wrappers if useful;
   - remove business logic only after one final clean-room `pmanager workflow
     windows-phase1` validation.
3. Update or split `docs/build-flow.md` and `docs/validation-matrix.md` so they
   explicitly describe the Python-first Windows path as validated.
4. Add a Linux/Ubuntu Python-first workflow:
   - reuse `pmanager fetch vtk`;
   - validate `pmanager build vtk --configure/build/install/wheel` for
     `linux-x86_64-gcc-py312-release`;
   - validate `pmanager sync venv`;
   - validate runtime provenance and import order.
5. Consider whether the target venv should continue installing `pmanager` and
   test tooling, or whether runtime venvs should become more minimal later.
6. Only after VTK is stable on Windows and Linux, revisit the library registry
   for future third-party libraries. Keep VTK concrete for now.

## Suggested first prompt for the next session

Use this prompt to continue smoothly:

```text
Please read AI_HANDOFF.md, README.md, docs/python-first-dev-env.md, and
docs/windows-from-scratch.md. The Windows Python-first workflow has been
validated through pmanager workflow windows-phase1. Continue from the handoff:
review the current state, then propose and implement the next small step toward
retiring the old PowerShell scripts or validating Ubuntu, without over-
abstracting the multi-library design.
```
