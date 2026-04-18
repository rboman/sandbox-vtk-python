# Problem statement

## Context

A native C++ library (`codecpp`) uses VTK and is wrapped to Python via SWIG.
A separate pure Python package (`codepy`) uses PyVista.

## Risk

PyVista depends on Python `vtk`.
If the Python environment also loads a different VTK binary set through the native extension used by `codecpp`, one Python process may mix incompatible VTK runtimes.

## Consequence

Even without direct VTK object exchange between `codecpp` and `codepy`, importing both modules in one process may fail or behave unpredictably.

## Core question

How should the repository, build flow, packaging flow, and runtime flow be organized so that:
- the native C++ side uses a custom-built VTK
- the Python side uses a matching VTK wheel
- both sides remain coherent at runtime