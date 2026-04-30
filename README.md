# sandbox-vtk-python

Cross-platform VTK sandbox for a mixed C++/Python stack.

## Document map

| File | Audience | Purpose |
| --- | --- | --- |
| README.md | Package developers (`codecpp`, `codepy`) | Daily usage of `pmanager` and package development workflow |
| AGENTS.md | AI build-system maintainers | Build orchestration rules, invariants, and change policy |

## What this repository provides

- Target-specific VTK SDK builds for native compilation
- Target-specific local `vtk` wheels for Python runtime
- Target virtual environments under `.venvs/<target>/`
- Python-first orchestration through `pmanager`

## Supported targets

- `win-amd64-msvc2022-py310-release`
- `linux-x86_64-gcc-py312-release`

## Quick start

### Windows (`cmd.exe`)

```bat
python scripts\bootstrap-dev-env.py
.venvs\pmanager-dev\Scripts\activate.bat
pmanager workflow windows
```

### Linux

```bash
python scripts/bootstrap-dev-env.py
source .venvs/pmanager-dev/bin/activate
pmanager workflow linux
```

## Daily commands

```text
pmanager fetch vtk
pmanager build vtk --configure
pmanager build vtk --build
pmanager build vtk --install
pmanager build vtk --wheel
pmanager sync venv
pmanager validate audit --mode strict
pmanager validate provenance
pmanager validate import-order --require-extension
```

## Runtime contract for package developers

Inside a target venv:

- `vtk`, `pyvista`, and `codecpp` resolve to one coherent VTK runtime
- VTK runtime libraries are loaded from the target venv
- `external/install/.../sdk` remains compile-time only

## Where to go next

- `examples/README.md` for quick runtime checks
- `docs/python-first-dev-env.md` for compact operational workflow
- `docs/build-flow.md` for build/sync orchestration details
