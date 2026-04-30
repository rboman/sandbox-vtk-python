# Python-first development environment

This document describes the current day-to-day workflow based on `pmanager`.

## Purpose

Use a dedicated tooling venv (`.venvs/pmanager-dev`) to orchestrate target builds
and target runtime venvs.

Keep compile-time and runtime concerns explicit:

- compile-time: `external/install/vtk-9.3.1/<target>/sdk/`
- runtime: `.venvs/<target>/.../site-packages/`

## Supported targets

- `win-amd64-msvc2022-py310-release`
- `linux-x86_64-gcc-py312-release`

## Bootstrap

### Windows (`cmd.exe`)

```bat
python scripts\bootstrap-dev-env.py
.venvs\pmanager-dev\Scripts\activate.bat
```

### Linux

```bash
python scripts/bootstrap-dev-env.py
source .venvs/pmanager-dev/bin/activate
```

## Current command surface

```text
pmanager targets
pmanager fetch vtk
pmanager build vtk --configure
pmanager build vtk --build
pmanager build vtk --install
pmanager build vtk --wheel
pmanager sync venv
pmanager validate audit --mode strict
pmanager validate provenance
pmanager validate import-order --require-extension
pmanager workflow windows-phase1
pmanager workflow linux-phase1
```

## Recommended workflow

### Full workflow (preferred)

- Windows: `pmanager workflow windows-phase1`
- Linux: `pmanager workflow linux-phase1`

### Step-by-step workflow (debug)

1. `pmanager fetch vtk`
2. `pmanager build vtk --configure`
3. `pmanager build vtk --build`
4. `pmanager build vtk --install`
5. `pmanager build vtk --wheel`
6. `pmanager sync venv`
7. `pmanager validate provenance`
8. `pmanager validate import-order --require-extension`

## Environment hygiene contract

`pmanager` execution sanitizes unsafe environment variables and constrains runtime
resolution to the target venv.

Validation commands must keep passing in strict mode:

- audit
- provenance
- import-order

## Future evolution

- keep shell scripts as thin wrappers
- preserve Windows/Linux parity in behavior and documentation
- add new external library recipes only after preserving current VTK invariants
- keep runtime provenance checks mandatory for any workflow change
