#!/usr/bin/env python3
"""Read-only static doctor for shared pstack structure and Grok adapter compatibility.

Checks static structure, skills, and configuration layout; NOT a six-host native conformance verdict.
CLI facade re-exporting from scripts.verify_harness.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.verify_harness as _vh
from scripts.verify_harness import *


def main() -> int:
    return _vh.main(root=ROOT)


if __name__ == "__main__":
    sys.exit(main())
