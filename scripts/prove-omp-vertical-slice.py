#!/usr/bin/env python3
"""Prove one smallest end-to-end OMP vertical slice (#292).

CLI entrypoint and facade re-exporting from scripts.prove_omp_vertical_slice.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.prove_omp_vertical_slice import *
from scripts.prove_omp_vertical_slice import main

if __name__ == "__main__":
    main()
