"""Static policy schema + semantic parity checks; no live model availability implied."""

from __future__ import annotations

import copy
import json
import re
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
from jsonschema import Draft202012Validator, ValidationError as JsonSchemaError

from scripts import model_role_policy
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

def test_caller_slug_with_unsupported_effort_blocks_in_planner() -> None:
    """Validator checks declared models only; caller slugs reach the planner gate."""
    policy = live_policy()
    host = policy["hosts"]["codex"]
    host["model_catalog"] = [
        {"id": "weak-model", "provider": "test", "family": "fictional",
         "supported_efforts": ["low"]},
        {"id": "test-model", "provider": "test", "family": "fictional",
         "supported_efforts": ["low", "high"]},
    ]
    host["role_overrides"] = {"swarm-workers": {"models": ["test-model"], "effort": "high"}}
    plan = plan_role(policy, PACKAGE, host="codex", role="swarm-workers",
                     explicit="weak-model", capabilities=capability_bindings())
    assert plan.status == "BLOCKED"
    assert "unsupported on model" in plan.reasons[0]


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

from scripts.model_role_resolver import model_plan_to_wire, plan_role


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


def test_plan_role_is_pure_and_performs_no_io(monkeypatch) -> None:
    """#437 acceptance: plan_role is side-effect-free with zero I/O, network, or subprocess calls."""
    import builtins
    import socket

    def denied(*args, **kwargs):
        raise AssertionError("I/O is forbidden during pure resolution")

    monkeypatch.setattr(builtins, "open", denied)
    monkeypatch.setattr(subprocess, "run", denied)
    monkeypatch.setattr(subprocess, "Popen", denied)
    monkeypatch.setattr(socket, "socket", denied)

    policy = catalog_plan_policy()
    plan = plan_role(policy, PACKAGE, host="codex", role="swarm-workers", capabilities=capability_bindings())
    assert plan.status == "PLANNED"
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
    user = plan_role(policy, PACKAGE, host="codex", role="swarm-workers",
                     user="model-b", capabilities=capability_bindings())
    assert (user.source, user.seats[0].model) == ("user", "model-b")
    policy["hosts"]["codex"]["role_overrides"] = {"swarm-workers": {"models": ["model-c"]}}
    host_role = plan_role(policy, PACKAGE, host="codex", role="swarm-workers",
                          capabilities=capability_bindings())
    assert (host_role.source, host_role.seats[0].model) == ("host-role", "model-c")
    invalid = plan_role(policy, PACKAGE, host="codex", role="swarm-workers",
                        explicit="does-not-exist", capabilities=capability_bindings())
    assert invalid.status == "BLOCKED"
    assert "no silent substitution" in invalid.reasons[0]


@pytest.mark.parametrize("path", ["explicit", "project", "user"])
@pytest.mark.parametrize("duplicates", [["model-a", "model-a"], ["model-a", "model-a", "model-a"]])
def test_duplicate_choice_lists_are_refused_on_every_caller_path(path: str,
                                                                 duplicates: list[str]) -> None:
    # A repeated slug is one model, never two independent seats: the uniqueness
    # rule lives in check_choice_list, the single home shared by policy and planner.
    with pytest.raises(ValidationError) as excinfo:
        plan_role(catalog_plan_policy(), PACKAGE, host="codex", role="interrogate-reviewers",
                  capabilities=capability_bindings(), **{path: duplicates})
    assert f"{path}: choices must be unique nonempty list" in str(excinfo.value)


@pytest.mark.parametrize("explicit", ["model-a", ["model-a"]])
def test_single_slug_explicit_choice_still_plans(explicit: str | list[str]) -> None:
    plan = plan_role(catalog_plan_policy(), PACKAGE, host="codex", role="swarm-workers",
                     explicit=explicit, capabilities=capability_bindings())
    assert plan.status == "PLANNED"
    assert (plan.source, plan.seats[0].model) == ("explicit", "model-a")


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


