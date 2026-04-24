#!/usr/bin/env python
from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PMANAGER_SRC = REPO_ROOT / "packages" / "pmanager" / "src"
if str(PMANAGER_SRC) not in sys.path:
    sys.path.insert(0, str(PMANAGER_SRC))

from pmanager.validation.audit_environment import *  # noqa: F403
from pmanager.validation.audit_environment import main


if __name__ == "__main__":
    raise SystemExit(main())
