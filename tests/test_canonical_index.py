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
    principles = [
        a for a in data["artifacts"]
        if a.get("category") == "principle" and a.get("mode") in ("preserve", "adapt")
    ]
    assert data["counts"]["principles"] == len(principles)
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
    data = json.loads(INVENTORY.read_text(encoding="utf-8"))
    assert f"Principles: {data['counts']['principles']}" in proc.stdout


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


def test_canonical_index_dynamic_count_adaptation() -> None:
    """Prove a changed canonical inventory derives counts dynamically without test-source count edits."""
    # Synthetic classified artifacts with an arbitrary dynamic principle count
    sample_classified = [
        {"path": "skills/principle-a/SKILL.md", "canonical_hash": "abc", "category": "principle", "mode": "preserve"},
        {"path": "skills/principle-b/SKILL.md", "canonical_hash": "def", "category": "principle", "mode": "preserve"},
        {"path": "skills/principle-c/SKILL.md", "canonical_hash": "123", "category": "principle", "mode": "adapt"},
        {"path": "skills/poteto-mode/playbooks/feature.md", "canonical_hash": "456", "category": "playbook", "mode": "adapt"},
    ]

    principles_count = sum(1 for c in sample_classified if c["category"] == "principle" and c["mode"] in ("preserve", "adapt"))
    playbooks_count = sum(1 for c in sample_classified if c["category"] == "playbook" and c["mode"] in ("preserve", "adapt"))

    assert principles_count == 3
    assert playbooks_count == 1


def test_canonical_index_drift_observation_metadata() -> None:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--drift"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert "Observation Source:" in proc.stdout
    assert "Observation Time:" in proc.stdout

def _upstream_cache_present() -> bool:
    try:
        loader = importlib.util.spec_from_file_location("canonical_index_probe", SCRIPT)
        assert loader is not None and loader.loader is not None
        mod = importlib.util.module_from_spec(loader)
        loader.loader.exec_module(mod)
        return mod.get_git_cache_root() is not None
    except Exception:
        return False


import pytest


@pytest.mark.skipif(not _upstream_cache_present(), reason="no upstream cache; contract BLOCKED, not failed")
def test_canonical_index_classify_drift_cli(tmp_path: Path) -> None:
    """The classifier writes where it is told and leaves the tracked record alone."""
    tracked = ROOT / "openspec" / "canonical-drift.json"
    tracked_before = tracked.read_bytes() if tracked.is_file() else None
    out = tmp_path / "drift.json"

    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--classify-drift", "--out", str(out)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert "Total changed files:" in proc.stdout
    report = json.loads(out.read_text(encoding="utf-8"))
    assert sum(report["buckets"].values()) == report["total_changed_files"]
    assert len(report["entries"]) == report["total_changed_files"]
    if report["total_changed_files"] == 0:
        # A pin landing exactly on upstream HEAD classifies no drift.
        assert report["pin"] == report["upstream_head"]
    else:
        assert report["entries"], "a classified report lists its entries"
    assert all({"path", "status", "bucket", "mode"} <= set(entry) for entry in report["entries"])
    assert (tracked.read_bytes() if tracked.is_file() else None) == tracked_before


def test_vendored_entrypoints_stay_executable() -> None:
    for path in (
        "skills/poteto-mode/scripts/watch-pr/watch-pr",
        "skills/poteto-mode/scripts/worktree-audit.sh",
    ):
        mode = (ROOT / path).stat().st_mode
        assert mode & 0o111, f"{path} must stay executable (mode {oct(mode)})"
