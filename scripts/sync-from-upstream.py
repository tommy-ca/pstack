#!/usr/bin/env python3
"""Show how to refresh this port from official Cursor pstack.

CLI facade re-exporting from scripts.sync_from_upstream.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.sync_from_upstream as _sfu
from scripts.sync_from_upstream import *


def main(argv: list[str] | None = None) -> None:
    _sfu.main(argv)


if __name__ == "__main__":
    main()
