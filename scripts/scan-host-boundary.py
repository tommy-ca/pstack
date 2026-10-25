#!/usr/bin/env python3
"""Host-boundary gate for the portable shared surfaces.

CLI facade re-exporting from scripts.scan_host_boundary.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.scan_host_boundary as _shb
from scripts.scan_host_boundary import *


def main() -> int:
    return _shb.main(root=ROOT, profiles_dir=PROFILES_DIR)


if __name__ == "__main__":
    sys.exit(main())
