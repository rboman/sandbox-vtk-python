from __future__ import annotations

"""Tiny mesh/runtime helpers used to validate pyvista + vtk wiring.

This module intentionally stays minimal and focused on sanity checks.
"""


def build_demo_mesh():
    """Create a small demo sphere mesh."""
    import pyvista as pv

    return pv.Sphere(theta_resolution=8, phi_resolution=8)


def runtime_summary() -> dict[str, str]:
    """Return lightweight runtime metadata for pyvista/vtk."""
    import pyvista as pv
    import vtk

    return {
        "pyvista_version": pv.__version__,
        "vtk_version": vtk.vtkVersion.GetVTKVersion(),
        "vtk_file": getattr(vtk, "__file__", "unknown"),
    }
