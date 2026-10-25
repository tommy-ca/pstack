"""Model role policy schema, metaschema, grammar, and taxonomy contracts."""

from __future__ import annotations

import copy
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
from jsonschema import Draft202012Validator, ValidationError as JsonSchemaError

from scripts import model_role_policy
from scripts.model_role_policy import check_model_role_policy
from scripts.model_role_resolver import model_plan_to_wire, plan_role
from scripts.portability_schema import ValidationError
from tests.model_role_helpers import (
    EXAMPLE,
    PACKAGE,
    ROOT,
    SCHEMA,
    VALIDATOR,
    catalog_plan_policy,
    capability_bindings,
    validate,
)


def test_schema_is_draft_2020_12_and_example_is_valid() -> None:
    Draft202012Validator.check_schema(SCHEMA)
    validate(EXAMPLE)


@pytest.mark.parametrize(("mutation", "needle"), [
    (lambda p: p["role_constraints"].update({"unlisted-role": {"selection": "single"}}), "unknown canonical role"),
    (lambda p: p["role_constraints"]["arena-runners"].update({"required_capabilities": ["agent.spawn"]}), "agent.spawn and agent.join"),
    (lambda p: p["role_constraints"]["swarm-workers"].update({"minimum_independent_workers": 2}), "non-panel role"),
    (lambda p: p["role_constraints"]["swarm-workers"].update({"required_capabilities": ["provider.call"]}), "unknown capability"),
    (lambda p: p["hosts"]["codex"]["tier_defaults"].update({"unlisted-tier": ["inherit-parent"]}), "unknown tier"),
    (lambda p: p["hosts"]["codex"]["tier_defaults"].update({"panel": ["gpt-not-observed"]}), "absent from host catalog"),
    (lambda p: p["hosts"]["codex"].update({"model_catalog": [{"id": "gpt-not-observed","provider": "x","family": "x"}]}), "unverified catalog"),
    (lambda p: p["hosts"]["codex"].update({"verification_status": "verified"}), "live verified claims"),
    (lambda p: p["canonical_source"].update({"pin": "0" * 40}), "canonical pin differs"),
    (lambda p: p["hosts"].update({"copilot": p["hosts"].pop("codex")}), "not declared"),
    (lambda p: p["constraints"].update({"allow_unverified_models": True}), "violates its schema"),
    (lambda p: p["hosts"]["codex"].pop("model_catalog"), "violates its schema"),
    (lambda p: p["hosts"]["codex"].pop("fallback"), "violates its schema"),
    (lambda p: p["role_constraints"]["swarm-workers"].update({"minimum_independent_workers": 17}), "violates its schema"),
])
def test_cross_document_failures(mutation, needle: str) -> None:
    policy = copy.deepcopy(EXAMPLE)
    mutation(policy)
    with pytest.raises(ValidationError, match=needle):
        check_model_role_policy(policy, PACKAGE)


def test_duplicate_role_id_fails_even_when_schema_is_valid() -> None:
    desc = copy.deepcopy(PACKAGE)
    desc["roles"].append(copy.deepcopy(desc["roles"][0]))
    with pytest.raises(ValidationError, match="duplicate role IDs"):
        check_model_role_policy(EXAMPLE, desc)


def test_schema_rejects_unknown_top_level_fields() -> None:
    policy = copy.deepcopy(EXAMPLE)
    policy["workflow_database"] = "shadow-state"
    with pytest.raises(JsonSchemaError):
        VALIDATOR.validate(policy)


def test_schema_rejects_unsupported_topology() -> None:
    policy = copy.deepcopy(EXAMPLE)
    policy["role_constraints"]["arena-runners"]["selection"] = "virtual-panel"
    with pytest.raises(JsonSchemaError):
        VALIDATOR.validate(policy)


