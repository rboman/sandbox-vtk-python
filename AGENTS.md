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

## Phase-1 success criteria

Phase 1 is successful when:
- the repository structure is agreed
- the VTK build/runtime strategy is explicit
- the validation matrix is explicit
- implementation order is clear