def test_cross_family_panel_seat_selection_clean_planned() -> None:
    policy = catalog_plan_policy()
    plan = plan_role(policy, PACKAGE, host="codex", role="interrogate-reviewers",
                     explicit=["model-a", "model-b"], capabilities=capability_bindings())
    assert plan.status == "PLANNED"
    assert len(plan.seats) == 2
    assert (plan.seats[0].ordinal, plan.seats[0].model, plan.seats[0].family, plan.seats[0].provider) == (
        1, "model-a", "alpha", "fixture"
    )
    assert (plan.seats[1].ordinal, plan.seats[1].model, plan.seats[1].family, plan.seats[1].provider) == (
        2, "model-b", "beta", "fixture"
    )
    assert plan.reasons == ()


def test_panel_strict_family_diversity_blocks_on_single_family_and_passes_on_diverse() -> None:
    policy = catalog_plan_policy()
    policy["role_constraints"]["interrogate-reviewers"]["require_distinct_model_families"] = True

    # Diverse families: PASS / PLANNED
    diverse = plan_role(policy, PACKAGE, host="codex", role="interrogate-reviewers",
                        explicit=["model-a", "model-b"], capabilities=capability_bindings())
    assert diverse.status == "PLANNED"
    assert diverse.reasons == ()

    # Single family across 2 seats: BLOCKED
    same_family = plan_role(policy, PACKAGE, host="codex", role="interrogate-reviewers",
                            explicit=["model-a", "model-c"], capabilities=capability_bindings())
    assert same_family.status == "BLOCKED"
    assert same_family.reasons == ("required model-family diversity missing",)
    assert same_family.seats == ()

    # Single seat: cannot prove diversity -> BLOCKED
    single_seat = plan_role(policy, PACKAGE, host="codex", role="interrogate-reviewers",
                            explicit=["model-a"], capabilities=capability_bindings())
    assert single_seat.status == "BLOCKED"
    assert single_seat.reasons == ("required model-family diversity missing",)
    assert single_seat.seats == ()

    # Inherit parent: no proven model/family -> BLOCKED
    inherited = plan_role(policy, PACKAGE, host="codex", role="interrogate-reviewers",
                          explicit=["inherit-parent"], capabilities=capability_bindings())
    assert inherited.status == "BLOCKED"
    assert inherited.reasons == ("required model-family diversity missing",)
    assert inherited.seats == ()


def test_cross_judge_family_diversity_degraded_and_blocked_negatives() -> None:
    policy = catalog_plan_policy()

    # parent_family is None: diversity unproven -> DEGRADED
    unproven_parent = plan_role(policy, PACKAGE, host="codex", role="arena-cross-judge-pool",
                                explicit=["model-a", "model-b"], parent_family=None,
                                capabilities=capability_bindings())
    assert unproven_parent.status == "DEGRADED"
    assert "cross-judge family diversity unproven" in unproven_parent.reasons[0]

    # parent_family is None with strict diversity required -> BLOCKED
    policy_strict = copy.deepcopy(policy)
    policy_strict["role_constraints"]["arena-cross-judge-pool"]["require_distinct_model_families"] = True
    blocked_parent = plan_role(policy_strict, PACKAGE, host="codex", role="arena-cross-judge-pool",
                               explicit=["model-a", "model-b"], parent_family=None,
                               capabilities=capability_bindings())
    assert blocked_parent.status == "BLOCKED"
    assert "cross-judge model family independence is unproven" in blocked_parent.reasons[0]

    # Inherit parent cross-judge without strict diversity -> DEGRADED
    inherited = plan_role(policy, PACKAGE, host="codex", role="arena-cross-judge-pool",
                          explicit=["inherit-parent"], parent_family="alpha",
                          capabilities=capability_bindings())
    assert inherited.status == "DEGRADED"
    assert "cross-judge family diversity unproven" in inherited.reasons[0]

    # Inherit parent cross-judge with strict diversity -> BLOCKED
    inherited_blocked = plan_role(policy_strict, PACKAGE, host="codex", role="arena-cross-judge-pool",
                                  explicit=["inherit-parent"], parent_family="alpha",
                                  capabilities=capability_bindings())
    assert inherited_blocked.status == "BLOCKED"
    assert "cross-judge model family independence is unproven" in inherited_blocked.reasons[0]


