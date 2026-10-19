#!/usr/bin/env python3
"""Tests for GitHub Copilot candidate profile, declared host gates, and driver (#442)."""

import json
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.drivers import CopilotDriver, get_driver
from scripts.host_identity import (
    is_builtin,
    is_declared_host,
    is_external,
    is_valid_host_id,
)
from scripts.portability_schema import (
    Binding,
    Evidence,
    HarnessProfile,
    ValidationError,
)

SCHEMAS_DIR = ROOT / "schemas" / "portability"


def _registry() -> Registry:
    return Registry().with_resources(
        [
            (
                (schema := json.loads(path.read_text(encoding="utf-8")))["$id"],
                Resource.from_contents(schema),
            )
            for path in sorted(SCHEMAS_DIR.glob("*.json"))
        ]
    )


def test_copilot_profile_conforms_to_schema_and_declared_host_gates() -> None:
    profile_path = ROOT / "profiles" / "copilot.json"
    assert profile_path.is_file(), "profiles/copilot.json must exist"

    data = json.loads(profile_path.read_text(encoding="utf-8"))
    assert data["host"] == "github:copilot"
    assert data["support_state"] == "candidate"

    # Declared host gates (#446)
    assert is_valid_host_id("github:copilot") is True
    assert is_external("github:copilot") is True
    assert is_declared_host("github:copilot") is True
    assert is_builtin("github:copilot") is False

    # Draft 2020-12 JSON Schema validation
    profile_schema = json.loads((SCHEMAS_DIR / "profile.schema.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(profile_schema, registry=_registry())
    validator.validate(data)

    # Domain model validation
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

    # Truthful multi-agent accounting: spawn/join/cancel/message are GAP (#442)
    spawn_b = next(b for b in bindings if b.capability == "agent.spawn")
    assert spawn_b.implementation_status == "gap"
    assert spawn_b.enforcement == "advisory"

    join_b = next(b for b in bindings if b.capability == "agent.join")
    assert join_b.implementation_status == "gap"

    cancel_b = next(b for b in bindings if b.capability == "agent.cancel")
    assert cancel_b.implementation_status == "gap"

    msg_b = next(b for b in bindings if b.capability == "agent.message")
    assert msg_b.implementation_status == "gap"

    # Distinguishes genuine hard readonly from prompt advice (#442)
    ro_binding = next(b for b in bindings if b.capability == "workspace.readonly")
    assert ro_binding.enforcement == "advisory", "Copilot exposes no kernel-level readonly mount"

    # Isolation mode: only "none" supported (no native worktree isolation primitive)
    rc = data["runtime_conventions"]
    assert rc["supported_isolation_modes"] == ["none"]
    assert rc["default_model"] == "inherit", "Model choice is host-managed, no unsupported default model"
    assert "subagent_type" in rc["forbidden_spawn_fields"]

    # Tool mappings contain all required fields
    tm = data["tool_mappings"]
    for required in ("file_read", "file_edit", "shell_run", "agent_spawn", "agent_join", "plan_update", "human_ask"):
        assert required in tm and tm[required].strip()


def test_copilot_profile_fail_closed_negatives() -> None:
    profile_path = ROOT / "profiles" / "copilot.json"
    data = json.loads(profile_path.read_text(encoding="utf-8"))

    # 1. Bare unnamespaced 'copilot' must be refused (#446)
    assert not is_valid_host_id("copilot")
    assert not is_external("copilot")
    with pytest.raises(ValidationError):
        HarnessProfile(
            host="copilot",
            support_state="candidate",
            bindings=[Binding(**b) for b in data.get("bindings", [])],
            skills_dir=data.get("skills_dir"),
            plugin_manifest=data.get("plugin_manifest"),
        ).validate()

    # 2. Declared host cannot self-promote to packaged or supported without native evidence
    for forbidden_state in ("packaged", "supported"):
        bad_prof = HarnessProfile(
            host=data["host"],
            support_state=forbidden_state,
            bindings=[Binding(**b) for b in data.get("bindings", [])],
            skills_dir=data.get("skills_dir"),
            plugin_manifest=data.get("plugin_manifest"),
        )
        with pytest.raises(ValidationError, match="must stay candidate"):
            bad_prof.validate()

    # 3. Cannot mark binding verified without evidence
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

    # 4. Prompt-only posture cannot validate as hard enforcement
    with pytest.raises(ValidationError, match="Prompt-only posture .* cannot be validated as hard enforcement"):
        Binding(
            host="github:copilot",
            capability="workspace.readonly",
            implementation_status="native",
            primitive="prompt instruction readonly",
            enforcement="hard",
            verification_status="static-only",
        ).validate()


def test_copilot_driver_scenarios(tmp_path: Path) -> None:
    driver = get_driver("github:copilot", ROOT)
    assert isinstance(driver, CopilotDriver)

    # 1. Discovery: if binary not installed, fails closed with honest BLOCKED
    avail, reason = driver.is_available()
    disc = driver.discover(tmp_path)
    if not avail:
        assert disc.verdict == "BLOCKED"
        assert "copilot" in disc.stdout.lower()
    else:
        assert disc.verdict in ("PASS", "FAIL")

    # 2. Route playbook
    route_tdd = driver.route_playbook("TDD", tmp_path)
    assert route_tdd.verdict == "PASS"

    route_bad = driver.route_playbook("nonexistent-playbook-query", tmp_path)
    assert route_bad.verdict == "FAIL"

    # 3. Child spawn (honestly verifies gap)
    spawn = driver.child_spawn(tmp_path)
    assert spawn.verdict == "PASS"

    # 4. Isolation (honestly verifies modes: ["none"] and advisory readonly)
    iso = driver.isolation(tmp_path)
    assert iso.verdict == "PASS"

    # 5. Evidence capture
    ev = driver.evidence_capture(tmp_path)
    assert ev.verdict == "PASS"
