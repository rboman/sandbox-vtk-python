# codecpp

Native C++ + SWIG package that compiles against the repo-managed VTK SDK and resolves VTK at Python runtime from the active venv.

## Phase-1 packaging rules

- build backend: `scikit-build-core`
- native build system: CMake
- binding tool: SWIG
- development install: non-editable

## Runtime rule

`codecpp` must not rely on the SDK install tree at Python runtime.

On Windows, `codecpp/__init__.py` bootstraps DLL lookup through `os.add_dll_directory(...)`.

On Linux, `_codecpp.so` carries a `RUNPATH` that points at the venv-installed VTK wheel layout.
