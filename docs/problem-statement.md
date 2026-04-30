# Problem Statement

`codecpp` uses native VTK through SWIG, while `codepy` uses `pyvista` and Python `vtk`.

Without strict runtime control, one process can load incompatible VTK binaries.

The repository solves this by:

- building one target-specific VTK SDK for native compilation
- generating and installing one matching target-specific `vtk` wheel
- validating runtime provenance and import order in the same target venv
