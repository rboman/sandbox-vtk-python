# Build Flow

## Target naming

`<os>-<arch>-<toolchain>-<python>-<buildtype>`

Examples:

- `win-amd64-msvc2022-py310-release`
- `linux-x86_64-gcc-py312-release`

## End-to-end workflow

- Windows: `pmanager workflow windows`
- Linux: `pmanager workflow linux`

Each workflow runs:

1. fetch source
2. prepare target venv
3. configure/build/install VTK SDK
4. build local `vtk` wheel
5. sync target venv
6. run provenance and import-order validation

## Important behavior

- VTK wheel version is detected dynamically (for example `9.3.1.dev0`) and reused for constraints.
- Windows sync stages VTK runtime DLLs into `site-packages/bin`.
- Linux codecpp build environment adds external SWIG path only when needed.
