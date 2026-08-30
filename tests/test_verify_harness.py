"""Drive the shipped static harness scanner (not a reimplementation)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCANNER = ROOT / "scripts" / "verify-harness.py"


def test_verify_harness_script_exists() -> None:
    assert SCANNER.is_file(), SCANNER


def test_verify_harness_passes_on_this_tree() -> None:
    proc = subprocess.run(
        [sys.executable, str(SCANNER)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout


if __name__ == "__main__":
    test_verify_harness_script_exists()
    test_verify_harness_passes_on_this_tree()
    print("PASS tests/test_verify_harness.py")
