from __future__ import annotations

import importlib

from ._runtime import describe_runtime, prepare_runtime
from ._version import __version__

prepare_runtime()

_extension_import_error: Exception | None = None
_swig_module = None

try:
    _swig_module = importlib.import_module(".codecpp", __name__)
except ImportError as exc:
    _extension_import_error = exc
else:
    exported = getattr(_swig_module, "__all__", None)
    if exported is None:
        exported = [name for name in dir(_swig_module) if not name.startswith("_")]
    for name in exported:
        globals()[name] = getattr(_swig_module, name)


def extension_loaded() -> bool:
    return _swig_module is not None


def require_extension():
    if _swig_module is None:
        details = describe_runtime(verbose=True)
        bootstrap_error = None
        try:
            prepare_runtime(strict=True)
        except Exception as exc:  # pragma: no cover - diagnostic path
            bootstrap_error = f"{type(exc).__name__}: {exc}"
        message = (
            "The codecpp native extension is not available. "
            "This is expected before the first VTK-backed build, but invalid for "
            "runtime validation.\n"
            f"Runtime details: {details}\n"
            f"Bootstrap status: {bootstrap_error or 'runtime bootstrap completed'}"
        )
        raise ImportError(message) from _extension_import_error
    return _swig_module


__all__ = [
    "__version__",
    "describe_runtime",
    "extension_loaded",
    "prepare_runtime",
    "require_extension",
]

if _swig_module is not None:
    __all__.extend(name for name in dir(_swig_module) if not name.startswith("_"))
