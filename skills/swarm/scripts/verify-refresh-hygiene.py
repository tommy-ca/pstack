#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "skills" / "swarm" / "scripts" / "refresh-hygiene.py"
TSV_HEADER = "kind\taction\tpath\tnote"


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
            capture_output=True,
            text=True,
        )
        if dry.returncode not in (0, 2):
            return dry.returncode if dry.returncode else 1
        if not dry.stdout.startswith(TSV_HEADER):
            sys.stderr.write(dry.stderr)
            return 1
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
            capture_output=True,
            text=True,
        )
        if host.returncode != 0:
            return host.returncode
        if not host.stdout.startswith("cp -- "):
            sys.stderr.write(host.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
