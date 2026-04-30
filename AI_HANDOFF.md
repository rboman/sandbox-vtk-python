# AI Handoff

Last updated: 2026-04-30

## Current operational state

`pmanager` provides Python-first multi-platform orchestration.

Primary workflow commands:

- `pmanager workflow windows`
- `pmanager workflow linux`

## Invariants

Compile-time authority:

```text
external/install/vtk-9.3.1/<target>/sdk/
```

Runtime authority:

```text
.venvs/<target>/.../site-packages/
```

Validation must keep passing:

- `pmanager validate audit --mode strict`
- `pmanager validate provenance`
- `pmanager validate import-order --require-extension`

## Guidance for next AI session

Focus on build-system changes only:

- keep strict environment sanitization
- preserve Windows/Linux parity
- update tests with workflow/build/sync changes
- keep active docs concise and behavior-focused
