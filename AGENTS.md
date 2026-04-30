# AGENTS.md

## Repository purpose

This repository is a cross-platform sandbox for a mixed C++ / Python project using a custom-built VTK.

The purpose is to validate architecture, packaging, and runtime behavior.
Functional demo code is intentionally trivial.

## Primary goals

- build VTK 9.3.1 from source
- use it for native C++ compilation
- generate a matching local Python wheel for `vtk`
- install that wheel into a virtual environment
- use `pyvista` in the same environment
- validate that `codecpp` and `pyvista` can coexist in one Python process

## Platforms

- Windows with Visual Studio 2022
- Ubuntu/Linux

Both are important from the beginning.

## Initial technology choices

- CMake
- SWIG
- pyproject.toml
- venv + pip
- typer for future CLI orchestration

## Important architectural rule

Compile-time and run-time concerns must remain explicit.

The repository should distinguish:
1. a native SDK/install tree used for C++ compilation
2. a Python wheel/runtime used inside the venv

## Runtime rule

At Python runtime, `codecpp`, `vtk`, and `pyvista` must resolve to one coherent VTK runtime.

## Planning rule

Do not rush into implementation.
Prefer:
- explicit documentation
- directory layout
- validation strategy
- import-order tests
- DLL/shared-library provenance checks

## What to avoid

- hardcoded Python-version-specific site-packages paths
- accidental dependence on a globally installed VTK
- mixing native SDK binaries and venv runtime binaries without documenting it
- premature large code generation
- unnecessary empty boilerplate files

## Phase-1 status

**COMPLETED AND VALIDATED** ✅

Both Windows and Linux phase-1 workflows are fully operational:

- ✅ Repository structure is stable and well-documented
- ✅ VTK build/runtime strategy is explicit and proven on both platforms
- ✅ Validation matrix is complete (audit, provenance, import-order)
- ✅ Implementation order is proven in practice

### Validated outcomes

- **Windows**: `pmanager workflow windows-phase1` succeeds end-to-end with target `win-amd64-msvc2022-py310-release`
- **Linux**: `pmanager workflow linux-phase1` succeeds end-to-end with target `linux-x86_64-gcc-py312-release`
- Both platforms: VTK wheel generated, installed into venv, codecpp compiled and loaded, pyvista importable
- Both platforms: provenance validation confirms all VTK runtime libraries loaded from venv, not SDK tree
- Both platforms: codecpp and pyvista coexist without runtime conflicts