#!/usr/bin/env python3
"""Tests for Claude Code native profile, plugin manifest, and driver (#441)."""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.drivers import ClaudeDriver, get_driver
from scripts.host_identity import is_declared_host, is_builtin
from scripts.portability_schema import (
    Binding,
    Evidence,
    HarnessProfile,
    ValidationError,
)

_pp_spec = importlib.util.spec_from_file_location("project_package", ROOT / "scripts" / "project-package.py")
assert _pp_spec and _pp_spec.loader
_pp_mod = importlib.util.module_from_spec(_pp_spec)
_pp_spec.loader.exec_module(_pp_mod)

check_claude_plugin = _pp_mod.check_claude_plugin
load_package_descriptor = _pp_mod.load_package_descriptor


def test_claude_profile_conforms_to_schema_and_declared_host_gates() -> None:
    profile_path = ROOT / "profiles" / "claude.json"
    assert profile_path.is_file(), "profiles/claude.json must exist"

    data = json.loads(profile_path.read_text(encoding="utf-8"))
    assert data["host"] == "claude"
    assert data["support_state"] == "candidate"

    # Declared host gate checks (#446)
    assert is_declared_host("claude") is True
    assert is_builtin("claude") is False

    bindings = [Binding(**b) for b in data.get("bindings", [])]
    evidence = [Evidence(**e) for e in data.get("evidence_ledger", [])]

    profile = HarnessProfile(
        host=data["host"],
        support_state=data["support_state"],
        bindings=bindings,
        skills_dir=data.get("skills_dir"),
        plugins_dir=data.get("plugins_dir"),
        plugin_manifest=data.get("plugin_manifest"),
        evidence_ledger=evidence,
        tool_mappings=data.get("tool_mappings"),
        skill_order=data.get("skill_order"),
        runtime_conventions=data.get("runtime_conventions"),
    )
    profile.validate()

    # Distinguishes genuine hard readonly from prompt advice (#441)
    ro_binding = next(b for b in bindings if b.capability == "workspace.readonly")
    assert ro_binding.enforcement == "advisory", "Claude Code exposes no kernel-level readonly mount"

    # Distinguishes child nesting from parent-owned orchestration policy (#441)
    rc = data["runtime_conventions"]
    assert rc["max_subagent_depth"] == 1, "Parent-owned orchestration bounds subagent depth to 1"
    assert "directory-allowlist" in rc["supported_isolation_modes"]

    # All required tool mappings present
    tm = data["tool_mappings"]
    for required in ("file_read", "file_edit", "shell_run", "agent_spawn", "agent_join", "plan_update", "human_ask"):
        assert required in tm and tm[required].strip()


def test_claude_profile_fail_closed_negatives() -> None:
    profile_path = ROOT / "profiles" / "claude.json"
    data = json.loads(profile_path.read_text(encoding="utf-8"))

    # 1. Declared host cannot self-promote to packaged without native evidence
    bad_data = dict(data, support_state="packaged")
    bad_prof = HarnessProfile(
        host=bad_data["host"],
        support_state=bad_data["support_state"],
        bindings=[Binding(**b) for b in bad_data.get("bindings", [])],
        skills_dir=bad_data.get("skills_dir"),
        plugin_manifest=bad_data.get("plugin_manifest"),
    )
    with pytest.raises(ValidationError, match="must stay candidate"):
        bad_prof.validate()

    # 2. Cannot mark binding verified without evidence
    bad_bindings = [dict(b) for b in data["bindings"]]
    bad_bindings[0]["verification_status"] = "verified"
    bad_prof2 = HarnessProfile(
        host=data["host"],
        support_state="candidate",
        bindings=[Binding(**b) for b in bad_bindings],
        skills_dir=data.get("skills_dir"),
        plugin_manifest=data.get("plugin_manifest"),
    )
    with pytest.raises(ValidationError, match="cannot mark .* verified without native evidence"):
        bad_prof2.validate()

    # 3. Prompt-only posture cannot validate as hard enforcement
    with pytest.raises(ValidationError, match="Prompt-only posture .* cannot be validated as hard enforcement"):
        Binding(
            host="claude",
            capability="workspace.readonly",
            implementation_status="native",
            primitive="prompt instruction readonly",
            enforcement="hard",
            verification_status="static-only",
        ).validate()


