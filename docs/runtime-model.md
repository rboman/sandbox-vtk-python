# Runtime Model

## Python runtime rule

During Python execution, `vtk`, `pyvista`, and `codecpp` must resolve to the VTK wheel installed inside the target venv.

The SDK install tree is compile-time only and must not become the active Python runtime by accident.

## Windows strategy

`packages/codecpp/src/codecpp/__init__.py` bootstraps native loading before importing the SWIG-generated wrapper:

1. locate `vtkmodules` in the active interpreter
2. derive candidate DLL directories from the wheel layout
3. register them with `os.add_dll_directory(...)`
4. import the SWIG shadow module, which in turn imports `_codecpp.pyd`

The package must raise a diagnostic error if:

- `vtkmodules` is missing
- the active interpreter is not the intended venv
- runtime DLL directories cannot be determined

In practice, the local VTK wheel generated from source may not embed the VTK runtime DLLs itself on Windows.
The supported repo workflow therefore stages the DLLs from the matching VTK build into `site-packages/bin` during `pmanager sync venv`, which matches the layout expected by `vtkmodules/__init__.py`.
When Qt-enabled VTK modules are present, the workflow also writes `vtkmodules/_build_paths.py` so VTK can add the Qt runtime directory through `os.add_dll_directory(...)`.
That keeps the **effective** runtime origin inside the venv while avoiding dependence on the SDK path at import time.

Phase-1 Windows validation has confirmed that this model works for:

- `vtk`
- `pyvista`
- `codecpp`
- both import orders between `pyvista` and `codecpp`

## Linux strategy

`_codecpp.so` must carry an explicit `RUNPATH` so the loader can resolve VTK from the installed wheel layout.

Phase-1 baseline:

- `$ORIGIN`
- `$ORIGIN/..`
- `$ORIGIN/../vtkmodules`
- `$ORIGIN/../vtk.libs`

`LD_LIBRARY_PATH` is allowed only for manual diagnosis, not as a required runtime mechanism.

## Validation rule

The provenance checks must fail if any loaded `vtk`-related DLL/shared library comes from:

- `external/install/.../sdk`
- a global unmanaged Python installation
- another developer toolchain location outside the active venv
