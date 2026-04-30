# codecpp

Native C++ + SWIG package built against the repo-managed VTK SDK and loaded against VTK from the active target venv.

## Packaging rules

- backend: `scikit-build-core`
- native build: CMake
- binding tool: SWIG
- install mode in target venv: non-editable

## Runtime rule

`codecpp` does not use SDK runtime paths.

- Windows: `codecpp/__init__.py` configures DLL lookup via `os.add_dll_directory(...)`
- Linux: `_codecpp.so` uses RUNPATH entries for the venv-installed wheel layout
