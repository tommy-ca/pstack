#!/usr/bin/env python3
"""Enablement and catalog identity checker for pstack plugin agents.

CLI facade re-exporting from scripts.check_plugin_agents.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.check_plugin_agents as _cpa
from scripts.check_plugin_agents import *


def main(argv: list[str] | None = None) -> int:
    return _cpa.main(argv)


if __name__ == "__main__":
    sys.exit(main())
