# ADR 0001: Separate VTK SDK authority from Python runtime authority

## Status

Accepted.

## Decision

The repository treats the native SDK install tree and the Python wheel runtime as two distinct views of the same VTK build:

- `external/install/vtk-9.3.1/<target>/sdk/` is compile-time authority
- the target venv `site-packages` is runtime authority

`codecpp` may compile against the SDK but must resolve VTK at Python runtime from the venv-installed wheel.

## Consequences

- global `PYTHONPATH`-based use of the SDK install tree is unsupported
- runtime provenance must be testable
- Windows bootstrap logic is mandatory
- Linux `RUNPATH` is mandatory
- hidden global environment help is treated as a bug, not a convenience
