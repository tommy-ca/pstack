#!/usr/bin/env python3
"""CLI entrypoint and facade re-exporting from scripts.prove_omp_native_package."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.prove_omp_native_package import *
from scripts.prove_omp_native_package import main

if __name__ == "__main__":
    main()