def test_unavailable_model_in_panel_or_cross_judge_blocks_closed() -> None:
    policy = catalog_plan_policy()

    # Interrogate panel with one missing slug
    panel_plan = plan_role(policy, PACKAGE, host="codex", role="interrogate-reviewers",
                           explicit=["model-a", "ghost-model"], capabilities=capability_bindings())
    assert panel_plan.status == "BLOCKED"
    assert panel_plan.seats == ()
    assert any("model 'ghost-model' absent from codex catalog; no silent substitution" in r for r in panel_plan.reasons)

    # Cross-judge with missing slug
    judge_plan = plan_role(policy, PACKAGE, host="codex", role="arena-cross-judge-pool",
                           explicit=["ghost-model"], parent_family="alpha",
                           capabilities=capability_bindings())
    assert judge_plan.status == "BLOCKED"
    assert judge_plan.seats == ()
    assert any("model 'ghost-model' absent from codex catalog; no silent substitution" in r for r in judge_plan.reasons)

    # Arena runners with missing slug
    runner_plan = plan_role(policy, PACKAGE, host="codex", role="arena-runners",
                            explicit=["model-a", "ghost-model"], capabilities=capability_bindings())
    assert runner_plan.status == "BLOCKED"
    assert runner_plan.seats == ()
    assert any("model 'ghost-model' absent from codex catalog; no silent substitution" in r for r in runner_plan.reasons)




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


ROLE_TOKEN_RE = re.compile(r"pstack:([a-z][a-z0-9-]*)")
PLACEHOLDER_RE = re.compile(r"pstack:<[^>]*>")


