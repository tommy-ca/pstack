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
    ToolMapping,
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


def test_antigravity_profile_conformance() -> None:
    profile_path = ROOT / "profiles" / "antigravity.json"
    assert profile_path.is_file()
    data = json.loads(profile_path.read_text(encoding="utf-8"))
    assert data["host"] == "antigravity"
    assert data["skills_dir"] == ".agents/skills"
    assert data["plugin_manifest"] == ".antigravity-plugin/plugin.json"
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
    )
    profile.validate()
    assert isinstance(profile.tool_mappings, ToolMapping)


def test_all_harness_profiles_conform_to_layout_and_model() -> None:
    profiles_dir = ROOT / "profiles"
    assert profiles_dir.is_dir()
    expected_hosts = {
        "grok": (".grok/skills", ".grok-plugin/plugin.json"),
        "codex": (".codex/skills", ".codex-plugin/plugin.json"),
        "omp": (".omp/skills", ".omp-plugin/plugin.json"),
        "opencode": (".opencode/skills", ".opencode-plugin/package.json"),
        "antigravity": (".agents/skills", ".antigravity-plugin/plugin.json"),
    }
    for host, (expected_skills_dir, expected_manifest) in expected_hosts.items():
        pf = profiles_dir / f"{host}.json"
        assert pf.is_file(), f"Missing profile for {host}"
        data = json.loads(pf.read_text(encoding="utf-8"))
        assert data["host"] == host
        assert data.get("skills_dir") == expected_skills_dir
        assert data.get("plugin_manifest") == expected_manifest
        assert "tool_mappings" in data, f"Profile {host} missing tool_mappings"

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
        )
        profile.validate()
        assert isinstance(profile.tool_mappings, ToolMapping)


def test_harness_profile_rejects_missing_skills_dir_or_manifest() -> None:
    b = Binding(
        host="grok",
        capability="agent.spawn",
        implementation_status="native",
        enforcement="hard",
        verification_status="verified",
        primitive="spawn_subagent",
        evidence_ref=".audit/evidence/grok-spawn.log",
    )
    # Explicitly empty skills_dir
    p_no_skills = HarnessProfile(host="grok", support_state="mapped", bindings=[b], skills_dir="")
    with pytest.raises(ValidationError, match="must declare a non-empty skills_dir"):
        p_no_skills.validate()

    # Explicitly empty manifest
    p_no_manifest = HarnessProfile(
        host="grok", support_state="mapped", bindings=[b], skills_dir=".grok/skills", plugin_manifest=""
    )
    with pytest.raises(ValidationError, match="must declare a plugin_manifest"):
        p_no_manifest.validate()


def test_tool_mapping_validation() -> None:
    tm = ToolMapping(
        file_read="view_file",
        file_edit="replace_file_content",
        shell_run="run_command",
        agent_spawn="invoke_subagent",
        agent_join="manage_subagents",
        plan_update="todo.md",
        human_ask="ask_question",
    )
    tm.validate()

    # Empty required field raises ValidationError
    tm_empty = ToolMapping(
        file_read="",
        file_edit="replace_file_content",
        shell_run="run_command",
        agent_spawn="invoke_subagent",
        agent_join="manage_subagents",
        plan_update="todo.md",
        human_ask="ask_question",
    )
    with pytest.raises(ValidationError, match="missing or empty required field"):
        tm_empty.validate()


def test_harness_profile_tool_mapping_rejection() -> None:
    b = Binding(
        host="grok",
        capability="agent.spawn",
        implementation_status="native",
        enforcement="hard",
        verification_status="verified",
        primitive="spawn_subagent",
        evidence_ref=".audit/evidence/grok-spawn.log",
    )
    # Unknown field in tool_mappings dict raises ValidationError
    with pytest.raises(ValidationError, match="Unknown fields in tool_mappings"):
        HarnessProfile(
            host="grok",
            support_state="mapped",
            bindings=[b],
            skills_dir=".grok/skills",
            plugin_manifest=".grok-plugin/plugin.json",
            tool_mappings={"file_read": "read", "invalid_unknown_tool": "boom"},
        )


def test_tool_mapping_json_schema_conformance() -> None:
    schema_path = SCHEMAS_DIR / "tool-mapping.schema.json"
    assert schema_path.is_file()
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    required_fields = set(schema.get("required", []))
    allowed_fields = set(schema.get("properties", {}).keys())

    profiles_dir = ROOT / "profiles"
    for host in ("grok", "codex", "omp", "opencode", "antigravity"):
        pf = profiles_dir / f"{host}.json"
        data = json.loads(pf.read_text(encoding="utf-8"))
        tm_data = data.get("tool_mappings", {})
        # All required fields must be present
        for rf in required_fields:
            assert rf in tm_data, f"Host {host} missing required tool mapping: {rf}"
            assert isinstance(tm_data[rf], str) and tm_data[rf].strip()
        # No forbidden or unknown fields
        for k in tm_data:
            assert k in allowed_fields, f"Host {host} has unknown tool mapping: {k}"



