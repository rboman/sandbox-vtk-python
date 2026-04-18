from __future__ import annotations

import json

import codecpp
from codepy import runtime_summary


if __name__ == "__main__":
    payload = {
        "codecpp": codecpp.describe_runtime(),
        "codepy": runtime_summary(),
    }
    print(json.dumps(payload, indent=2))
