#!/usr/bin/env python3
"""Verify the decision contract and canonical routing registry offline.

CLI facade re-exporting from scripts.verify_decision_contract.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.verify_decision_contract as _vdc
from scripts.verify_decision_contract import *


def main() -> int:
    return _vdc.main()


if __name__ == "__main__":
    sys.exit(main())
