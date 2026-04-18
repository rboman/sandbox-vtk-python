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
