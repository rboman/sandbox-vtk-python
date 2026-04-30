# Build Flow

## Target naming

Each build target is named by:

`<os>-<arch>-<toolchain>-<python>-<buildtype>`

Phase-1 examples:

- `win-amd64-msvc2022-py310-release`
- `linux-x86_64-gcc-py312-release`

## VTK flow (both platforms)

The following steps are executed automatically by `pmanager workflow <platform>-phase1`:

1. Ensure the source tree exists at `external/src/vtk-9.3.1/`.
2. Create a clean target venv in `.venvs/<target>/`.
3. Run environment audit with strict mode.
4. Configure VTK into `external/build/vtk-9.3.1/<target>/`.
5. Install the SDK into `external/install/vtk-9.3.1/<target>/sdk/`.
6. Build a local wheel into `external/wheelhouse/vtk-9.3.1/<target>/`.
7. Write a manifest describing the exact build inputs.

The repository correctly handles wheel version strings that may include `.dev0` (for example, `vtk-9.3.1.dev0-...whl`).
The sync step installs the actual wheel file first, detects the installed version, and then constrains `pyvista` against that exact local VTK runtime.

On Windows, `pmanager sync venv` also stages the VTK runtime DLLs from the matching SDK build into the target venv so that `import vtk` succeeds without relying on the SDK path.

### Windows backend selection

On Windows, `pmanager build vtk` behaves as follows:

- prefer `Ninja` when `ninja` is available
- require a Visual Studio developer `cmd.exe` prompt for Ninja/MSVC builds
- fall back to the Visual Studio generator if Ninja is unavailable
- always build in parallel

If the build directory already contains a configured `CMakeCache.txt`, `pmanager` reuses that generator and refuses silent backend switching. This avoids corrupting an in-progress build tree.

### Windows workflow

```bat
pmanager workflow windows-phase1
```

This command runs the complete Windows sequence:

- Fetch, configure, build, and install VTK SDK for `win-amd64-msvc2022-py310-release`
- Generate the local `vtk` wheel (`vtk-9.3.1.dev0-cp310-cp310-win_amd64.whl`)
- Create and populate the target venv
- Install the wheel and stage VTK runtime DLLs into `site-packages/bin`
- Install pyvista, codecpp, codepy, and pmanager packages
- Validate provenance and import order

### Linux workflow

```bash
pmanager workflow linux-phase1
```

This command runs the complete Linux sequence:

- Fetch, configure, build, and install VTK SDK for `linux-x86_64-gcc-py312-release`
- Generate the local `vtk` wheel (`vtk-9.3.1.dev0-cp312-cp312-linux_x86_64.whl`)
- Create and populate the target venv
- Install the wheel with automatic SWIG detection for codecpp compilation
- Install pyvista, codecpp, codepy, and pmanager packages
- Validate provenance (all 293+ VTK libraries from venv, none from SDK tree)
- Validate import order in both directions

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
