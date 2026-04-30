# AGENTS.md

## Document map

| File | Audience | Purpose |
| --- | --- | --- |
| README.md | Package developers (`codecpp`, `codepy`) | How to use the current `pmanager` workflow |
| AGENTS.md | AI build-system maintainers | How to change the multi-platform build system safely |

## Scope

This file is for AI agents maintaining build orchestration and `pmanager`.

In scope:

- fetch/build/install/wheel/sync/validate orchestration
- environment sanitization and reproducibility
- target modeling and platform-specific build behavior
- build-system documentation maintenance

Out of scope:

- feature work inside `packages/codecpp` business logic
- feature work inside `packages/codepy` business logic
- application-level simulation behavior

## System invariants

1. Compile-time and runtime authority stay separate.
2. Build inputs are explicit and target-specific.
3. Runtime provenance points to the target venv.
4. Global shell state is untrusted.

Compile-time authority:

```text
external/install/vtk-9.3.1/<target>/sdk/
```

Runtime authority:

```text
.venvs/<target>/.../site-packages/
```

## Supported targets

- `win-amd64-msvc2022-py310-release`
- `linux-x86_64-gcc-py312-release`

## Build-system responsibilities

`pmanager` owns:

- source fetch
- cmake configure/build/install
- wheel generation
- target venv sync
- validation execution (`audit`, `provenance`, `import-order`)

## Safety rules for AI changes

- Never introduce hidden dependency on global `VTK_DIR`, `CMAKE_PREFIX_PATH`, `PYTHONPATH`, `LD_LIBRARY_PATH`, or SDK `bin` directories.
- Keep paths target-specific and inspectable.
- Keep workflow steps runnable independently.
- Keep Windows/Linux parity in command behavior and docs.
- Prefer small, reversible changes with tests.

## Required checks after workflow/build changes

1. `pmanager validate audit --mode strict`
2. `pmanager validate provenance`
3. `pmanager validate import-order --require-extension`
4. `pytest tests/`

## Change policy

When changing build/sync/workflow logic:

1. update code
2. update tests
3. update active docs outside `docs/legacy/`
4. keep migration history in `docs/legacy/` only

Documentation convention for Python code lives in:

- `docs/code-documentation-style.md`

## Evolution direction

- Keep VTK as the concrete baseline recipe
- Add new external library recipes only after preserving current invariants
- Keep shell scripts as thin wrappers around Python orchestration
