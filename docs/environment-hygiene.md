# Environment Hygiene

## Why

Developer machines often contain unmanaged SDKs and Python packages. Build and runtime behavior must remain reproducible without hidden global help.

## Unsafe variables (default)

- Python: `PYTHONPATH`, `PYTHONHOME`, `PYTHONSTARTUP`, `VIRTUAL_ENV` (mismatch), `PIP_*`
- Native/CMake: `CMAKE_PREFIX_PATH`, `VTK_DIR`, `CMAKE_TOOLCHAIN_FILE`, `INCLUDE`, `LIB`, `LIBRARY_PATH`, `CPATH`
- Loader: `PATH`, `LD_LIBRARY_PATH`, `DYLD_LIBRARY_PATH`
- Managers: `CONDA_PREFIX`, `CONDA_DEFAULT_ENV`

## Policy

- Run strict audit in repo workflows.
- Force `PYTHONNOUSERSITE=1` in managed validation.
- Treat global environment dependence as a bug.
