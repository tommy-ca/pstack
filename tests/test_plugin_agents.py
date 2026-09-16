"""Enabled grok pstack must expose pstack:swarm-workers."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check-plugin-agents.py"
CLAUDE = ROOT / "tests" / "fixtures" / "inspect-claude-marketplace-pstack.json"
CHECKOUT = ROOT / "tests" / "fixtures" / "inspect-checkout-pstack.json"


def test_claude_marketplace_pstack_fails_closed() -> None:
    got = subprocess.run(
        [sys.executable, str(SCRIPT), "--inspect-json", str(CLAUDE)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert got.returncode == 1, got.stdout + got.stderr
    assert "pstack:swarm-workers" in got.stderr
    assert "pstack-claude/plugins/pstack" in got.stderr


def test_checkout_pstack_passes() -> None:
    got = subprocess.run(
        [sys.executable, str(SCRIPT), "--inspect-json", str(CHECKOUT)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert got.returncode == 0, got.stdout + got.stderr
    assert got.stdout.splitlines()[0] == "PASS plugin-agents pstack:swarm-workers"
