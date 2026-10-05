from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "canonical-index.py"
INVENTORY = ROOT / "openspec" / "canonical-inventory.json"


def test_canonical_index_script_exists() -> None:
    assert SCRIPT.is_file(), SCRIPT


def test_canonical_index_get_pin_matches_upstream() -> None:
    loader = importlib.util.spec_from_file_location("canonical_index", SCRIPT)
    assert loader is not None and loader.loader is not None
    mod = importlib.util.module_from_spec(loader)
    loader.loader.exec_module(mod)

    pin = mod.get_pin()
    assert len(pin) == 40
    upstream_text = (ROOT / "UPSTREAM").read_text(encoding="utf-8")
    assert pin in upstream_text


def test_canonical_inventory_file_exists_and_conforms() -> None:
    assert INVENTORY.is_file(), INVENTORY
    data = json.loads(INVENTORY.read_text(encoding="utf-8"))
    assert data["pin_conformance"] == "PASS"
    assert data["counts"]["principles"] == 23
    assert data["counts"]["gaps"] == 0
    assert data["counts"]["total_artifacts"] > 100


def test_canonical_index_cli_check_exits_zero() -> None:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert "PASS: Canonical inventory conforms to pin." in proc.stdout
    assert "Principles: 23" in proc.stdout


def test_canonical_index_cli_drift_reports_drift_or_current() -> None:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--drift"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert "Upstream Freshness:" in proc.stdout


def test_canonical_index_excludes_make_bot_ui_with_reason() -> None:
    data = json.loads(INVENTORY.read_text(encoding="utf-8"))
    matches = [a for a in data["artifacts"] if a["path"] == "skills/make-bot-ui/SKILL.md"]
    assert len(matches) == 1
    assert matches[0]["mode"] == "exclude"
    assert "reason" in matches[0]
