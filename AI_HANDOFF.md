# AI handoff

Last updated: 2026-04-30

## Active state

The repository runs a Python-first multi-platform build orchestration through
`pmanager`.

Supported workflows:

- `pmanager workflow windows-phase1`
- `pmanager workflow linux-phase1`

Both workflows execute:

1. fetch
2. configure
3. build
4. install SDK
5. build wheel
6. sync target venv
7. validate provenance and import order

## Architecture invariants

Compile-time authority:

```text
external/install/vtk-9.3.1/<target>/sdk/
```

Runtime authority:

```text
.venvs/<target>/.../site-packages/
```

Runtime validation requirement:

- VTK-related libraries resolve from the target venv
- SDK tree is compile-time only

## Current command set

```text
pmanager fetch vtk
pmanager build vtk --configure
pmanager build vtk --build
pmanager build vtk --install
pmanager build vtk --wheel
pmanager sync venv
pmanager validate audit --mode strict
pmanager validate provenance
pmanager validate import-order --require-extension
pmanager workflow windows-phase1
pmanager workflow linux-phase1
```

## Guidance for next AI session

Focus on build-system and orchestration changes only:

- keep environment sanitization strict
- preserve Windows/Linux parity
- keep docs outside `docs/legacy/` aligned with current behavior
- update tests with every workflow/build/sync change

Do not treat this file as a migration log. Keep it as a compact operational
snapshot plus near-term build-system direction.