def test_claude_plugin_manifest_integrity() -> None:
    plugin_path = ROOT / ".claude-plugin" / "plugin.json"
    market_path = ROOT / ".claude-plugin" / "marketplace.json"

    assert plugin_path.is_file()
    assert market_path.is_file()

    plugin = json.loads(plugin_path.read_text(encoding="utf-8"))
    assert isinstance(plugin["agents"], list)
    assert len(plugin["agents"]) == 22, "All 22 canonical agents must be listed"
    for agent_path in plugin["agents"]:
        assert agent_path.endswith(".md"), f"Agent path must end with .md: {agent_path}"
        assert (ROOT / agent_path).is_file(), f"Agent file missing: {agent_path}"

    desc, _ = load_package_descriptor()
    assert check_claude_plugin(desc) is True


def test_claude_native_plugin_validate_cli() -> None:
    driver = get_driver("claude", ROOT)
    avail, reason = driver.is_available()
    if not avail:
        pytest.skip(f"Claude CLI not available: {reason}")

    # Run native claude plugin validate
    res = subprocess.run(
        ["claude", "plugin", "validate", ".", "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0, f"claude plugin validate failed: {res.stderr}\n{res.stdout}"
    out = json.loads(res.stdout)
    assert out.get("success") is True, f"Validation unsuccessful: {out}"


def test_claude_driver_scenarios(tmp_path: Path) -> None:
    driver = get_driver("claude", ROOT)
    assert isinstance(driver, ClaudeDriver)

    avail, reason = driver.is_available()
    assert avail is True, f"Claude CLI should be detected: {reason}"

    version = driver.get_version()
    assert version is not None and "Claude Code" in version

    # 1. Discover
    disc = driver.discover(tmp_path)
    assert disc.verdict == "PASS"

    # 2. Route playbook
    route_tdd = driver.route_playbook("TDD", tmp_path)
    assert route_tdd.verdict == "PASS"

    route_bad = driver.route_playbook("nonexistent-playbook-query", tmp_path)
    assert route_bad.verdict == "FAIL"

    # 3. Child spawn
    spawn = driver.child_spawn(tmp_path)
    assert spawn.verdict == "PASS"

    # 4. Isolation
    iso = driver.isolation(tmp_path)
    assert iso.verdict == "PASS"

    # 5. Evidence capture
    ev = driver.evidence_capture(tmp_path)
    assert ev.verdict == "PASS"


def test_claude_harness_guide_integrity() -> None:
    guide_path = ROOT / "docs" / "harness" / "claude-code.md"
    assert guide_path.is_file(), "docs/harness/claude-code.md must exist"

    content = guide_path.read_text(encoding="utf-8")

    # Explicit non-validated status and scope boundary
    assert "Non-validated harness reference / external adaptation guide" in content
    assert "declared native host target in `pstack.package.json#host_targets`" in content

    # Six-host matrix preserved in package descriptor
    pkg_desc = json.loads((ROOT / "pstack.package.json").read_text(encoding="utf-8"))
    assert pkg_desc["host_targets"] == ["grok", "codex", "omp", "opencode", "antigravity", "droid"]
    assert "claude" not in pkg_desc["host_targets"], "Claude Code must stay candidate profile (#628)"

    # Native vs Shim vs Gap Taxonomy present
    assert "Native vs Shim vs Gap Taxonomy" in content
    assert "Native" in content
    assert "Shim" in content
    assert "Gap" in content

    # Unsupported features fail closed
    assert "Unsupported features (fail-closed gaps)" in content
    assert "Cursor Automations" in content
    assert "Bugbot" in content

