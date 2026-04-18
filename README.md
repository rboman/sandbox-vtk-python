# sandbox-vtk-python

Sandbox cross-platform (Windows + Ubuntu) for a mixed C++ / Python project using a custom-built VTK 9.3.1.

## Problem

A native C++ library (`codecpp`) uses VTK and is exposed to Python via SWIG.
A pure Python package (`codepy`) uses PyVista.

The key risk is loading incompatible VTK runtimes in the same Python process:
- one coming from `pyvista` / `vtk`
- another one coming from the native build used by `codecpp`

## Goal

Design a repository and workflow proving that:
- VTK can be built from source
- a native SDK view can be used for C++ compilation
- a matching local Python wheel can be installed into a venv
- `codecpp` and `pyvista` can coexist in the same Python process

## Constraints

- VTK version: 9.3.1
- Platforms: Windows and Ubuntu
- First Python target: 3.10
- Windows compiler: Visual Studio 2022
- Python env management: venv + pip
- First binding technology: SWIG
- Local wheelhouse is acceptable
- Public PyPI publication is not required
- `pmanager` only needs a skeleton in v1

## Current status

An Ubuntu workflow already exists for:
- building VTK from source
- enabling Python wrapping
- enabling VTK wheel build
- creating a local wheel
- installing VTK into `/opt/vtk-9.3.1`

See `scripts/reference/ubuntu/` and `docs/existing-linux-workflow.md`.
