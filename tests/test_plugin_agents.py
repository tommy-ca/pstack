"""Enabled grok pstack must be this tommy-ca/pstack checkout."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check-plugin-agents.py"


def test_enabled_tree_without_swarm_workers_fails(tmp_path: Path) -> None:
    foreign = tmp_path / "other-pstack"
    (foreign / "agents").mkdir(parents=True)
    payload = {
        "agents": [
            {"name": "pstack:poteto-agent"},
            {"name": "pstack:comment-sicko"},
        ],
        "plugins": [
            {"name": "pstack", "enabled": True, "path": str(foreign)},
        ],
    }
    inspect = tmp_path / "inspect.json"
    inspect.write_text(json.dumps(payload), encoding="utf-8")
    got = subprocess.run(
        [sys.executable, str(SCRIPT), "--inspect-json", str(inspect)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert got.returncode == 1, got.stdout + got.stderr
    assert "pstack:swarm-workers" in got.stderr
    assert "agents/swarm-workers.md" in got.stderr
    assert "tommy-ca/pstack" in got.stderr


def test_name_without_enabled_path_fails() -> None:
    got = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--inspect-json",
            str(ROOT / "tests" / "fixtures" / "inspect-name-only.json"),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert got.returncode == 1, got.stdout + got.stderr
    assert "no enabled pstack plugin path" in got.stderr


def test_checkout_pstack_passes(tmp_path: Path) -> None:
    payload = {
        "agents": [{"name": "pstack:swarm-workers"}],
        "plugins": [
            {"name": "pstack", "enabled": True, "path": str(ROOT)},
        ],
    }
    inspect = tmp_path / "inspect.json"
    inspect.write_text(json.dumps(payload), encoding="utf-8")
    got = subprocess.run(
        [sys.executable, str(SCRIPT), "--inspect-json", str(inspect)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert got.returncode == 0, got.stdout + got.stderr
    assert got.stdout.splitlines()[0] == "PASS plugin-agents pstack:swarm-workers"
