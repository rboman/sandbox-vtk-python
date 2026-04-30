# Validation Matrix

## Required checks

1. Environment audit (strict)
2. Native build outputs (SDK + wheel)
3. Python packaging sync (local wheel + constrained pyvista)
4. Runtime provenance
5. Import order (`codecpp -> pyvista` and `pyvista -> codecpp`)

## Runtime pass criteria

- `vtk.vtkVersion.GetVTKVersion()` reports `9.3.1`
- VTK-related runtime libraries resolve from target venv
- No VTK runtime library resolves from `external/install/.../sdk`
