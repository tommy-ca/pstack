"""Static policy schema + semantic parity checks; no live model availability implied."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
from jsonschema import Draft202012Validator, ValidationError as JsonSchemaError

from scripts.model_role_policy import check_model_role_policy
from scripts.portability_schema import ValidationError

SCHEMA = json.loads((ROOT / "schemas/portability/model-role-policy.schema.json").read_text())
EXAMPLE = json.loads((ROOT / "examples/portability/model-role-policy.example.json").read_text())
PACKAGE = json.loads((ROOT / "pstack.package.json").read_text())
VALIDATOR = Draft202012Validator(SCHEMA)


def validate(policy: dict, descriptor: dict = PACKAGE) -> None:
    VALIDATOR.validate(policy)
    check_model_role_policy(policy, descriptor)


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
    (lambda p: p["constraints"].update({"allow_unverified_models": True}), "opt into unverified"),
    (lambda p: p["hosts"]["codex"].pop("model_catalog"), "must be an explicit list"),
    (lambda p: p["hosts"]["codex"].pop("fallback"), "fallback must be"),
    (lambda p: p["role_constraints"]["swarm-workers"].update({"minimum_independent_workers": 17}), "invalid minimum_independent_workers"),
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


def live_policy() -> dict:
    policy = copy.deepcopy(EXAMPLE)
    config = policy["hosts"]["codex"]
    config["discovery"] = "live"
    config["verification_status"] = "verified"
    config["catalog_observation"] = {
        "host_version": "test-fixture-only", "observed_at": "2026-10-15T00:00:00Z",
        "receipt": ".audit/test-fixture-no-runtime-claim.json",
        "implementation_revision": "0" * 40,
    }
    config["model_catalog"] = [
        {"id": "test-model", "provider": "test", "family": "fictional",
         "supported_efforts": ["low", "high"]},
    ]
    config["tier_defaults"]["fast-verifier"] = ["test-model"]
    config["role_overrides"] = {"swarm-workers": {"models": ["test-model"], "effort": "high"}}
    return policy


def test_live_shape_with_fake_fixture_is_structurally_valid_only() -> None:
    # This checks a data shape, not a real native model/receipt or support status.
    validate(live_policy())


def test_live_claim_without_observation_fails() -> None:
    policy = live_policy()
    del policy["hosts"]["codex"]["catalog_observation"]
    with pytest.raises(ValidationError, match="observed catalog"):
        check_model_role_policy(policy, PACKAGE)


def test_wrong_effort_fails_for_named_model() -> None:
    policy = live_policy()
    policy["hosts"]["codex"]["role_overrides"]["swarm-workers"]["effort"] = "ultra"
    with pytest.raises(ValidationError, match="unsupported effort"):
        check_model_role_policy(policy, PACKAGE)


def test_package_roles_have_exactly_one_local_agent_definition() -> None:
    # Role IDs are owned by the descriptor. The agent files are host-independent
    # references; checked-in example policy may not define another role roster.
    role_ids = {role["id"] for role in PACKAGE["roles"]}
    agent_paths = list((ROOT / "agents").glob("*.md"))
    files = {p.stem for p in agent_paths}
    assert len(role_ids) == len(PACKAGE["roles"]), "duplicate role IDs"
    assert len(files) == len(agent_paths), "duplicate agent filenames"
    assert files == role_ids, f"role-agent drift: missing={role_ids - files}; extra={files - role_ids}"

# --- Harness-neutral planning, separated from live dispatch -----------------

from scripts.model_role_resolver import plan_role


def catalog_plan_policy() -> dict:
    p = copy.deepcopy(EXAMPLE)
    host = p["hosts"]["codex"]
    host["discovery"] = "catalog"  # offline source inventory, NOT live evidence
    host["verification_status"] = "static-only"
    host["model_catalog"] = [
        {"id": "model-a", "provider": "fixture", "family": "alpha"},
        {"id": "model-b", "provider": "fixture", "family": "beta"},
        {"id": "model-c", "provider": "fixture", "family": "alpha"},
    ]
    host["tier_defaults"].update({
        "fast-verifier": ["model-a"],
        "panel": ["model-a"],
        "adversarial-panel": ["model-a", "model-b"],
    })
    return p


def capability_bindings(*, advisory_readonly: bool = False) -> dict:
    return {name: {"implementation_status": "native",
                   "enforcement": "advisory" if advisory_readonly and name == "workspace.readonly" else "hard"}
            for name in ["agent.spawn", "agent.join", "workspace.isolated", "workspace.readonly"]}


def test_role_planner_static_only_even_with_complete_fixture() -> None:
    plan = plan_role(catalog_plan_policy(), PACKAGE, host="codex", role="swarm-workers",
                     capabilities=capability_bindings())
    assert plan.status == "PLANNED"
    assert plan.evidence_level == "static-planning-only"
    assert plan.seats[0].model == "model-a"
    assert plan.source == "host-tier"


def test_overrides_are_precedent_but_do_not_silently_replace_unknown_slug() -> None:
    policy = catalog_plan_policy()
    plan = plan_role(policy, PACKAGE, host="codex", role="swarm-workers",
                     explicit="model-b", project="model-c", user="model-a",
                     capabilities=capability_bindings())
    assert (plan.source, plan.seats[0].model) == ("explicit", "model-b")
    project = plan_role(policy, PACKAGE, host="codex", role="swarm-workers",
                        project="model-c", user="model-a", capabilities=capability_bindings())
    assert (project.source, project.seats[0].model) == ("project", "model-c")
    invalid = plan_role(policy, PACKAGE, host="codex", role="swarm-workers",
                        explicit="does-not-exist", capabilities=capability_bindings())
    assert invalid.status == "BLOCKED"
    assert "no silent substitution" in invalid.reasons[0]


def test_inherit_parent_omits_model_and_does_not_forge_family() -> None:
    p = plan_role(catalog_plan_policy(), PACKAGE, host="codex", role="swarm-workers",
                  explicit="inherit-parent", capabilities=capability_bindings())
    assert p.status == "PLANNED"
    assert p.seats[0].model is None
    assert p.seats[0].family is None


def test_unconfigured_host_and_role_fail_closed() -> None:
    policy = catalog_plan_policy()
    assert plan_role(policy, PACKAGE, host="claude", role="swarm-workers").status == "BLOCKED"
    assert plan_role(policy, PACKAGE, host="codex", role="imaginary-role").status == "BLOCKED"


def test_separate_seat_count_from_family_count() -> None:
    policy = catalog_plan_policy()
    policy["hosts"]["codex"]["role_overrides"] = {
        "arena-runners": {"models": ["model-a"], "seats": 3}
    }
    validate(policy)
    p = plan_role(policy, PACKAGE, host="codex", role="arena-runners",
                  capabilities=capability_bindings())
    assert len(p.seats) == 3
    assert len({s.model for s in p.seats}) == 1
    assert len({s.ordinal for s in p.seats}) == 3
    assert p.status == "DEGRADED"
    assert "model families" in p.reasons[0]


def test_panel_diversity_is_not_assumed_from_repeated_family() -> None:
    policy = catalog_plan_policy()
    plan = plan_role(policy, PACKAGE, host="codex", role="interrogate-reviewers",
                     explicit=["model-a", "model-c"], capabilities=capability_bindings())
    assert len(plan.seats) == 2
    assert plan.status == "DEGRADED"
    assert {seat.family for seat in plan.seats} == {"alpha"}


def test_cross_judge_prefers_different_family_from_parent() -> None:
    policy = catalog_plan_policy()
    plan = plan_role(policy, PACKAGE, host="codex", role="arena-cross-judge-pool",
                     explicit=["model-a", "model-b"], parent_family="alpha",
                     capabilities=capability_bindings())
    assert len(plan.seats) == 1
    assert plan.seats[0].model == "model-b"
    assert plan.status == "PLANNED"


def test_missing_required_family_diversity_blocks_without_switching_silently() -> None:
    policy = catalog_plan_policy()
    policy["role_constraints"]["arena-cross-judge-pool"]["require_distinct_model_families"] = True
    plan = plan_role(policy, PACKAGE, host="codex", role="arena-cross-judge-pool",
                     explicit=["model-a", "model-c"], parent_family="alpha",
                     capabilities=capability_bindings())
    assert plan.status == "BLOCKED"
    assert "unproven" in plan.reasons[0]


def test_unknown_or_advisory_capability_cannot_be_hard_pass() -> None:
    policy = catalog_plan_policy()
    missing = plan_role(policy, PACKAGE, host="codex", role="interrogate-reviewers",
                        capabilities={"agent.spawn": {"implementation_status": "native", "enforcement": "hard"}})
    assert missing.status == "BLOCKED"
    advisory = plan_role(policy, PACKAGE, host="codex", role="interrogate-reviewers",
                         capabilities=capability_bindings(advisory_readonly=True))
    assert advisory.status == "DEGRADED"
    assert any("not hard" in reason for reason in advisory.reasons)


def test_single_role_rejects_panel_config() -> None:
    plan = plan_role(catalog_plan_policy(), PACKAGE, host="codex", role="swarm-workers",
                     explicit=["model-a", "model-b"], capabilities=capability_bindings())
    assert plan.status == "BLOCKED"


def test_missing_named_mapping_fails_closed() -> None:
    policy = catalog_plan_policy()
    policy["hosts"]["codex"]["tier_defaults"].pop("fast-verifier")
    plan = plan_role(policy, PACKAGE, host="codex", role="swarm-workers",
                     capabilities=capability_bindings())
    assert plan.status == "BLOCKED"
    policy["hosts"]["codex"]["fallback"] = "inherit-parent"
    inherited = plan_role(policy, PACKAGE, host="codex", role="swarm-workers",
                          capabilities=capability_bindings())
    assert (inherited.source, inherited.seats[0].model) == ("inherit-parent", None)


def test_cross_judge_cannot_claim_multiple_seats() -> None:
    policy = catalog_plan_policy()
    policy["hosts"]["codex"]["role_overrides"] = {
        "arena-cross-judge-pool": {"models": ["model-a", "model-b"], "seats": 3}
    }
    with pytest.raises(ValidationError, match="non-panel role"):
        check_model_role_policy(policy, PACKAGE)


def test_reference_fork_snapshot_preserves_unreviewed_states() -> None:
    manifest = json.loads(
        (ROOT / "docs/research/pstack-claude-forks-2026-10-15.json").read_text()
    )
    assert manifest["source_sha"] == "94f5ce95abe8a9dec976967d79941f631cf477cd"
    rows = manifest["entries"]
    assert len(rows) == 48
    assert len({row["path"] for row in rows}) == len(rows)
    assert sum(row["reference_kind"] == "policy" for row in rows) == 40
    assert sum(row["reference_kind"] == "port-feature" for row in rows) == 8
    assert all(row["review_state"] == "pending" for row in rows)
    assert all(row["proposed_adoption"] == "unclassified" for row in rows)


def test_plan_wire_schema_accepts_pure_planner_and_forbids_fake_runtime_claims() -> None:
    from scripts.model_role_resolver import model_plan_to_wire
    plan_schema = json.loads(
        (ROOT / "schemas/portability/model-plan.schema.json").read_text()
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
    # Inherited model cannot magically have a known provider/family.
    with pytest.raises(JsonSchemaError):
        validate_plan(fake)

    fake = copy.deepcopy(wire)
    fake["seats"][0]["family"] = None
    # A named model without family identity is a forged half-plan.
    with pytest.raises(JsonSchemaError):
        validate_plan(fake)

    fake = copy.deepcopy(wire)
    fake["seats"][0]["provider"] = None
    with pytest.raises(JsonSchemaError):
        validate_plan(fake)
