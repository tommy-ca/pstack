#!/usr/bin/env python3
"""Rerun the refresh-hygiene pytest slice and CLI dry-run."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "skills" / "swarm" / "scripts" / "refresh-hygiene.py"


def main() -> int:
    tests = subprocess.run(
        [
            "uv",
            "run",
            "--with",
            "pytest",
            "pytest",
            "-q",
            "tests/test_refresh_hygiene.py",
            "tests/test_print_coverage_decoy_nested.py",
        ],
        cwd=ROOT,
        check=False,
    )
    if tests.returncode != 0:
        return tests.returncode
    with tempfile.TemporaryDirectory() as raw:
        skills = Path(raw) / "skills"
        skills.mkdir()
        dry = subprocess.run(
            [sys.executable, str(SCRIPT), "--root", str(ROOT), "--skills", str(skills)],
            cwd=ROOT,
            check=False,
        )
        if dry.returncode not in (0, 2):
            return dry.returncode if dry.returncode else 1
        host = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--root",
                str(ROOT),
                "--skills",
                str(skills),
                "--host-script",
            ],
            cwd=ROOT,
            check=False,
        )
        if host.returncode != 0:
            return host.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
