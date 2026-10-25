#!/usr/bin/env python3
"""Deterministic scaffolding and validation of portable verification skills.

CLI facade re-exporting from scripts.scaffold_verification_skill.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.scaffold_verification_skill as _svs
from scripts.scaffold_verification_skill import *

require_builtin_host_keys(HOST_DETECT_ORDER, "HOST_DETECT_ORDER")


def main() -> int:
    return _svs.main()


if __name__ == "__main__":
    sys.exit(main())
