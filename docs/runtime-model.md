# Runtime Model

## Rule

During Python execution, `vtk`, `pyvista`, and `codecpp` resolve to VTK from the target venv.

The SDK tree is compile-time only.

## Windows

- `codecpp/__init__.py` registers runtime DLL directories before loading `_codecpp.pyd`
- `pmanager sync venv` stages VTK runtime DLLs in `site-packages/bin`
- optional Qt paths are written to `vtkmodules/_build_paths.py`

## Linux

`_codecpp.so` must carry RUNPATH entries for the venv wheel layout:

- `$ORIGIN`
- `$ORIGIN/..`
- `$ORIGIN/../vtkmodules`
- `$ORIGIN/../vtk.libs`

`LD_LIBRARY_PATH` is diagnostic-only.
