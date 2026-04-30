# examples

Validation helpers, not application features.

## Run

After a successful target workflow, activate the target venv and run:

### Windows

```bat
.venvs\win-amd64-msvc2022-py310-release\Scripts\activate.bat
cd examples
python import_both.py
python show_runtime.py
```

### Linux

```bash
source .venvs/linux-x86_64-gcc-py312-release/bin/activate
cd examples
python import_both.py
python show_runtime.py
```

## Scripts

- `import_both.py`: verifies both import orders
- `show_runtime.py`: prints runtime origin details
