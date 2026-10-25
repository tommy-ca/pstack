#!/usr/bin/env python3
"""Project canonical pstack.package.json into harness-native plugin descriptors.

CLI entrypoint and facade re-exporting from scripts.package_projection.
References scripts.host_identity via package_projection.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.package_projection import *
from scripts.package_projection import _split_frontmatter, main

if __name__ == "__main__":
    main()
