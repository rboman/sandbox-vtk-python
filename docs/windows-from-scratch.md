# Windows From-Scratch Validation

This document records the full Windows phase-1 procedure from a fresh clone.

It assumes:

- Windows 11
- Visual Studio 2022 with C++ toolchain installed
- Python 3.10 available as `C:\Python310\python.exe`
- `ninja` available in `PATH`
- Qt runtime available at `C:\local\qt\bin` or discoverable through `QTDIR`/`Qt5_DIR`
- SWIG should be also present
  
The goal is to validate, from scratch, that:

- VTK 9.3.1 builds from source
- a local Windows `vtk` wheel is generated
- the wheel installs into a repo-local venv
- `pyvista` installs against that local VTK runtime
- `codecpp` and `pyvista` import in both orders in one process
- runtime DLLs resolve from the venv, not from the SDK tree

## Recommended clean-room strategy

Do the first full rerun in a **fresh clone directory**, not in a working tree that already contains:

- `external/build/...`
- `external/install/...`
- `external/wheelhouse/...`
- `.venvs/...`

That gives the strongest evidence that the workflow is self-contained.

Example:

```powershell
cd D:\dev\VIBECODING
git clone <your-new-github-repo-url> sandbox-vtk-python-fresh
cd .\sandbox-vtk-python-fresh
```

## 1. Create the target venv

```powershell
C:\Python310\python.exe -m venv .venvs\win-amd64-msvc2022-py310-release
```

You do **not** need to activate the venv globally. All supported commands call the target interpreter explicitly.

## 2. Fetch the VTK source tree

Use the repo helper:

```powershell
.\scripts\windows\fetch-vtk-source.cmd
```

This wrapper calls PowerShell with `-ExecutionPolicy Bypass`, which avoids failures on machines where direct `.ps1` execution is disabled.

On Windows, the helper now prefers `tar.exe` instead of `Expand-Archive`, because it is usually much faster on large source archives.

After that, the repository expects the VTK source tree at:

```text
external\src\vtk-9.3.1\
```

If you need to replace an existing extracted tree, run:

```powershell
.\scripts\windows\fetch-vtk-source.cmd -Force
```

FIXME: Download is still **very** slow, we should use "curl" in the future, if found on the system.

## 3. Enter the sanitized repo shell

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\enter-clean-dev-shell.ps1 -Target win-amd64-msvc2022-py310-release
```

This step is important even on a machine that already has old VTK, Qt, or Python-related environment variables configured globally.

## 4. Audit the environment before building

```powershell
.\.venvs\win-amd64-msvc2022-py310-release\Scripts\python.exe .\scripts\validate\audit-environment.py --mode strict --target-venv .\.venvs\win-amd64-msvc2022-py310-release
```

Expected result:

- `No violations detected.`

If this fails, fix the environment first. Do not continue to the build stage with a dirty audit result.

## 5. Build VTK and generate the local wheel

```powershell
& .\scripts\windows\build-vtk.ps1 -Target win-amd64-msvc2022-py310-release -PythonExe .\.venvs\win-amd64-msvc2022-py310-release\Scripts\python.exe
```

What this step does:

- configures VTK with the repo-selected broad feature set
- prefers `Ninja` automatically when available
- builds VTK
- installs the SDK into `external\install\vtk-9.3.1\win-amd64-msvc2022-py310-release\sdk`
- generates a local wheel into `external\wheelhouse\vtk-9.3.1\win-amd64-msvc2022-py310-release`

FIXME: Problème actuel:
"""
/sdk/vtk-9.3.1.data/headers/cmake/VTKPython-targets-release.cmake
-- Installing: D:/dev/VIBECODING/sandbox-vtk-python/external/install/vtk-9.3.1/win-amd64-msvc2022-py310-release/sdk/vtk-9.3.1.data/share/licenses/VTK/Copyright.txt
python.exe : Traceback (most recent call last):
At D:\dev\VIBECODING\sandbox-vtk-python\scripts\windows\build-vtk.ps1:193 char:9
+         & $PythonPath "-c" "import wheel.bdist_wheel" 2>$null
+         ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: (Traceback (most recent call last)::String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
"""
Le package Wheel n'est pas installé dans l'environnement. Et il ne s'installe pas automatiquement.

L'installation manuelle de wheel dans la venv provoque la compilation de 6293 fichiers lorsqu'on relance le script!

FIXME: Problème moins grave: pip n'est pas upgradé dans la venv


Expected artifact:

```text
external\wheelhouse\vtk-9.3.1\win-amd64-msvc2022-py310-release\vtk-9.3.1.dev0-cp310-cp310-win_amd64.whl
```

Note:

- The current VTK build emits `9.3.1.dev0`, not plain `9.3.1`.
- The repo workflow now accounts for that automatically.

## 6. Sync the target venv

```powershell
& .\scripts\windows\sync-venv.ps1 -Target win-amd64-msvc2022-py310-release
```

What this step does:

- installs the local VTK wheel into the venv
- stages VTK runtime DLLs into `site-packages\bin`
- writes `vtkmodules\_build_paths.py` so VTK can add the Qt runtime directory
- installs `pyvista`
- builds and installs `codecpp`
- installs `codepy` and `pmanager`

Expected outcome:

- successful completion with no runtime-path error

## 7. Validate runtime provenance

```powershell
.\.venvs\win-amd64-msvc2022-py310-release\Scripts\python.exe .\scripts\validate\runtime-provenance.py --target-venv .\.venvs\win-amd64-msvc2022-py310-release --target-sdk-root .\external\install\vtk-9.3.1\win-amd64-msvc2022-py310-release\sdk
```

Expected result:

- module origins printed for `vtk`, `pyvista`, and `codecpp`
- final line:

```text
Runtime provenance OK: vtk/codecpp native libraries are resolved from the target venv and not from the SDK tree.
```

## 8. Validate import order

```powershell
.\.venvs\win-amd64-msvc2022-py310-release\Scripts\python.exe .\scripts\validate\import-order.py --require-extension
```

Expected result:

```text
Order ['codecpp', 'pyvista']: returncode=0
Order ['pyvista', 'codecpp']: returncode=0
```

## 9. Run one manual sanity check

```powershell
.\.venvs\win-amd64-msvc2022-py310-release\Scripts\python.exe -c "import vtk, pyvista, codecpp; codecpp.require_extension(); print(vtk.vtkVersion.GetVTKVersion()); print(codecpp.describe_runtime())"
```

Expected result:

- VTK version prints successfully
- `codecpp.describe_runtime()` reports a runtime rooted in the target venv

## 10. Optional final inspection

To inspect the staged runtime layout in the venv:

```powershell
Get-ChildItem .\.venvs\win-amd64-msvc2022-py310-release\Lib\site-packages\bin | Select-Object -First 20 Name
Get-ChildItem .\.venvs\win-amd64-msvc2022-py310-release\Lib\site-packages\vtkmodules\_build_paths.py
```

## If the rerun succeeds

Then Windows phase 1 can be considered validated from a fresh clone.

At that point, the next most useful task is to repeat the same idea on Ubuntu.

## If the rerun fails

Capture and keep:

- the exact command
- the last 50 to 100 lines of output
- whether the failure happened during:
  - audit
  - VTK configure
  - VTK build
  - wheel generation
  - `sync-venv`
  - runtime provenance
  - import order
