#!/usr/bin/env python3
"""Native package lifecycle driver for pstack across supported harnesses.

CLI entrypoint and facade re-exporting from scripts.package_lifecycle.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.package_lifecycle import *
from scripts.package_lifecycle import main

if __name__ == "__main__":
    main()
