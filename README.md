# sandbox-vtk-python

Cross-platform sandbox for a mixed C++ / Python project using a custom-built VTK 9.3.1.

## Project context

This repository is intended for day-to-day numerical simulation work in a university
laboratory setting.

The target audience is small: one main developer, possibly a student or a close
collaborator. The tooling should therefore stay practical and understandable.
It is not meant to become an enterprise build platform with many layers of
fallbacks and policy machinery.

The preferred direction is:

- keep the architecture explicit;
- keep the workflow easy to test step by step;
- assume normal development conveniences such as network access for installing
  basic Python tooling;
- ask before adding large compatibility workarounds;
- favor clear Python code over duplicated PowerShell/Bash logic;
- on Windows, prefer `cmd.exe` commands in user-facing documentation and keep
  PowerShell only as a temporary implementation detail for existing scripts.

The repository exists to prove one architectural point first:

- `codecpp` can compile against a custom VTK SDK;
- a matching local `vtk` wheel can be installed into a venv;
- `codepy` can use `pyvista` in the same environment;
- both can coexist in one Python process without loading two conflicting VTK runtimes.

## Design rules

- Compile-time and runtime concerns stay explicit.
- The user's shell is treated as untrusted until proven otherwise.
- Python runtime VTK comes from the venv wheel, not from the SDK install tree.
- Scripts must detect environment pollution instead of silently benefiting from it.
- Simplicity matters: environment hygiene should protect the numerical workflow,
  not turn the repository into a complex infrastructure project.

## Repository layout

```text
.
|-- constraints/
|-- docs/
|-- examples/
|-- external/
|   |-- build/
|   |-- install/
|   |-- src/
|   `-- wheelhouse/
|-- packages/
|   |-- codecpp/
|   |-- codepy/
|   `-- pmanager/
|-- scripts/
|   |-- ubuntu/
|   |-- validate/
|   `-- windows/
`-- tests/
```

## Supported phase-1 targets

- `win-amd64-msvc2022-py310-release`
- `linux-x86_64-gcc-py312-release`

The repository is intentionally ready for more Python versions later, but these
two targets are the first supported baselines.

## Workflow summary

The preferred Windows workflow is now Python-first:

```bat
python scripts\bootstrap-dev-env.py
.venvs\pmanager-dev\Scripts\activate.bat
pmanager workflow windows-phase1
```

That workflow runs:

1. fetch VTK sources into `external/src/vtk-9.3.1`;
2. create the target venv under `.venvs/<target>/`;
3. configure and build VTK in `external/build/vtk-9.3.1/<target>/`;
4. install the native SDK into `external/install/vtk-9.3.1/<target>/sdk/`;
5. build the local `vtk` wheel into `external/wheelhouse/vtk-9.3.1/<target>/`;
6. install that local wheel into the target venv;
7. install `pyvista` under a dynamic VTK constraint;
8. build/install `packages/codecpp`, `packages/codepy`, and `packages/pmanager`;
9. run provenance and import-order validations.

The individual commands remain available for step-by-step debugging:

```bat
pmanager fetch vtk
pmanager build vtk --configure
pmanager build vtk --build
pmanager build vtk --install
pmanager build vtk --wheel
pmanager sync venv
pmanager validate provenance
pmanager validate import-order
```

The older PowerShell/Bash scripts are still present as migration fallback, but
the project direction is to remove their business logic once Python parity is
fully accepted.

## Why the repository is strict about environment hygiene

This project is explicitly designed for developer machines that may already expose:

- global `PATH` entries for old SDKs;
- `PYTHONPATH` entries pointing to unmanaged packages;
- pre-existing `vtk` packages outside the target venv;
- `VTK_DIR`, `CMAKE_PREFIX_PATH`, `INCLUDE`, or `LIB` values from older native builds.

On such machines, "it works on my machine" is not a success signal. A valid run
must remain correct after:

- clearing global Python path injections;
- removing accidental runtime loader help;
- forcing Python user site packages off;
- constraining CMake and pip inputs to the repo-managed target.

One nuance matters in practice: a sanitized shell can remove inherited
environment variables, but it cannot magically remove packages already installed
in the global interpreter's own `site-packages`.

That is why the supported workflow always moves quickly to a target venv and
treats runs from the global interpreter as diagnostic only.

## Key documents

- `docs/architecture.md`
- `docs/build-flow.md`
- `docs/runtime-model.md`
- `docs/environment-hygiene.md`
- `docs/validation-matrix.md`
- `docs/python-first-dev-env.md`
- `docs/windows-from-scratch.md`
- `docs/decisions/0001-vtk-sdk-vs-python-runtime.md`
- `AI_HANDOFF.md`

## Current implementation scope

The repository now contains:

- architecture and validation documentation;
- target naming and constraints files;
- sanitized shell entry scripts for Windows and Ubuntu;
- Python fetch/build/sync/workflow orchestration in `pmanager`;
- Python audit and provenance utilities;
- a `codecpp` package skeleton using CMake + SWIG + scikit-build-core;
- a `codepy` package skeleton using PyVista;
- a `pmanager` Typer CLI.

The intended `pmanager` direction is Python-first. PowerShell and Bash should
eventually remain only for shell-specific entry points and convenience wrappers.
On Windows, new user-facing commands should be shown for `cmd.exe` by default.

## Current validation status

Windows phase 1 is now validated for:

- building VTK 9.3.1 from source with Python wrapping enabled;
- generating a local Windows wheel and installing it into the target venv;
- installing `pyvista` against that local VTK runtime;
- building and installing `codecpp`;
- importing `codecpp` and `pyvista` in both orders inside the same Python process;
- resolving VTK runtime DLLs from the venv instead of the SDK tree;
- running `pmanager workflow windows-phase1` from a clean repository after
  bootstrapping `.venvs/pmanager-dev`.

Ubuntu remains the next platform to validate end-to-end.
