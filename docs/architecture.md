# Architecture

## Core model

The repository uses one VTK build exposed through two explicit authorities:

- Compile-time authority: `external/install/vtk-9.3.1/<target>/sdk/`
- Runtime authority: `.venvs/<target>/.../site-packages/`

## Package roles

- `packages/codecpp`: native C++/SWIG package, built against SDK, loaded against venv runtime
- `packages/codepy`: pure Python package using `pyvista` in the same venv
- `packages/pmanager`: fetch/build/sync/validate orchestrator

## Non-negotiable rules

- Never trust global `PATH`, `PYTHONPATH`, `VTK_DIR`, `CMAKE_PREFIX_PATH`, or loader variables.
- Runtime imports must not depend on SDK runtime paths.
- Build and runtime trees stay independently inspectable.
