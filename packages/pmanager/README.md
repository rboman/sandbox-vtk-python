# pmanager

Python-first orchestrator for fetch/build/sync/validate workflows.

## Quick start

### Windows

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

## Command groups

- `pmanager fetch vtk`
- `pmanager build vtk`
- `pmanager sync venv`
- `pmanager validate ...`
- `pmanager workflow windows|linux`
