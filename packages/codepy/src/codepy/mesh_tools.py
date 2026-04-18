from __future__ import annotations


def build_demo_mesh():
    import pyvista as pv

    return pv.Sphere(theta_resolution=8, phi_resolution=8)


def runtime_summary() -> dict[str, str]:
    import pyvista as pv
    import vtk

    return {
        "pyvista_version": pv.__version__,
        "vtk_version": vtk.vtkVersion.GetVTKVersion(),
        "vtk_file": getattr(vtk, "__file__", "unknown"),
    }
