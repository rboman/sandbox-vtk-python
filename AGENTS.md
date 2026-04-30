# AGENTS.md

## Audience and scope

This file targets AI agents that maintain the multi-platform build system and `pmanager`.

In scope:

- fetch/build/install/wheel/sync/validate orchestration
- environment sanitization and reproducibility
- target modeling and platform behavior
- documentation for build mechanics

Out of scope:

- feature development inside `codecpp` business logic
- feature development inside `codepy` business logic
- application-level simulation behavior

## System contract

1. Compile-time authority and runtime authority stay separate.
2. Build inputs are explicit and target-specific.
3. Runtime provenance always points to the target venv.
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

`pmanager` is the primary orchestrator and owns:

- source fetch
- cmake configure/build/install
- wheel generation
- target venv sync
- validation execution (`audit`, `provenance`, `import-order`)

## Safety rules for AI changes

- Never introduce hidden dependence on global `VTK_DIR`, `CMAKE_PREFIX_PATH`, `PYTHONPATH`, `LD_LIBRARY_PATH`, or SDK `bin` directories.
- Keep path construction target-specific and inspectable.
- Keep workflow steps runnable independently for debugging.
- Keep Windows and Linux parity in command design and docs.
- Prefer small, reversible changes with tests.

## Validation requirements

Any change to build/sync/workflow logic keeps these checks green:

1. `pmanager validate audit --mode strict`
2. `pmanager validate provenance`
3. `pmanager validate import-order --require-extension`
4. unit tests under `tests/`

## Change policy

When updating the build system:

1. update code
2. update tests
3. update active docs outside `docs/legacy/`
4. keep migration history in `docs/legacy/` only

## Evolution direction

- keep VTK as the concrete baseline recipe
- add new external libraries only after preserving current invariants
- keep shell scripts thin wrappers around Python orchestration