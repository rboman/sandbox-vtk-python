# Validation Matrix

## Environment audit

- detect unsafe variables
- detect unmanaged `site-packages` entries
- detect a pre-installed `vtk` outside the target venv
- record interpreter and venv identity

## Native build validation

- VTK configure arguments match the expected broad profile
- SDK install tree exists in the target-specific location
- VTK manifest records Python executable, generator, install root, and wheel output

## Python packaging validation

- local `vtk` wheel installs from the repo wheelhouse
- `pyvista` installs under constraints
- no dependency resolution silently replaces `vtk==9.3.1`

## Runtime validation

- `import codecpp; import pyvista`
- `import pyvista; import codecpp`
- `vtk.vtkVersion.GetVTKVersion()` reports `9.3.1`
- loaded VTK libraries originate from the target venv
- no VTK library originates from the SDK tree

### Windows phase-1 runtime contract

- target: `win-amd64-msvc2022-py310-release`
- workflow: `pmanager workflow windows-phase1`
- local wheel uses the `vtk-9.3.1.dev0-...` naming pattern
- `pmanager sync venv` installs that wheel, stages runtime DLLs into `site-packages/bin`, and writes `vtkmodules/_build_paths.py`
- `pmanager validate provenance` is required to pass
- `pmanager validate import-order --require-extension` is required to pass in both import orders
- `codecpp` extension module compiles and loads
- all three imports (vtk, pyvista, codecpp) coexist in one process

### Linux phase-1 runtime contract

- target: `linux-x86_64-gcc-py312-release`
- workflow: `pmanager workflow linux-phase1`
- local wheel uses the `vtk-9.3.1.dev0-...` naming pattern
- `pmanager sync venv` installs that wheel and all dependencies
- `pmanager validate provenance` is required to report VTK runtime libraries from the target venv
- `pmanager validate import-order --require-extension` is required to pass in both import orders
- `codecpp` extension module compiles via SWIG and loads without relying on global `/opt` paths
- environment sanitization (strict whitelist PATH) prevents pollution from global VTK installations
- all three imports (vtk, pyvista, codecpp) coexist in one process

### Windows runtime layout expectation

- `vtk.py` and `vtkmodules/` live in `site-packages`
- VTK runtime DLLs live in `site-packages/bin`
- Qt runtime hints live in `site-packages/vtkmodules/_build_paths.py`
- `codecpp` uses the same venv runtime and must not depend on `external/install/.../sdk/bin` at import time

## Negative validation

- polluted `PYTHONPATH` must be detected
- polluted loader paths must be detected
- unmanaged `vtk` outside the venv must be reported
