# codepy

Pure Python package using PyVista inside the same target venv as `codecpp`.

`codepy` intentionally does not solve VTK runtime issues itself. It relies on the repository workflow to ensure that:

- the target venv already contains the custom `vtk==9.3.1` wheel
- `pyvista` is installed under a pinned constraints file
- `codecpp` and `codepy` observe the same runtime VTK origin
