"""Static policy schema + semantic parity checks; no live model availability implied."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError as JsonSchemaError

from scripts.model_role_policy import check_model_role_policy
from scripts.portability_schema import ValidationError

ROOT = Path(__file__).resolve().parents[1]
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
    (lambda p: p["role_constraints"]["swarm-workers"].update({"minimum_independent_workers": 2}), "single model"),
    (lambda p: p["role_constraints"]["swarm-workers"].update({"required_capabilities": ["provider.call"]}), "unknown capability"),
    (lambda p: p["hosts"]["codex"]["tier_defaults"].update({"unlisted-tier": ["inherit-parent"]}), "unknown tier"),
    (lambda p: p["hosts"]["codex"]["tier_defaults"].update({"panel": ["gpt-not-observed"]}), "absent from host catalog"),
    (lambda p: p["hosts"]["codex"].update({"model_catalog": [{"id": "gpt-not-observed","provider": "x","family": "x"}]}), "unverified catalog"),
    (lambda p: p["hosts"]["codex"].update({"verification_status": "verified"}), "live verified claims"),
    (lambda p: p["canonical_source"].update({"pin": "0" * 40}), "canonical pin differs"),
    (lambda p: p["hosts"].update({"copilot": p["hosts"].pop("codex")}), "not declared"),
    (lambda p: p["constraints"].update({"allow_unverified_models": True}), "opt into unverified"),
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
