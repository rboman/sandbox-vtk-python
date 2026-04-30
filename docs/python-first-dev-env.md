# Python-first Development Environment

## Purpose

Use `pmanager` from `.venvs/pmanager-dev` to build and validate target environments.

## Setup

### Windows

```bat
python scripts\bootstrap-dev-env.py
.venvs\pmanager-dev\Scripts\activate.bat
call scripts\windows\vsdev.cmd
```

Use `call scripts\windows\vsdev.cmd` before build or workflow commands when using the Ninja backend so `cl.exe` and related MSVC tools are available in the current terminal.

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
call scripts\windows\vsdev.cmd   (Windows + Ninja)
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
