#!/usr/bin/env python3
"""Sync and reconcile canonical pstack package to the live Antigravity plugin installation.

CLI facade re-exporting from scripts.sync_antigravity_plugin.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.sync_antigravity_plugin as _sap
from scripts.sync_antigravity_plugin import *


def main() -> None:
    _sap.main()


if __name__ == "__main__":
    main()