def test_plan_wire_schema_accepts_pure_planner_and_forbids_fake_runtime_claims() -> None:
    plan_schema = json.loads(
        (ROOT / "schemas/portability/model-plan.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator.check_schema(plan_schema)
    validate_plan = Draft202012Validator(plan_schema).validate

    plan = plan_role(catalog_plan_policy(), PACKAGE, host="codex",
                     role="swarm-workers", capabilities=capability_bindings())
    wire = model_plan_to_wire(plan)
    validate_plan(wire)
    assert wire["evidence_level"] == "static-planning-only"
    assert wire["status"] == "PLANNED"

    blocked = plan_role(catalog_plan_policy(), PACKAGE, host="codex",
                        role="swarm-workers", explicit="not-there",
                        capabilities=capability_bindings())
    validate_plan(model_plan_to_wire(blocked))

    fake = copy.deepcopy(wire)
    fake["status"] = "VERIFIED"
    with pytest.raises(JsonSchemaError):
        validate_plan(fake)

    fake = copy.deepcopy(wire)
    fake["evidence_level"] = "runtime-verified"
    with pytest.raises(JsonSchemaError):
        validate_plan(fake)

    fake = copy.deepcopy(wire)
    fake["seats"][0]["model"] = None
    with pytest.raises(JsonSchemaError):
        validate_plan(fake)

    fake = copy.deepcopy(wire)
    fake["seats"][0]["family"] = None
    with pytest.raises(JsonSchemaError):
        validate_plan(fake)

    fake = copy.deepcopy(wire)
    fake["seats"][0]["provider"] = None
    with pytest.raises(JsonSchemaError):
        validate_plan(fake)


@pytest.mark.parametrize("token", sorted(model_role_policy.INHERIT))
def test_inherit_tokens_rejected_as_catalog_ids_by_both_validators(token: str) -> None:
    policy = copy.deepcopy(EXAMPLE)
    policy["hosts"]["codex"]["model_catalog"] = [
        {"id": token, "provider": "x", "family": "x", "supported_efforts": []}
    ]
    with pytest.raises(JsonSchemaError):
        VALIDATOR.validate(policy)
    with pytest.raises(ValidationError, match="violates its schema"):
        check_model_role_policy(policy, PACKAGE)


def test_inherit_set_matches_schema_def() -> None:
    schema = json.loads((ROOT / "schemas/portability/model-role-policy.schema.json").read_text(encoding="utf-8"))
    assert set(model_role_policy.INHERIT) == set(schema["$defs"]["inheritTokens"]["enum"])


def test_canonical_role_taxonomy_schema_and_pin_audit_contract() -> None:
    """#435 acceptance contract: canonical 22-role taxonomy, schema, fixtures, and pin audit."""
    roles = PACKAGE["roles"]
    assert len(roles) == 22, f"expected 22 canonical roles, got {len(roles)}"
    role_ids = {r["id"] for r in roles}
    assert len(role_ids) == 22, "duplicate role IDs detected in package descriptor"

    legal_tiers = {
        "adversarial-panel",
        "fast-verifier",
        "fast-worker",
        "panel",
        "strong-judgment",
        "strongest",
    }
    for role in roles:
        assert role["id"].strip() == role["id"], "role ID must not contain whitespace"
        assert re.fullmatch(r"^[a-z][a-z0-9-]*$", role["id"]), f"invalid role ID format {role['id']}"
        assert role["description"].strip(), f"missing description for role {role['id']}"
        assert role["default_model_role"] in legal_tiers, (
            f"role {role['id']} has invalid default_model_role {role['default_model_role']}"
        )

    agent_files = {p.stem for p in (ROOT / "agents").glob("*.md")}
    assert agent_files == role_ids, f"role-agent drift: missing={role_ids - agent_files}; extra={agent_files - role_ids}"

    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts/effort_ladder.py"), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, f"effort ladder check failed: {proc.stderr + proc.stdout}"

    import scripts.canonical_index as mod
    cache = mod.get_git_cache_root()
    inventory = mod.compute_inventory(cache)
    assert inventory["pin"] == "88d47514b82e7c44f00f2b2a72ff6dd12158038c", "canonical pin mismatch"
    assert inventory["pin_conformance"] == "PASS", f"canonical conformance failed: {inventory['counts']}"
    assert inventory["counts"]["gaps"] == 0, "canonical inventory must contain 0 unclassified gaps"
    assert inventory["counts"]["total_artifacts"] == 172, f"expected 172 artifacts, got {inventory['counts']['total_artifacts']}"

    assert len(EXAMPLE["hosts"]) == 6, "all 6 host targets must be declared"
    for host_name, host_cfg in EXAMPLE["hosts"].items():
        assert host_cfg["model_catalog"] == [], f"{host_name} checked-in catalog must be empty"
        assert set(host_cfg["tier_defaults"].keys()) == legal_tiers, f"{host_name} must map all 6 legal tiers"
