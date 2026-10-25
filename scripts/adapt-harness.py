#!/usr/bin/env python3
"""Rewrite Cursor harness call sites onto grok-build tools.

CLI facade re-exporting from scripts.adapt_harness.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.adapt_harness as _ah
from scripts.adapt_harness import *


def files_transform_would_change(root: Path | None = None) -> list[str]:
    return _ah.files_transform_would_change(root=root if root is not None else ROOT)


def main() -> int:
    return _ah.main(root=ROOT)


if __name__ == "__main__":
    sys.exit(main())
