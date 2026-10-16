"""Static, host-neutral role policy contract; no runtime model dispatch.

The pstack package descriptor owns role IDs and tier names. This module checks
cross-document invariants that JSON Schema cannot express. A static PASS is
never a claim that a provider/model can execute on the current host.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from functools import lru_cache
from pathlib import Path
from typing import Any

from scripts.portability_schema import VERIFICATION_STATUSES, PORTABLE_CAPABILITY_UNIVERSE, ValidationError

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "examples/portability/model-role-policy.example.json"
SCHEMA = ROOT / "schemas/portability/model-role-policy.schema.json"


@lru_cache(maxsize=1)
def _schema() -> dict[str, Any]:
    """Normative schema, read from disk once per process; no per-call I/O."""
    return json.loads(SCHEMA.read_text(encoding="utf-8"))


INHERIT = frozenset(_schema()["$defs"]["inheritTokens"]["enum"])
VALID_SELECTIONS = frozenset({"single", "panel", "cross-judge"})
VALID_DISCOVERY = frozenset({"unverified", "catalog", "live"})
VALID_VERIFICATION = frozenset(VERIFICATION_STATUSES)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


@lru_cache(maxsize=1)
def _validator() -> Any:
    """Compiled Draft 2020-12 validator; built once, reused by every policy check."""
    from jsonschema import Draft202012Validator

    return Draft202012Validator(_schema())


def _validate_against_schema(policy: dict[str, Any]) -> None:
    """Schema is normative per spec; the checker enforces it plus cross-document parity."""
    try:
        _validator().validate(policy)
    except Exception as exc:
        raise ValidationError(f"model-role policy violates its schema: {exc}") from exc


def check_choice_list(label: str, choices: Any) -> list[str]:
    """The single home of the model-choice-list rule: nonempty, unique slugs.

    Accepts one alias or any sequence of aliases and returns a list. Both the
    policy checker and the planner route caller-supplied (explicit/project/user)
    and policy-supplied (tier_defaults/overrides) lists through here, so a
    duplicate list can never be planned as independent seats.
    """
    if isinstance(choices, str):
        values: list[Any] = [choices]
    elif isinstance(choices, Sequence) and not isinstance(choices, (bytes, bytearray)):
        values = list(choices)
    else:
        raise ValidationError(f"{label}: choices must be a str or a sequence of model aliases")
    require(bool(values) and all(isinstance(value, str) and bool(value) for value in values),
            f"{label}: choices must be nonempty model aliases or slugs")
    require(len(values) == len(set(values)), f"{label}: choices must be unique nonempty list")
    return values  # every element is a nonempty str, proven by the require above


def check_model_role_policy(policy: dict[str, Any], descriptor: dict[str, Any]) -> None:
    """Validate all policy facts without host invocation; the schema is read once."""
    _validate_against_schema(policy)
    require(isinstance(policy, dict) and isinstance(descriptor, dict), "policy/descriptor must be objects")
    require(type(policy.get("version")) is int and policy["version"] == 1, "unsupported policy version")
    require(policy.get("role_source") == "pstack.package.json#/roles", "role_source must point to package roles")

    roles = descriptor.get("roles", [])
    require(isinstance(roles, list) and roles, "package roles must be a nonempty list")
    ids: list[str] = []
    tiers: set[str] = set()
    for role in roles:
        require(isinstance(role, dict), "package role must be an object")
        rid = role.get("id")
        tier = role.get("default_model_role")
        require(isinstance(rid, str) and bool(rid), "package role lacks ID")
        require(isinstance(tier, str) and bool(tier), f"package role {rid} lacks tier")
        ids.append(rid)
        tiers.add(tier)
    require(len(ids) == len(set(ids)), "package contains duplicate role IDs")
    role_ids = set(ids)

    source = policy.get("canonical_source")
    if source is not None:
        require(isinstance(source, dict) and source.get("repository") == "cursor/plugins",
                "canonical source must be cursor/plugins")
        require(source.get("pin") == descriptor.get("upstream_pin"), "canonical pin differs from descriptor")

    constraints = policy.get("role_constraints", {})
    require(isinstance(constraints, dict), "role_constraints must be an object")
    for rid, contract in constraints.items():
        require(rid in role_ids, f"unknown canonical role constraint: {rid}")
        require(isinstance(contract, dict), f"role constraint {rid} must be an object")
        selection = contract.get("selection", "single")
        require(selection in VALID_SELECTIONS, f"{rid}: unsupported selection mode")
        count = contract.get("minimum_independent_workers", 1)
        require(type(count) is int and 1 <= count <= 16, f"{rid}: invalid minimum_independent_workers")
        require(selection == "panel" or count == 1,
                f"{rid}: non-panel role cannot require >1 workers")
        capabilities = contract.get("required_capabilities", [])
        require(isinstance(capabilities, list), f"{rid}: required_capabilities must be a list")
        for capability in capabilities:
            require(capability in PORTABLE_CAPABILITY_UNIVERSE, f"{rid}: unknown capability {capability}")
        if selection in ("panel", "cross-judge"):
            require("agent.spawn" in capabilities and "agent.join" in capabilities,
                    f"{rid}: panel requires agent.spawn and agent.join")
        if contract.get("require_distinct_model_families", False):
            require(selection != "single", f"{rid}: family diversity requires a panel/cross-judge")

    host_targets = set(descriptor.get("host_targets", []))
    hosts = policy.get("hosts")
    require(isinstance(hosts, dict) and hosts, "hosts must be a nonempty object")
    for host, config in hosts.items():
        require(host in host_targets, f"host {host} is not declared by pstack.package.json")
        require(isinstance(config, dict), f"host {host} policy must be an object")
        discovery = config.get("discovery")
        verification = config.get("verification_status", "unverified")
        require(discovery in VALID_DISCOVERY, f"{host}: unknown discovery level")
        require(verification in VALID_VERIFICATION, f"{host}: unknown verification level")
        require("model_catalog" in config, f"{host}: model_catalog must be an explicit list")
        require(config.get("fallback") in ("inherit-parent", "fail-closed"),
                f"{host}: fallback must be inherit-parent or fail-closed")
        catalog = config.get("model_catalog", [])
        require(isinstance(catalog, list), f"{host}: model_catalog must be a list")
        models: dict[str, dict[str, Any]] = {}
        for model in catalog:
            require(isinstance(model, dict), f"{host}: model entry must be an object")
            slug = model.get("id")
            require(isinstance(slug, str) and slug not in INHERIT and bool(slug),
                    f"{host}: invalid model slug {slug!r}")
            require(slug not in models, f"{host}: duplicate model slug {slug}")
            require(bool(model.get("provider")) and bool(model.get("family")),
                    f"{host}: model {slug} missing provider/family")
            efforts = model.get("supported_efforts", [])
            require(isinstance(efforts, list) and all(isinstance(e, str) for e in efforts) and
                    len(efforts) == len(set(efforts)),
                    f"{host}: model {slug} has duplicate/invalid efforts")
            models[slug] = model

        observation = config.get("catalog_observation")
        if discovery == "live" or verification == "verified":
            require(discovery == "live" and bool(models) and isinstance(observation, dict),
                    f"{host}: live verified claims need observed catalog and models")
            require(all(bool(observation.get(k)) for k in ("host_version", "observed_at", "receipt")),
                    f"{host}: missing catalog observation evidence")
        if discovery == "unverified":
            require(not models, f"{host}: unverified catalog cannot claim observed model IDs")
        require(verification != "verified" or discovery == "live",
                f"{host}: verified catalog must be live-observed")

        overrides = config.get("role_overrides", {})
        require(isinstance(overrides, dict), f"{host}: role_overrides must be a mapping")
        for rid in overrides:
            require(rid in role_ids, f"{host}: unknown override role {rid}")

        def check_choices(label: str, choices: Any, effort: str | None = None) -> None:
            for slug in check_choice_list(f"{host}/{label}", choices):
                if slug not in INHERIT:
                    require(slug in models, f"{host}/{label}: model {slug} absent from host catalog")
                    if effort is not None:
                        require(effort in models[slug].get("supported_efforts", []),
                                f"{host}/{label}: unsupported effort {effort} on {slug}")
            if effort is not None:
                require(discovery == "live", f"{host}/{label}: effort needs live host proof")

        defaults = config.get("tier_defaults")
        require(isinstance(defaults, dict), f"{host}: tier_defaults must be an object")
        for tier, choices in defaults.items():
            require(tier in tiers, f"{host}: unknown tier {tier} (derive from package roles)")
            check_choices(f"tier={tier}", choices)
        for rid, override in overrides.items():
            require(isinstance(override, dict), f"{host}: override {rid} must be an object")
            seats = override.get("seats", 1)
            require(type(seats) is int and 1 <= seats <= 16, f"{host}/{rid}: invalid panel seats")
            role_selection = constraints.get(rid, {}).get("selection", "single")
            require(role_selection == "panel" or seats == 1,
                    f"{host}/{rid}: non-panel role cannot request multiple seats")
            effort = override.get("effort")
            check_choices(f"role={rid}", override.get("models"), effort)

    policy_constraints = policy.get("constraints", {})
    require(isinstance(policy_constraints, dict), "policy constraints must be an object")
    require(policy_constraints.get("allow_unverified_models") is not True,
            "model-policy cannot opt into unverified model dispatch")


def validate_checked_in_example(root: Path = ROOT) -> None:
    """Static repository preflight; add a separate runtime harness proof gate."""
    policy = json.loads((root / POLICY.relative_to(ROOT)).read_text(encoding="utf-8"))
    descriptor = json.loads((root / "pstack.package.json").read_text(encoding="utf-8"))
    check_model_role_policy(policy, descriptor)


if __name__ == "__main__":
    validate_checked_in_example()
    print("STATIC CONTRACT PASS: model-role policy matches package role IDs and tiers")