def test_skill_role_tokens_resolve_to_descriptor_roles_and_agents() -> None:
    # Local claim only: every concrete pstack:<role> token emitted in skill
    # docs resolves to a descriptor role id and a local agent file.
    # Template placeholders (pstack:<...>) are excluded, not resolved.
    role_ids = {role["id"] for role in PACKAGE["roles"]}
    agent_files = {p.stem for p in (ROOT / "agents").glob("*.md")}
    tokens: set[str] = set()
    for path in sorted((ROOT / "skills").rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        text = PLACEHOLDER_RE.sub("", text)
        tokens.update(ROLE_TOKEN_RE.findall(text))
    assert tokens, "no role tokens found; scan is broken"
    missing_roles = tokens - role_ids
    missing_agents = tokens - agent_files
    assert not missing_roles, f"tokens without descriptor role: {sorted(missing_roles)}"
    assert not missing_agents, f"tokens without agent file: {sorted(missing_agents)}"


# --- Stale/unverified catalog stays planning-grade (never PLANNED) ----------


def unproven_catalog_policy(status: str) -> dict:
    """Same complete fixture as catalog_plan_policy, one verification claim flipped."""
    policy = catalog_plan_policy()
    policy["hosts"]["codex"]["verification_status"] = status
    return policy


@pytest.mark.parametrize("status", ["stale", "unverified"])
def test_unproven_catalog_can_never_plan_clean(status: str) -> None:
    # Every other input here is a complete, valid planning fixture; only the
    # catalog's verification claim distinguishes it. A stale or unverified
    # catalog must degrade, never report PLANNED as if it were observed.
    assert model_role_policy.UNPROVEN_CATALOG_STATUSES == {"stale", "unverified"}
    plan = plan_role(unproven_catalog_policy(status), PACKAGE, host="codex",
                     role="swarm-workers", capabilities=capability_bindings())
    assert plan.status == "DEGRADED"
    assert len(plan.seats) == 1 and plan.seats[0].model == "model-a"
    assert plan.reasons and "not live evidence" in plan.reasons[0]
    assert status in plan.reasons[0]
    # The wire contract must accept the degraded plan as a static artifact.
    plan_schema = json.loads((ROOT / "schemas/portability/model-plan.schema.json").read_text())
    Draft202012Validator(plan_schema).validate(model_plan_to_wire(plan))


def test_static_only_catalog_still_plans_and_stale_flips_it() -> None:
    policy = catalog_plan_policy()
    static_only = plan_role(policy, PACKAGE, host="codex", role="swarm-workers",
                            capabilities=capability_bindings())
    assert static_only.status == "PLANNED"
    assert static_only.reasons == ()

    policy["hosts"]["codex"]["verification_status"] = "stale"
    stale = plan_role(policy, PACKAGE, host="codex", role="swarm-workers",
                      capabilities=capability_bindings())
    assert stale.status == "DEGRADED"
    assert (stale.seats, stale.source) == (static_only.seats, static_only.source)


def test_unproven_catalog_gate_cannot_upgrade_a_blocker() -> None:
    # The gate lowers PLANNED to DEGRADED; a real blocker still wins outright.
    plan = plan_role(unproven_catalog_policy("stale"), PACKAGE, host="codex",
                     role="swarm-workers", explicit="not-a-real-model",
                     capabilities=capability_bindings())
    assert plan.status == "BLOCKED"
    assert "no silent substitution" in plan.reasons[0]


def test_unproven_catalog_may_not_carry_observation_or_evidence_refs() -> None:
    # A planning-grade catalog may not look evidence-backed in the same document.
    live_looking = unproven_catalog_policy("unverified")
    live_looking["hosts"]["codex"]["catalog_observation"] = {
        "host_version": "test-fixture-only", "observed_at": "2026-10-15T00:00:00Z",
        "receipt": ".audit/test-fixture-no-runtime-claim.json",
    }
    with pytest.raises(ValidationError, match="not live evidence"):
        check_model_role_policy(live_looking, PACKAGE)

    referenced = unproven_catalog_policy("stale")
    referenced["hosts"]["codex"]["model_catalog"][0]["evidence_ref"] = ".audit/test-fixture.json"
    with pytest.raises(ValidationError, match="not live evidence"):
        check_model_role_policy(referenced, PACKAGE)

    # Same claim, honest document: accepted as planning-grade input.
    check_model_role_policy(unproven_catalog_policy("stale"), PACKAGE)


def test_example_policy_covers_every_declared_host_with_empty_catalogs() -> None:
    declared = PACKAGE["host_targets"]
    tiers = {role["default_model_role"] for role in PACKAGE["roles"]}
    assert len(declared) == 6
    assert sorted(EXAMPLE["hosts"]) == sorted(declared)
    for host, config in EXAMPLE["hosts"].items():
        assert config["model_catalog"] == [], f"{host} must not invent unobserved model IDs"
        assert set(config["tier_defaults"]) == tiers, f"{host} does not map every declared tier"
    validate(EXAMPLE)


def test_every_declared_host_plans_without_an_unmapped_host_verdict() -> None:
    for host in PACKAGE["host_targets"]:
        plan = plan_role(EXAMPLE, PACKAGE, host=host, role="independent-verifier")
        assert plan.status != "BLOCKED", f"{host}: {plan.reasons}"
        assert plan.evidence_level == "static-planning-only"
        assert all(seat.model is None for seat in plan.seats), "no model ID may be invented"


def load_project_package_module():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "project_package_plan_probe", ROOT / "scripts" / "project-package.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_project_package_check_surfaces_the_planner_verdict(capsys) -> None:
    project_package = load_project_package_module()
    desc, _ = project_package.load_package_descriptor()
    assert project_package.check_model_role_plan(desc) is True
    out = capsys.readouterr().out
    assert out.count(project_package.PLAN_PROBE_ROLE) == len(PACKAGE["host_targets"])
    for role in project_package.PLAN_PROBE_ROLES:
        assert out.count(role) == len(PACKAGE["host_targets"])
    assert "BLOCKED" not in out
    assert "static-planning-only" in out


@pytest.mark.parametrize(
    "tier_to_drop,expected_blocked_role",
    [
        ("fast-worker", "how-explorer"),
        ("strong-judgment", "how-explainer"),
        ("panel", "architect-runners"),
        ("strongest", "independent-verifier"),
    ],
)
def test_check_model_role_plan_fails_closed_when_tier_dropped(
    monkeypatch, tmp_path, capsys, tier_to_drop, expected_blocked_role
) -> None:
    """Mutating any probed unconstrained tier out of tier_defaults causes check_model_role_plan to fail closed."""
    project_package = load_project_package_module()
    desc, _ = project_package.load_package_descriptor()

    policy_path = ROOT / "examples/portability/model-role-policy.example.json"
    policy_data = json.loads(policy_path.read_text(encoding="utf-8"))

    del policy_data["hosts"]["codex"]["tier_defaults"][tier_to_drop]
    mutant_policy_path = tmp_path / "model-role-policy.json"
    mutant_policy_path.write_text(json.dumps(policy_data), encoding="utf-8")

    monkeypatch.setattr(project_package, "MODEL_ROLE_POLICY", mutant_policy_path)
    assert project_package.check_model_role_plan(desc) is False
    out = capsys.readouterr().out
    assert f"BLOCKED: codex cannot plan {expected_blocked_role}" in out


def test_plan_role_has_exactly_one_production_caller() -> None:
    # U2 wiring: the sole non-test importer of the planner entry point is the
    # read-only project-package --check probe; no router or gateway may join it.
    # portability_schema.py mentions plan_role only in its recipe comment naming the
    # probe path, not as an import or call.
    importers = set()
    for path in (ROOT / "scripts").rglob("*.py"):
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if re.search(r"\bplan_role\b", line):
                importers.add(path.name)
                break
    assert importers == {"model_role_resolver.py", "project-package.py"}

def test_reference_fork_ledger_records_completed_source_review() -> None:
    """#434 acceptance line 1: 48 rows source-reviewed against pinned counterparts."""
    from collections import Counter
    manifest = json.loads(
        (ROOT / "docs/research/pstack-claude-forks-2026-10-15.json").read_text()
    )
    assert manifest["source_sha"] == "94f5ce95abe8a9dec976967d79941f631cf477cd"
    contract = manifest["source_review_contract"]["counterpart_sources"]
    assert contract["reference"]["pin"] == "94f5ce95abe8a9dec976967d79941f631cf477cd"
    assert contract["canonical"]["pin"] == "1dcc2bacde73ddd284803b7af28164d0436198fc"
    assert contract["target"]["pin"] == "3f4cd124f27cab90865df79d18d376e2f4335b2c"
    rows = manifest["entries"]
    assert len(rows) == 48
    assert len({row["path"] for row in rows}) == len(rows)
    assert sum(row["reference_kind"] == "policy" for row in rows) == 40
    assert sum(row["reference_kind"] == "port-feature" for row in rows) == 8
    assert all(row["review_state"] == "source-reviewed" for row in rows)
    assert all(row["why"].strip() for row in rows)
    assert all(row["upstream"] == "not-proposed" for row in rows)
    assert Counter(r["proposed_adoption"] for r in rows) == {"adapt": 36, "preserve": 1, "exclude": 2, "gap": 7, "policy-fork": 2}
    assert Counter(r["proposed_adoption"] for r in rows) == dict(manifest["review_counts"])
    assert not any(row["proposed_adoption"] == "unclassified" for row in rows)
    per_row = [row for row in rows if "license_disposition" in row]
    assert {row["path"] for row in per_row} == {
        "plugins/pstack/skills/thermo-nuclear-code-quality-review/SKILL.md",
        "plugins/pstack/skills/poteto-mode/playbooks/orchestrate.md",
    }
    assert all(row["proposed_adoption"] == "policy-fork" for row in per_row)
    assert all(row["license_disposition"]["scope"] == "per-row" for row in per_row)
    assert all(set(r["source_review"]) >= {"counterpart_blobs", "attribution_profile", "semantic_delta", "check_or_gap"} for r in rows)
    absent = manifest["source_review_contract"]["absent_counterparts"]
    assert [(a["side"], a["path"]) for a in absent] == [("target", "skills/poteto-mode/scripts/check-plan.test.ts")]

    # Counterpart blob format and git object store verification
    import subprocess
    hex_pattern = re.compile(r"^[0-9a-f]{40}$")
    absent_target_paths = {a["path"] for a in absent if a.get("side") == "target"}
    for row in rows:
        blobs = row["source_review"]["counterpart_blobs"]
        assert hex_pattern.match(blobs["reference"]), f"invalid reference blob {blobs['reference']}"
        assert hex_pattern.match(blobs["canonical"]), f"invalid canonical blob {blobs['canonical']}"
        rel_target = row["path"].removeprefix("plugins/pstack/")
        if rel_target in absent_target_paths:
            assert blobs["target"] is None, f"expected absent target blob for {row['path']}"
        else:
            assert hex_pattern.match(blobs["target"]), f"invalid target blob {blobs['target']}"
            is_shallow = subprocess.run(
                ["git", "rev-parse", "--is-shallow-repository"], cwd=ROOT, capture_output=True, text=True
            ).stdout.strip() == "true"
            if not is_shallow:
                res = subprocess.run(["git", "cat-file", "-e", blobs["target"]], cwd=ROOT)
                assert res.returncode == 0, f"target blob {blobs['target']} missing from git object store"

    # Review scope fail-closed and independent acceptance record
    scope = manifest["review_scope"]
    assert scope["approval"] == "not granted"
    assert scope["implementation"] == "not authorized or claimed"
    assert scope["runtime"] == "not verified"
    assert scope["independent_acceptance"].startswith("completed;")
    assert "resolved on mainline" in scope["watcher_gap"]


def test_canonical_role_taxonomy_schema_and_pin_audit_contract() -> None:
    """#435 acceptance contract: canonical 22-role taxonomy, schema, fixtures, and pin audit."""
    # 1. Package descriptor role taxonomy
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

    # 2. Role-to-agent definition parity
    agent_files = {p.stem for p in (ROOT / "agents").glob("*.md")}
    assert agent_files == role_ids, f"role-agent drift: missing={role_ids - agent_files}; extra={agent_files - role_ids}"

    # 3. Canonical effort ladder alignment
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts/effort_ladder.py"), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, f"effort ladder check failed: {proc.stderr + proc.stdout}"

    # 4. Canonical pin inventory conformance audit
    import importlib.util
    spec = importlib.util.spec_from_file_location("canonical_index", ROOT / "scripts/canonical-index.py")
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    cache = mod.get_git_cache_root()
    inventory = mod.compute_inventory(cache)
    assert inventory["pin"] == "1dcc2bacde73ddd284803b7af28164d0436198fc", "canonical pin mismatch"
    assert inventory["pin_conformance"] == "PASS", f"canonical conformance failed: {inventory['counts']}"
    assert inventory["counts"]["gaps"] == 0, "canonical inventory must contain 0 unclassified gaps"
    assert inventory["counts"]["total_artifacts"] == 167, f"expected 167 artifacts, got {inventory['counts']['total_artifacts']}"

    # 5. Checked-in example policy strictly avoids fake live models
    assert len(EXAMPLE["hosts"]) == 6, "all 6 host targets must be declared"
    for host_name, host_cfg in EXAMPLE["hosts"].items():
        assert host_cfg["model_catalog"] == [], f"{host_name} checked-in catalog must be empty"
        assert set(host_cfg["tier_defaults"].keys()) == legal_tiers, f"{host_name} must map all 6 legal tiers"


