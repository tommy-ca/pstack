#!/usr/bin/env python3
"""Generate, check, and audit canonical pstack inventory and drift from the UPSTREAM pin.

CLI facade re-exporting from scripts.canonical_index.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.canonical_index as _ci
from scripts.canonical_index import *


def main() -> int:
    return _ci.main(root=ROOT)


if __name__ == "__main__":
    sys.exit(main())
