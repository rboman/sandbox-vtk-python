# Architecture

## Goal

The repository proves that one custom VTK build can support two distinct but coherent views:

- a **native SDK view** used for C++ compilation
- a **Python wheel/runtime view** used inside a venv

The key success condition is that `codecpp` and `pyvista` can be imported in the same Python process while resolving to one coherent VTK runtime.

## Authority boundaries

### Compile-time authority

Compile-time VTK lives in:

- `external/install/vtk-9.3.1/<target>/sdk/`

This tree is the only supported source for:

- headers
- import/static libraries
- VTK CMake package config
- manifest metadata used by native builds

### Runtime authority

Runtime Python VTK lives in:

- `.venvs/<target>/.../site-packages`

This venv-installed wheel is the only supported source for:

- `vtk`
- `vtkmodules`
- runtime DLL/shared library resolution during Python execution

## Package roles

### `packages/codecpp`

- Native C++ code using VTK.
- SWIG bindings exposed into Python.
- Build-time consumer of the repo-managed VTK SDK.
- Runtime consumer of the venv-installed VTK wheel.

### `packages/codepy`

- Pure Python package using `pyvista`.
- Shares the same venv and therefore the same `vtk` wheel runtime as `codecpp`.

### `packages/pmanager`

- Future Typer-based orchestrator.
- Phase 1 only requires a CLI skeleton and stable command surface for later automation.

## Non-negotiable constraints

- Global `PATH`, `PYTHONPATH`, `LD_LIBRARY_PATH`, `CMAKE_PREFIX_PATH`, and `VTK_DIR` are never trusted.
- Scripts must construct the environment they need.
- A successful import must remain successful after removing hidden global path injections.
- SDK and runtime trees must be independently inspectable.
