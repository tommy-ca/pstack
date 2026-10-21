"""Shared fixtures, schemas, and helper functions for model role policy test suites."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jsonschema import Draft202012Validator
from scripts.model_role_policy import check_model_role_policy

SCHEMA = json.loads((ROOT / "schemas/portability/model-role-policy.schema.json").read_text(encoding="utf-8"))
EXAMPLE = json.loads((ROOT / "examples/portability/model-role-policy.example.json").read_text(encoding="utf-8"))
PACKAGE = json.loads((ROOT / "pstack.package.json").read_text(encoding="utf-8"))
VALIDATOR = Draft202012Validator(SCHEMA)


def validate(policy: dict, descriptor: dict = PACKAGE) -> None:
    VALIDATOR.validate(policy)
    check_model_role_policy(policy, descriptor)


def live_policy() -> dict:
    policy = copy.deepcopy(EXAMPLE)
    config = policy["hosts"]["codex"]
    config["discovery"] = "live"
    config["verification_status"] = "verified"
    config["catalog_observation"] = {
        "host_version": "test-fixture-only",
        "observed_at": "2026-10-15T00:00:00Z",
        "receipt": ".audit/test-fixture-no-runtime-claim.json",
        "implementation_revision": "0" * 40,
    }
    config["model_catalog"] = [
        {
            "id": "test-model",
            "provider": "test",
            "family": "fictional",
            "supported_efforts": ["low", "high"],
        },
    ]
    config["tier_defaults"]["fast-verifier"] = ["test-model"]
    config["role_overrides"] = {
        "swarm-workers": {"models": ["test-model"], "effort": "high"}
    }
    return policy


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
    return {
        name: {
            "implementation_status": "native",
            "enforcement": "advisory" if advisory_readonly and name == "workspace.readonly" else "hard",
        }
        for name in ["agent.spawn", "agent.join", "workspace.isolated", "workspace.readonly"]
    }


def unproven_catalog_policy(status: str) -> dict:
    """Same complete fixture as catalog_plan_policy, one verification claim flipped."""
    policy = catalog_plan_policy()
    policy["hosts"]["codex"]["verification_status"] = status
    return policy
