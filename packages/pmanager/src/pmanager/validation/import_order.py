from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys


def run_order(order: list[str], require_extension: bool) -> dict[str, object]:
    snippets = [
        "import importlib",
        *(f"importlib.import_module('{name}')" for name in order),
    ]
    if require_extension and "codecpp" in order:
        snippets.append("import codecpp; codecpp.require_extension()")
    program = "; ".join(snippets)

    env = os.environ.copy()
    env["PYTHONNOUSERSITE"] = "1"
    completed = subprocess.run(
        [sys.executable, "-c", program],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    return {
        "order": order,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--order",
        action="append",
        default=["codecpp,pyvista", "pyvista,codecpp"],
        help="Comma-separated import order.",
    )
    parser.add_argument("--require-extension", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    results = [
        run_order([name.strip() for name in item.split(",") if name.strip()], args.require_extension)
        for item in args.order
    ]
    failures = [result for result in results if result["returncode"] != 0]

    if args.json:
        print(json.dumps({"results": results}, indent=2))
    else:
        for result in results:
            print(f"Order {result['order']}: returncode={result['returncode']}")
            if result["stderr"]:
                print(result["stderr"])

    return 1 if failures else 0
