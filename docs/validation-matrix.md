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

## Negative validation

- polluted `PYTHONPATH` must be detected
- polluted loader paths must be detected
- unmanaged `vtk` outside the venv must be reported
