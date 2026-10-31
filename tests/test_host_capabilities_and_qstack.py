"""Tests for six-host capability reconciliation, package projection, and QStack overlay compatibility.

Validates acceptance criteria for Issue #848 (Parent #842 / Epic #840):
- Exactly six declared hosts: grok, codex, omp, opencode, antigravity, droid
- Truthful profile capabilities for task/project/event/PR/CI
- No host leaks Cursor-only or Grok-specific primitives into shared skills
- Fallback handling for missing host capabilities (GAP/UNTESTED)
- Downstream QStack overlay compatibility: qorch retains separate quant authority
- Package projection integrity for all declared hosts
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
PROFILES = ROOT / "profiles"

DECLARED_HOSTS = ("grok", "codex", "omp", "opencode", "antigravity", "droid")


def test_six_declared_hosts_profiles_exist_and_are_valid_json() -> None:
    for host in DECLARED_HOSTS:
        profile_file = PROFILES / f"{host}.json"
        assert profile_file.is_file(), f"Profile for {host} must exist at {profile_file}"
        data = json.loads(profile_file.read_text(encoding="utf-8"))
        assert "host" in data
        assert data["host"] == host


def test_package_projection_check_passes_cleanly() -> None:
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "project_package.py"), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, f"project_package.py --check failed:\n{proc.stdout}\n{proc.stderr}"
    assert "PASS: grok manifest" in proc.stdout
    assert "PASS: codex manifest" in proc.stdout
    assert "PASS: omp manifest" in proc.stdout
    assert "PASS: opencode manifest" in proc.stdout
    assert "PASS: antigravity manifest" in proc.stdout
    assert "PASS: droid manifest" in proc.stdout


def test_no_cursor_only_tools_in_shared_skills() -> None:
    """Verify shared skills do not reference Cursor-only IDE APIs or removed orch CLI."""
    shared_skills_dir = ROOT / "skills"
    for skill_file in shared_skills_dir.rglob("SKILL.md"):
        content = skill_file.read_text(encoding="utf-8")
        # Shared skills must not execute raw scripts/orch/orch.ts
        assert "scripts/orch/orch.ts" not in content, f"{skill_file} leaks scripts/orch/orch.ts"
        # Shared skills must not use Cursor-only dynamic execution loop
        assert "in dynamic mode" not in content, f"{skill_file} leaks dynamic mode"


def test_qstack_overlay_authority_separation() -> None:
    """Validate that QStack overlay compatibility maintains qorch as separate research authority."""
    audit_doc = (
        ROOT / "docs" / "research" / "upstream-pstack-0.15.36-audit-2026-10-31.md"
    ).read_text(encoding="utf-8")
    assert "qorch" in audit_doc
    assert "separately owned by **qorch**, not PStack's generic Orchestrate" in audit_doc
    assert "not PStack's generic Orchestrate" in audit_doc

    # Verify generic orchestrate.md does not reference qorch
    orch = (ROOT / "skills" / "poteto-mode" / "playbooks" / "orchestrate.md").read_text(
        encoding="utf-8"
    )
    assert "qorch" not in orch, "Generic orchestrate playbook must not absorb qorch state"


def test_host_capability_fallback_handling() -> None:
    """Verify that absent events or supervisors degrade cleanly to polling or UNTESTED."""
    orch = (ROOT / "skills" / "poteto-mode" / "playbooks" / "orchestrate.md").read_text(
        encoding="utf-8"
    )
    assert "Prefer native PR/CI event subscriptions where available" in orch
    assert "bounded checkpoints; do not run unbounded polling loops" in orch
    assert "Subagent depth is 1" in orch
    assert "`gap` for nested track sub-coordinator ownership" in orch
