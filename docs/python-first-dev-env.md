# Python-first Development Environment

## Purpose

Use `pmanager` from `.venvs/pmanager-dev` to build and validate target environments.

## Setup

### Windows

```bat
python scripts\bootstrap-dev-env.py
.venvs\pmanager-dev\Scripts\activate.bat
```

### Linux

```bash
python scripts/bootstrap-dev-env.py
source .venvs/pmanager-dev/bin/activate
```

## Main workflows

- `pmanager workflow windows`
- `pmanager workflow linux`

## Step-by-step debug workflow

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
