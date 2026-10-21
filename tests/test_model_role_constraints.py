"""Model role constraints, capability gates, and panel diversity invariants."""

from __future__ import annotations

import copy
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest

from scripts.model_role_policy import check_model_role_policy
from scripts.model_role_resolver import plan_role
from scripts.portability_schema import ValidationError
from tests.model_role_helpers import (
    PACKAGE,
    ROOT,
    catalog_plan_policy,
    capability_bindings,
    live_policy,
    validate,
)


def test_live_shape_with_fake_fixture_is_structurally_valid_only() -> None:
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
    policy = live_policy()
    host = policy["hosts"]["codex"]
    host["model_catalog"] = [
        {"id": "weak-model", "provider": "test", "family": "fictional", "supported_efforts": ["low"]},
        {"id": "test-model", "provider": "test", "family": "fictional", "supported_efforts": ["low", "high"]},
    ]
    host["role_overrides"] = {"swarm-workers": {"models": ["test-model"], "effort": "high"}}
    plan = plan_role(policy, PACKAGE, host="codex", role="swarm-workers",
                     explicit="weak-model", capabilities=capability_bindings())
    assert plan.status == "BLOCKED"
    assert "unsupported on model" in plan.reasons[0]


def test_package_roles_have_exactly_one_local_agent_definition() -> None:
    role_ids = {role["id"] for role in PACKAGE["roles"]}
    agent_paths = list((ROOT / "agents").glob("*.md"))
    files = {p.stem for p in agent_paths}
    assert len(role_ids) == len(PACKAGE["roles"]), "duplicate role IDs"
    assert len(files) == len(agent_paths), "duplicate agent filenames"
    assert files == role_ids, f"role-agent drift: missing={role_ids - files}; extra={files - role_ids}"


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

    diverse = plan_role(policy, PACKAGE, host="codex", role="interrogate-reviewers",
                         explicit=["model-a", "model-b"], capabilities=capability_bindings())
    assert diverse.status == "PLANNED"
    assert diverse.reasons == ()

    same_family = plan_role(policy, PACKAGE, host="codex", role="interrogate-reviewers",
                            explicit=["model-a", "model-c"], capabilities=capability_bindings())
    assert same_family.status == "BLOCKED"
    assert same_family.reasons == ("required model-family diversity missing",)
    assert same_family.seats == ()

    single_seat = plan_role(policy, PACKAGE, host="codex", role="interrogate-reviewers",
                             explicit=["model-a"], capabilities=capability_bindings())
    assert single_seat.status == "BLOCKED"
    assert single_seat.reasons == ("required model-family diversity missing",)
    assert single_seat.seats == ()

    inherited = plan_role(policy, PACKAGE, host="codex", role="interrogate-reviewers",
                           explicit=["inherit-parent"], capabilities=capability_bindings())
    assert inherited.status == "BLOCKED"
    assert inherited.reasons == ("required model-family diversity missing",)
    assert inherited.seats == ()


def test_cross_judge_family_diversity_degraded_and_blocked_negatives() -> None:
    policy = catalog_plan_policy()

    unproven_parent = plan_role(policy, PACKAGE, host="codex", role="arena-cross-judge-pool",
                                 explicit=["model-a", "model-b"], parent_family=None,
                                 capabilities=capability_bindings())
    assert unproven_parent.status == "DEGRADED"
    assert "cross-judge family diversity unproven" in unproven_parent.reasons[0]

    policy_strict = copy.deepcopy(policy)
    policy_strict["role_constraints"]["arena-cross-judge-pool"]["require_distinct_model_families"] = True
    blocked_parent = plan_role(policy_strict, PACKAGE, host="codex", role="arena-cross-judge-pool",
                                explicit=["model-a", "model-b"], parent_family=None,
                                capabilities=capability_bindings())
    assert blocked_parent.status == "BLOCKED"
    assert "cross-judge model family independence is unproven" in blocked_parent.reasons[0]

    inherited = plan_role(policy, PACKAGE, host="codex", role="arena-cross-judge-pool",
                           explicit=["inherit-parent"], parent_family="alpha",
                           capabilities=capability_bindings())
    assert inherited.status == "DEGRADED"
    assert "cross-judge family diversity unproven" in inherited.reasons[0]

    inherited_blocked = plan_role(policy_strict, PACKAGE, host="codex", role="arena-cross-judge-pool",
                                   explicit=["inherit-parent"], parent_family="alpha",
                                   capabilities=capability_bindings())
    assert inherited_blocked.status == "BLOCKED"
    assert "cross-judge model family independence is unproven" in inherited_blocked.reasons[0]


def test_unavailable_model_in_panel_or_cross_judge_blocks_closed() -> None:
    policy = catalog_plan_policy()

    panel_plan = plan_role(policy, PACKAGE, host="codex", role="interrogate-reviewers",
                            explicit=["model-a", "ghost-model"], capabilities=capability_bindings())
    assert panel_plan.status == "BLOCKED"
    assert panel_plan.seats == ()
    assert any("model 'ghost-model' absent from codex catalog; no silent substitution" in r for r in panel_plan.reasons)

    judge_plan = plan_role(policy, PACKAGE, host="codex", role="arena-cross-judge-pool",
                            explicit=["ghost-model"], parent_family="alpha",
                            capabilities=capability_bindings())
    assert judge_plan.status == "BLOCKED"
    assert judge_plan.seats == ()
    assert any("model 'ghost-model' absent from codex catalog; no silent substitution" in r for r in judge_plan.reasons)

    runner_plan = plan_role(policy, PACKAGE, host="codex", role="arena-runners",
                             explicit=["model-a", "ghost-model"], capabilities=capability_bindings())
    assert runner_plan.status == "BLOCKED"
    assert runner_plan.seats == ()
    assert any("model 'ghost-model' absent from codex catalog; no silent substitution" in r for r in runner_plan.reasons)
