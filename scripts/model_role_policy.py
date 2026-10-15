"""Static, host-neutral role policy contract; no runtime model dispatch.

The pstack package descriptor owns role IDs and tier names. This module checks
cross-document invariants that JSON Schema cannot express. A static PASS is
never a claim that a provider/model can execute on the current host.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scripts.portability_schema import PORTABLE_CAPABILITY_UNIVERSE, ValidationError

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "examples/portability/model-role-policy.example.json"
DESCRIPTOR = ROOT / "pstack.package.json"
INHERIT = frozenset({"inherit-parent", "auto"})
VALID_SELECTIONS = frozenset({"single", "panel", "cross-judge"})
VALID_DISCOVERY = frozenset({"unverified", "catalog", "live"})
VALID_VERIFICATION = frozenset({"unverified", "static-only", "verified", "stale"})


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def check_model_role_policy(policy: dict[str, Any], descriptor: dict[str, Any]) -> None:
    """Validate all policy facts without I/O or any host invocation."""
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
        require(type(count) is int and count >= 1, f"{rid}: invalid minimum_independent_workers")
        require(selection != "single" or count == 1, f"{rid}: single model cannot require >1 workers")
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
            require(isinstance(choices, list) and bool(choices) and
                    all(isinstance(c, str) for c in choices) and
                    len(choices) == len(set(choices)), f"{host}/{label}: choices must be unique nonempty list")
            for slug in choices:
                require(isinstance(slug, str) and bool(slug), f"{host}/{label}: invalid choice")
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
