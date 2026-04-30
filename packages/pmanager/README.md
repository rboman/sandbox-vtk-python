# pmanager

Python-first orchestrator for the VTK sandbox project.

## Status

Current operational scope:

- ✅ Environment auditing with strict safety checks
- ✅ Automatic target discovery (Windows/Linux, Python 3.10/3.12)
- ✅ VTK source fetching with validation
- ✅ CMake configuration and build with backend selection
- ✅ VTK SDK installation and Python wheel generation
- ✅ Target venv creation and package synchronization
- ✅ Complete runtime validation (audit, provenance, import order)
- ✅ End-to-end workflows for Windows and Linux

## Quick start

### Windows

```bat
python scripts\bootstrap-dev-env.py
.venvs\pmanager-dev\Scripts\activate.bat
pmanager workflow windows-phase1
```

### Linux

```bash
python scripts/bootstrap-dev-env.py
source .venvs/pmanager-dev/bin/activate
pmanager workflow linux-phase1
```

## Command reference

- `pmanager fetch vtk` — Fetch VTK 9.3.1 sources
- `pmanager build vtk` — Print build plan or run build steps
- `pmanager sync venv` — Install local wheel and packages into target venv
- `pmanager validate` — Audit and validate environment and runtime
- `pmanager workflow` — Run complete phase-1 sequence
