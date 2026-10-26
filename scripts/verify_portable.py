#!/usr/bin/env python3
"""Portable lever verification engine for pstack across agent harnesses.

CLI entrypoint and facade re-exporting from scripts.portable_verifier.
References scripts.host_identity via portable_verifier.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.portable_verifier as _pv
from scripts.portable_verifier import *
from scripts.portable_verifier import _receipt_payload


def main() -> None:
    _pv.main(
        root=ROOT,
        evidence_dir=DEFAULT_EVIDENCE_DIR,
        get_canonical_root=get_canonical_root,
    )


if __name__ == "__main__":
    main()
