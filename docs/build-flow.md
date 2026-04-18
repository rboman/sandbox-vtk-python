# Build Flow

## Target naming

Each build target is named by:

`<os>-<arch>-<toolchain>-<python>-<buildtype>`

Phase-1 examples:

- `win-amd64-msvc2022-py310-release`
- `linux-x86_64-gcc-py312-release`

## VTK flow

1. Ensure the source tree exists at `external/src/vtk-9.3.1/`.
2. Create a clean target venv in `.venvs/<target>/`.
3. Run `scripts/validate/audit-environment.py --mode strict`.
4. Configure VTK into `external/build/vtk-9.3.1/<target>/`.
5. Install the SDK into `external/install/vtk-9.3.1/<target>/sdk/`.
6. Build a local wheel into `external/wheelhouse/vtk-9.3.1/<target>/`.
7. Write a manifest describing the exact build inputs.

The repository must not assume that the produced wheel version string is exactly `9.3.1`.
Current VTK builds may emit a wheel such as `vtk-9.3.1.dev0-...whl`.
The sync scripts therefore install the actual wheel file first, detect the installed version, and then constrain `pyvista` against that exact local VTK runtime.

On Windows, the sync step also stages the VTK runtime DLLs from the matching SDK build into the target venv so that `import vtk` succeeds without relying on the SDK path.

### Windows backend selection

On Windows, `scripts/windows/build-vtk.ps1` now behaves as follows:

- prefer `Ninja` when `ninja` is available
- initialize a fresh MSVC toolchain environment through `VsDevCmd.bat` before a Ninja build
- fall back to the Visual Studio generator if Ninja is unavailable
- always build in parallel

If the build directory already contains a configured `CMakeCache.txt`, the script reuses that generator and refuses silent backend switching. This avoids corrupting an in-progress build tree.

## `codecpp` flow

1. Activate or select the same target venv used to build the wheel.
2. Install the local `vtk` wheel into the venv.
3. Install `pyvista` under the matching constraints file.
4. Build `packages/codecpp` against the SDK install tree for the same target.
5. Install `packages/codecpp` into the venv.
6. Run import-order and provenance validation.

## Explicit anti-patterns

- Do not set machine-global `VTK_DIR`.
- Do not rely on `python` or `cmake` discovered from a random shell.
- Do not import VTK in Python via `PYTHONPATH` pointing at the SDK install tree.
- Do not put `external/install/.../sdk/bin` on a long-lived global `PATH`.
