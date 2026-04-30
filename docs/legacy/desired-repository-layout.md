# Desired repository layout

## Main top-level areas

- `external/` for third-party sources, builds, installs, wheels
- `packages/codecpp/` for native + SWIG package
- `packages/codepy/` for pure Python package
- `packages/pmanager/` for orchestration CLI
- `docs/` for architecture and decisions
- `examples/` for runtime validation scripts
- `tests/` for automated checks

## Principle

The repository must remain explicit about:
- source trees
- build trees
- install trees
- wheel artifacts
- package boundaries
