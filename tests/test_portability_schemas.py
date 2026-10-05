import json
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.portability_schema import (
    Adaptation,
    Binding,
    Capability,
    Evidence,
    HarnessProfile,
    PackageDescriptor,
    ValidationError,
)

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS_DIR = ROOT / "schemas" / "portability"


def test_portability_json_schemas_are_valid_json() -> None:
    assert SCHEMAS_DIR.is_dir()
    schema_files = list(SCHEMAS_DIR.glob("*.json"))
    assert len(schema_files) >= 4
    for sf in schema_files:
        data = json.loads(sf.read_text(encoding="utf-8"))
        assert "$schema" in data
        assert "title" in data


def test_capability_validation() -> None:
    cap = Capability(id="agent.spawn", required_postconditions=["Child agent is initialized and addressable"])
    cap.validate()

    bad = Capability(id="bad_no_dot", required_postconditions=["ok"])
    with pytest.raises(ValidationError):
        bad.validate()

    no_post = Capability(id="agent.spawn", required_postconditions=[])
    with pytest.raises(ValidationError):
        no_post.validate()


def test_binding_rejects_prompt_only_as_hard_enforcement() -> None:
    # Hard enforcement with prompt-only primitive must fail
    binding = Binding(
        host="codex",
        capability="workspace.readonly",
        implementation_status="native",
        enforcement="hard",
        verification_status="static-only",
        primitive="Prompt instruction do not edit files",
    )
    with pytest.raises(ValidationError, match="Prompt-only posture"):
        binding.validate()

    # Changing enforcement to advisory passes
    binding.enforcement = "advisory"
    binding.validate()


def test_binding_requires_evidence_when_claimed_verified() -> None:
    binding = Binding(
        host="grok",
        capability="agent.spawn",
        implementation_status="native",
        enforcement="hard",
        verification_status="verified",
        primitive="spawn_subagent",
        evidence_ref=None,
    )
    with pytest.raises(ValidationError, match="claimed verified without evidence_ref"):
        binding.validate()

    binding.evidence_ref = ".audit/evidence/grok-spawn.log"
    binding.validate()


def test_package_descriptor_rejects_runtime_orchestration_fields() -> None:
    desc = PackageDescriptor(
        id="pstack",
        name="pstack",
        version="0.15.5-grokbuild.0",
        upstream_pin="4b4d98e5e3b3c139f63dbc1ce4b538954c8f2f52",
        host_targets=["grok", "codex"],
        skills_root="skills",
        lifecycle={"install": "echo install", "verify": "python3 scripts/verify-harness.py", "uninstall": "rm"},
        raw_dict={"spawn_topology": "tree"},
    )
    with pytest.raises(ValidationError, match="must not encode runtime orchestration semantics"):
        desc.validate()


def test_harness_profile_requires_all_capabilities_verified_for_supported_state() -> None:
    # A profile with static-only or missing capabilities cannot claim 'supported'
    b1 = Binding(
        host="codex",
        capability="agent.spawn",
        implementation_status="native",
        enforcement="hard",
        verification_status="static-only",
        primitive="agent spawn",
    )
    profile = HarnessProfile(
        host="codex",
        support_state="supported",
        bindings=[b1],
    )
    with pytest.raises(ValidationError, match="unverified required capability"):
        profile.validate()

    # Mapped state allows unverified bindings
    profile.support_state = "mapped"
    profile.validate()


def test_adaptation_requires_reason_for_exclude_and_gap() -> None:
    ad = Adaptation(canonical_artifact="skills/make-bot-ui/SKILL.md", mode="exclude", reason=None)
    with pytest.raises(ValidationError, match="requires an explicit reason"):
        ad.validate()

    ad.reason = "Replaced by local figure-it-out"
    ad.validate()
