from __future__ import annotations

import importlib


def run(order: list[str]) -> None:
    for name in order:
        importlib.import_module(name)
    print(f"Imported successfully: {order}")


if __name__ == "__main__":
    run(["codecpp", "pyvista"])
    run(["pyvista", "codecpp"])
