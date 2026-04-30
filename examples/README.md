# examples

Examples in this directory are for validation and observation, not application features.

These examples validate that the complete workflow produces a functional environment.

## Running examples

After running `pmanager workflow <platform>-phase1`, activate the target venv and run:

**Windows:**
```bat
.venvs\win-amd64-msvc2022-py310-release\Scripts\activate.bat
cd examples
python import_both.py
python show_runtime.py
```

**Linux:**
```bash
source .venvs/linux-x86_64-gcc-py312-release/bin/activate
cd examples
python import_both.py
python show_runtime.py
```

## Example scripts

- `import_both.py` — Import `codecpp` and `pyvista` in both orders to verify coexistence
- `show_runtime.py` — Display the active VTK runtime origin and loaded library locations
