"""Public entrypoints for the codepy package.

This file exposes the small runtime helpers used by examples and validation.
"""

from .mesh_tools import build_demo_mesh, runtime_summary

__all__ = ["build_demo_mesh", "runtime_summary"]
